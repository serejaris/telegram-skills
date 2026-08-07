#!/usr/bin/env python3
"""md2rich — Convert Markdown to Telegram Rich Message (InputRichMessage).

Produces a JSON object with field `markdown` (Rich Markdown string) suitable
for use as the `rich_message` parameter in sendRichMessage / sendRichMessageDraft.

Usage:
    python3 md2rich.py input.md
    cat input.md | python3 md2rich.py
    python3 md2rich.py input.md --send --chat-id 123456789
"""

import sys
import json
import mimetypes
import re
import argparse
import os
import secrets
from pathlib import Path
from urllib import request as urllib_request
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError

# ── Limits (Telegram Bot API 10.2) ────────────────────────────────────────────
MAX_CHARS = 32_768
MAX_BLOCKS = 500
MAX_NESTING = 16
MAX_MEDIA = 50
MAX_TABLE_COLS = 20
MEDIA_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
MEDIA_REF_RE = re.compile(r"tg://(photo|video|audio)\?id=([A-Za-z0-9_-]+)")
MEDIA_REF_CANDIDATE_RE = re.compile(
    r"""tg://(photo|video|audio)\?id=([^\s)"']+)"""
)
MEDIA_TYPES = {"animation", "audio", "photo", "video", "voice_note"}
REFERENCE_MEDIA_TYPES = {
    "photo": {"photo"},
    "video": {"video", "animation"},
    "audio": {"audio", "voice_note"},
}


# ── Validation helpers ────────────────────────────────────────────────────────

def count_chars(text: str) -> int:
    # spec wording is "32768 UTF-8 characters" — counted as Unicode code points here;
    # byte-length interpretation unverified.
    return len(text)


class LimitError(Exception):
    pass


def validate_limits(md: str, media: list[dict] | None = None) -> None:
    char_count = count_chars(md)
    if char_count > MAX_CHARS:
        raise LimitError(
            f"Text too long: {char_count} chars, limit is {MAX_CHARS}."
        )

    # Estimate block count: count block-level constructs heuristically.
    block_count = _estimate_block_count(md)
    if block_count > MAX_BLOCKS:
        raise LimitError(
            f"Too many blocks: ~{block_count} estimated, limit is {MAX_BLOCKS}."
        )

    # Check nesting depth (indented lists / nested blockquotes).
    max_depth = _estimate_max_nesting(md)
    if max_depth > MAX_NESTING:
        raise LimitError(
            f"Nesting too deep: {max_depth} levels, limit is {MAX_NESTING}."
        )

    # Count media blocks: standalone images (block-level, not inline).
    media_count = _count_media_blocks(md)
    if media_count > MAX_MEDIA:
        raise LimitError(
            f"Too many media blocks: {media_count}, limit is {MAX_MEDIA}."
        )

    # Check table columns.
    _check_table_cols(md)
    validate_media_bindings(md, media or [])


def validate_media_item(item: dict) -> str:
    """Validate one InputRichMessageMedia entry; return its id."""
    if not isinstance(item, dict):
        raise LimitError("Each media binding must be an object.")
    media_id = item.get("id")
    media_object = item.get("media")
    if not isinstance(media_id, str) or not MEDIA_ID_RE.fullmatch(media_id):
        raise LimitError(
            "Media id must be 1-64 characters using only A-Z, a-z, 0-9, _ and -."
        )
    if not isinstance(media_object, dict):
        raise LimitError(f"Media {media_id!r} must contain an InputMedia object.")
    media_type = media_object.get("type")
    source = media_object.get("media")
    if media_type not in MEDIA_TYPES:
        raise LimitError(
            f"Media {media_id!r} has unsupported type {media_type!r}; "
            f"choose one of {', '.join(sorted(MEDIA_TYPES))}."
        )
    if not isinstance(source, str) or not source:
        raise LimitError(f"Media {media_id!r} requires a non-empty media source.")
    return media_id


def validate_media_bindings(md: str, media: list[dict]) -> None:
    """Validate Bot API 10.2 tg:// references and InputRichMessageMedia entries.

    The check runs both ways. A reference without a binding never renders; a binding
    without a reference is an editing slip (renamed id, deleted paragraph) that Telegram
    does not report.
    """
    if len(media) > MAX_MEDIA:
        raise LimitError(
            f"Too many media bindings: {len(media)}, limit is {MAX_MEDIA}."
        )
    for _, media_id in MEDIA_REF_CANDIDATE_RE.findall(md):
        if not MEDIA_ID_RE.fullmatch(media_id):
            raise LimitError(
                f"Invalid tg:// media id {media_id!r}; use 1-64 characters from "
                "A-Z, a-z, 0-9, _ and -."
            )
    refs = MEDIA_REF_RE.findall(md)
    by_id: dict[str, dict] = {}

    for item in media:
        media_id = validate_media_item(item)
        if media_id in by_id:
            raise LimitError(f"Duplicate media id: {media_id!r}.")
        by_id[media_id] = item["media"]

    for ref_type, media_id in refs:
        if media_id not in by_id:
            raise LimitError(
                f"Media reference tg://{ref_type}?id={media_id} has no --media binding."
            )
        media_type = by_id[media_id]["type"]
        if media_type not in REFERENCE_MEDIA_TYPES[ref_type]:
            raise LimitError(
                f"Media reference tg://{ref_type}?id={media_id} is incompatible with "
                f"InputMedia type {media_type!r}."
            )

    unused = sorted(by_id.keys() - {media_id for _, media_id in refs})
    if unused:
        raise LimitError(
            "Media binding(s) never referenced by the markup: "
            + ", ".join(unused)
            + ". Remove them or add a tg:// reference."
        )


def _estimate_block_count(md: str) -> int:
    """Count paragraphs, headings, code blocks, dividers, list items, table rows,
    blockquote lines, and media blocks."""
    count = 0
    in_fence = False
    lines = md.splitlines()

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            if in_fence:
                count += 1  # opening fence = one pre block
            continue
        if in_fence:
            continue

        if re.match(r"^#{1,6}\s", stripped):
            count += 1  # heading
        elif stripped == "---" or stripped == "***" or stripped == "___":
            count += 1  # divider
        elif re.match(r"^\s*[-*+]\s", line) or re.match(r"^\s*\d+\.\s", line):
            count += 1  # list item
        elif stripped.startswith(">"):
            count += 1  # blockquote line (approximation)
        elif re.match(r"^\|", stripped):
            count += 1  # table row
        elif stripped.startswith("!["):
            count += 1  # potential media block
        elif stripped and not stripped.startswith("|"):
            count += 1  # paragraph text

    return count


def _estimate_max_nesting(md: str) -> int:
    """Detect max indentation depth from list indentation and nested blockquotes."""
    max_depth = 1
    for line in md.splitlines():
        # Each 2 or 4 spaces of indent = one nesting level.
        m = re.match(r"^( +)([-*+]|\d+\.)", line)
        if m:
            depth = len(m.group(1)) // 2 + 1
            max_depth = max(max_depth, depth)
        # Nested blockquotes: count leading `>`.
        m2 = re.match(r"^(>+)", line.strip())
        if m2:
            depth = len(m2.group(1))
            max_depth = max(max_depth, depth)
    return max_depth


def _count_media_blocks(md: str) -> int:
    """Count standalone image lines (block-level media: photos, video, audio, gif)."""
    count = 0
    for line in md.splitlines():
        stripped = line.strip()
        if re.match(r'^!\[.*?\]\((?:https?://|tg://(?:photo|video|audio)\?id=)', stripped):
            count += 1
    return count


def _check_table_cols(md: str) -> None:
    """Detect tables and enforce MAX_TABLE_COLS."""
    for line in md.splitlines():
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            cols = [c for c in stripped.split("|") if c.strip() not in ("", "---", ":---", "---:", ":---:")]
            if len(cols) > MAX_TABLE_COLS:
                raise LimitError(
                    f"Table has {len(cols)} columns, limit is {MAX_TABLE_COLS}."
                )


# ── Normalization ─────────────────────────────────────────────────────────────

def normalize_markdown(md: str) -> str:
    """
    Light normalization to align input Markdown with Rich Markdown style:
    - Ensure dividers are `---` (convert `***` / `___`).
    - Strip trailing whitespace.
    - Normalize Windows line endings.
    - Validate that block-level media uses HTTP/HTTPS (not data: URIs).
    """
    md = md.replace("\r\n", "\n").replace("\r", "\n")

    lines = md.splitlines()
    out = []
    for line in lines:
        stripped = line.strip()
        # Normalize dividers.
        if stripped in ("***", "___"):
            out.append("---")
        else:
            out.append(line.rstrip())

    # Check that block-level media only uses http/https URLs.
    result = "\n".join(out)
    for m in re.finditer(r'^!\[.*?\]\(([^)]+)\)', result, re.MULTILINE):
        url = m.group(1).strip()
        # Strip optional title: "url" or 'url' after space.
        url = re.split(r'\s+["\']', url)[0]
        if not url.startswith(("http://", "https://", "tg://photo?id=", "tg://video?id=", "tg://audio?id=")):
            sys.stderr.write(
                f"Warning: block-level media URL is not http/https and may be ignored by Telegram: {url!r}\n"
            )

    return result


# ── Build InputRichMessage ────────────────────────────────────────────────────

def build_input_rich_message(md: str, media: list[dict] | None = None) -> dict:
    """Return a dict representing InputRichMessage with field `markdown`."""
    result = {"markdown": md}
    if media:
        result["media"] = media
    return result


def parse_media_binding(value: str) -> dict:
    """Parse ID=TYPE=SOURCE into an InputRichMessageMedia object."""
    try:
        media_id, media_type, source = value.split("=", 2)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "media must use ID=TYPE=SOURCE"
        ) from exc
    item = {
        "id": media_id,
        "media": {"type": media_type, "media": source},
    }
    try:
        validate_media_item(item)
    except LimitError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    return item


def load_media_json(path: str) -> list[dict]:
    """Load a JSON array of InputRichMessageMedia objects.

    Use this instead of --media when bindings carry player metadata (duration,
    performer, title, has_spoiler) that ID=TYPE=SOURCE cannot express.
    """
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError) as exc:
        raise argparse.ArgumentTypeError(f"cannot read media JSON: {exc}") from exc
    if not isinstance(data, list):
        raise argparse.ArgumentTypeError("media JSON must be an array of bindings")
    for item in data:
        try:
            validate_media_item(item)
        except LimitError as exc:
            raise argparse.ArgumentTypeError(str(exc)) from exc
    return data


def parse_attachment(value: str) -> tuple[str, Path]:
    """Parse NAME=PATH into a multipart file part."""
    name, sep, raw_path = value.partition("=")
    if not sep or not name or not raw_path:
        raise argparse.ArgumentTypeError("attachment must use NAME=PATH")
    path = Path(raw_path)
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"attachment file not found: {raw_path}")
    return name, path


def resolve_attachments(
    media: list[dict],
    attachments: list[tuple[str, Path]],
) -> dict[str, Path]:
    """Match every attach://name in the bindings to a provided file part."""
    required = {
        item["media"]["media"].removeprefix("attach://")
        for item in media
        if str(item["media"]["media"]).startswith("attach://")
    }
    provided: dict[str, Path] = {}
    for name, path in attachments:
        if name in provided:
            raise LimitError(f"Duplicate attachment name: {name!r}.")
        provided[name] = path
    missing = sorted(required - provided.keys())
    if missing:
        raise LimitError(
            "attach:// media without a file part: "
            + ", ".join(missing)
            + ". Pass --attach NAME=PATH for each."
        )
    unused = sorted(provided.keys() - required)
    if unused:
        raise LimitError(
            "File part(s) not referenced by any binding: " + ", ".join(unused) + "."
        )
    return provided


# ── Send via Telegram Bot API ─────────────────────────────────────────────────

class UncertainDelivery(RuntimeError):
    """The request failed with an unknown send outcome.

    Telegram may already have posted the message. Retrying duplicates it, so the caller
    must resolve the state before sending anything again.
    """


def encode_multipart(
    fields: dict[str, str],
    files: dict[str, Path],
) -> tuple[bytes, str]:
    """Build a multipart/form-data body. Non-file fields are plain strings."""
    boundary = "----md2rich" + secrets.token_hex(16)
    parts: list[bytes] = []
    for name, value in fields.items():
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n'
            f"{value}\r\n".encode("utf-8")
        )
    for name, path in files.items():
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        parts.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{name}"; filename="{path.name}"\r\n'
            f"Content-Type: {mime}\r\n\r\n".encode("utf-8")
        )
        parts.append(path.read_bytes())
        parts.append(b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def send_rich_message(
    chat_id: str,
    rich_message: dict,
    files: dict[str, Path] | None = None,
) -> dict:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise EnvironmentError("TELEGRAM_BOT_TOKEN environment variable is not set.")

    url = f"https://api.telegram.org/bot{token}/sendRichMessage"

    if files:
        body, content_type = encode_multipart(
            {
                "chat_id": chat_id,
                "rich_message": json.dumps(rich_message, ensure_ascii=False),
            },
            files,
        )
    else:
        body = json.dumps(
            {"chat_id": chat_id, "rich_message": rich_message}
        ).encode("utf-8")
        content_type = "application/json"

    req = urllib_request.Request(
        url,
        data=body,
        headers={"Content-Type": content_type},
        method="POST",
    )
    try:
        with urllib_request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:500]
        if exc.code == 429 or exc.code >= 500:
            raise UncertainDelivery(
                f"HTTP {exc.code} — delivery outcome unknown, do not retry blindly: {detail}"
            ) from exc
        raise RuntimeError(f"HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise UncertainDelivery(
            f"transport failure — delivery outcome unknown, do not retry blindly: {exc}"
        ) from exc


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert Markdown to Telegram InputRichMessage JSON.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Markdown file to convert. Reads from stdin if omitted.",
    )
    parser.add_argument(
        "--send",
        action="store_true",
        help="Send the result via Telegram Bot API (requires TELEGRAM_BOT_TOKEN env var).",
    )
    parser.add_argument(
        "--chat-id",
        metavar="CHAT_ID",
        help="Target chat ID for --send.",
    )
    parser.add_argument(
        "--skip-entity-detection",
        action="store_true",
        help="Add skip_entity_detection:true to the output.",
    )
    parser.add_argument(
        "--rtl",
        action="store_true",
        help="Add is_rtl:true to the output.",
    )
    parser.add_argument(
        "--media",
        action="append",
        default=[],
        type=parse_media_binding,
        metavar="ID=TYPE=SOURCE",
        help=(
            "Bind tg:// media. TYPE: photo, video, animation, audio, voice_note. "
            "SOURCE: Telegram file_id, URL, or attach://name. Repeat as needed."
        ),
    )
    parser.add_argument(
        "--media-json",
        metavar="FILE",
        type=load_media_json,
        help=(
            "JSON array of full InputRichMessageMedia bindings. Use instead of --media "
            "when bindings carry metadata (duration, performer, title, has_spoiler)."
        ),
    )
    parser.add_argument(
        "--attach",
        action="append",
        default=[],
        type=parse_attachment,
        metavar="NAME=PATH",
        help=(
            "Upload a local file as the multipart part NAME, matching an "
            "attach://NAME binding. Repeat as needed."
        ),
    )
    args = parser.parse_args()

    media = list(args.media) + list(args.media_json or [])

    if args.send and not args.chat_id:
        sys.stderr.write("Error: --chat-id is required when using --send.\n")
        sys.exit(1)

    # Read input.
    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                raw = f.read()
        except OSError as exc:
            sys.stderr.write(f"Error reading file: {exc}\n")
            sys.exit(1)
    else:
        raw = sys.stdin.read()

    # Normalize.
    md = normalize_markdown(raw)

    # Validate limits and media bindings.
    try:
        validate_limits(md, media)
        attachments = resolve_attachments(media, args.attach)
    except LimitError as exc:
        sys.stderr.write(f"Limit exceeded: {exc}\n")
        sys.exit(1)

    # Build InputRichMessage.
    msg = build_input_rich_message(md, media)
    if args.skip_entity_detection:
        msg["skip_entity_detection"] = True
    if args.rtl:
        msg["is_rtl"] = True

    # Output.
    output = json.dumps(msg, ensure_ascii=False, indent=2)

    if args.send:
        try:
            response = send_rich_message(args.chat_id, msg, attachments)
            sys.stdout.write(json.dumps(response, ensure_ascii=False, indent=2) + "\n")
        except UncertainDelivery as exc:
            # Exit code 2 marks "unknown outcome" so a caller can tell it apart from a
            # definite failure and avoid resending into a duplicate.
            sys.stderr.write(f"Send outcome unknown: {exc}\n")
            sys.exit(2)
        except (EnvironmentError, RuntimeError) as exc:
            sys.stderr.write(f"Send failed: {exc}\n")
            sys.exit(1)
    else:
        sys.stdout.write(output + "\n")


if __name__ == "__main__":
    main()
