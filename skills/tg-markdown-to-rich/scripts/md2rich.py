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
import re
import argparse
import os
from urllib import request as urllib_request
from urllib.parse import urlencode
from urllib.error import URLError

# ── Limits (Telegram Bot API 10.1) ────────────────────────────────────────────
MAX_CHARS = 32_768
MAX_BLOCKS = 500
MAX_NESTING = 16
MAX_MEDIA = 50
MAX_TABLE_COLS = 20


# ── Validation helpers ────────────────────────────────────────────────────────

def count_chars(text: str) -> int:
    return len(text.encode("utf-8").decode("utf-8"))


class LimitError(Exception):
    pass


def validate_limits(md: str) -> None:
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
        if re.match(r'^!\[.*?\]\(https?://', stripped):
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
        if not url.startswith(("http://", "https://")):
            sys.stderr.write(
                f"Warning: block-level media URL is not http/https and may be ignored by Telegram: {url!r}\n"
            )

    return result


# ── Build InputRichMessage ────────────────────────────────────────────────────

def build_input_rich_message(md: str) -> dict:
    """Return a dict representing InputRichMessage with field `markdown`."""
    return {"markdown": md}


# ── Send via Telegram Bot API ─────────────────────────────────────────────────

def send_rich_message(chat_id: str, rich_message: dict) -> dict:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise EnvironmentError("TELEGRAM_BOT_TOKEN environment variable is not set.")

    url = f"https://api.telegram.org/bot{token}/sendRichMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "rich_message": rich_message,
    }).encode("utf-8")

    req = urllib_request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib_request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except URLError as exc:
        raise RuntimeError(f"HTTP request failed: {exc}") from exc


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
    args = parser.parse_args()

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

    # Validate limits.
    try:
        validate_limits(md)
    except LimitError as exc:
        sys.stderr.write(f"Limit exceeded: {exc}\n")
        sys.exit(1)

    # Build InputRichMessage.
    msg = build_input_rich_message(md)
    if args.skip_entity_detection:
        msg["skip_entity_detection"] = True
    if args.rtl:
        msg["is_rtl"] = True

    # Output.
    output = json.dumps(msg, ensure_ascii=False, indent=2)

    if args.send:
        try:
            response = send_rich_message(args.chat_id, msg)
            sys.stdout.write(json.dumps(response, ensure_ascii=False, indent=2) + "\n")
        except (EnvironmentError, RuntimeError) as exc:
            sys.stderr.write(f"Send failed: {exc}\n")
            sys.exit(1)
    else:
        sys.stdout.write(output + "\n")


if __name__ == "__main__":
    main()
