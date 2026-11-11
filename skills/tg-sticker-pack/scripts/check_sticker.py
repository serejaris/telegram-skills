#!/usr/bin/env python3
import argparse
import json
import re
import struct
import sys
from pathlib import Path

SIDE = 512
MAX_BYTES = 512 * 1024
NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


def png_info(data):
    if len(data) < 33 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError("not a PNG")
    w, h = struct.unpack(">II", data[16:24])
    color = data[25]
    alpha = color in (4, 6) or b"tRNS" in data
    return w, h, alpha


def webp_info(data):
    if len(data) < 30 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        raise ValueError("not a WEBP")
    kind = data[12:16]
    if kind == b"VP8X":
        flags = data[20]
        w = 1 + int.from_bytes(data[24:27], "little")
        h = 1 + int.from_bytes(data[27:30], "little")
        return w, h, bool(flags & 0x10)
    if kind == b"VP8L":
        if data[20] != 0x2F:
            raise ValueError("bad VP8L signature")
        bits = int.from_bytes(data[21:25], "little")
        return 1 + (bits & 0x3FFF), 1 + ((bits >> 14) & 0x3FFF), bool((bits >> 28) & 1)
    if kind == b"VP8 ":
        if data[23:26] != b"\x9d\x01\x2a":
            raise ValueError("bad VP8 start code")
        w, h = struct.unpack("<HH", data[26:30])
        return w & 0x3FFF, h & 0x3FFF, False
    raise ValueError(f"unknown WEBP chunk {kind!r}")


def check_file(path):
    p = Path(path)
    res = {"file": str(p), "errors": [], "warnings": []}
    try:
        data = p.read_bytes()
    except OSError as e:
        res["errors"].append(f"unreadable: {e.strerror}")
        return res
    try:
        if data[:4] == b"RIFF":
            w, h, alpha = webp_info(data)
            res["format"] = "webp"
        else:
            w, h, alpha = png_info(data)
            res["format"] = "png"
    except (ValueError, struct.error) as e:
        res["errors"].append(f"PNG or WEBP expected: {e}")
        return res
    res.update(width=w, height=h, alpha=alpha, bytes=len(data))
    if max(w, h) != SIDE or min(w, h) < 1:
        res["errors"].append(f"one side must be exactly {SIDE}px, the other at most {SIDE}px; got {w}x{h}")
    if len(data) > MAX_BYTES:
        res["errors"].append(f"file is {len(data)} bytes; keep static stickers under {MAX_BYTES}")
    if not alpha:
        res["warnings"].append("no alpha channel: the sticker will show a solid background")
    return res


def check_name(name, bot=None):
    errors = []
    if not 1 <= len(name) <= 64:
        errors.append("short name must be 1-64 characters")
    if not NAME_RE.match(name):
        errors.append("short name: English letters, digits and underscores, starting with a letter")
    if "__" in name:
        errors.append("short name can't contain consecutive underscores")
    if bot is not None:
        suffix = "_by_" + bot.lstrip("@")
        if not name.lower().endswith(suffix.lower()):
            errors.append(f"a bot-created set name must end in {suffix}")
    return {"name": name, "errors": errors}


def main(argv=None):
    p = argparse.ArgumentParser(description="Offline checks for static Telegram stickers and set names")
    sub = p.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("files")
    f.add_argument("paths", nargs="+")
    n = sub.add_parser("name")
    n.add_argument("name")
    n.add_argument("--bot", help="bot username when the set is created via Bot API")
    a = p.parse_args(argv)
    results = [check_file(x) for x in a.paths] if a.cmd == "files" else [check_name(a.name, a.bot)]
    for r in results:
        print(json.dumps(r, ensure_ascii=False))
    return 1 if any(r["errors"] for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
