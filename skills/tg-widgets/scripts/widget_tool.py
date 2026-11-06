#!/usr/bin/env python3
"""Measure a Telegram widget like the server does, and send it once.

check: no network. send: one POST to the beta Bot API path, never retried, because
a timeout does not prove the message was not delivered.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
import zlib

MAX_HTML = 32768
MAX_ZLIB = 4096
TARGET_ZLIB = 3800
API = "https://api.telegram.org/beta/bot{token}/sendWidget"


def measure(data: bytes) -> dict:
    packed = len(zlib.compress(data, 9))
    if len(data) > MAX_HTML or packed > MAX_ZLIB:
        verdict = "too_large"
    elif packed > TARGET_ZLIB:
        verdict = "near_limit"
    else:
        verdict = "ok"
    return {"html_bytes": len(data), "zlib_bytes": packed, "verdict": verdict}


def send(token: str, html: str, chat: str, caption: str | None) -> dict:
    payload = {"chat_id": chat, "html": html}
    if caption:
        payload["caption"] = caption
    request = urllib.request.Request(
        API.format(token=token),
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        return json.load(error)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check")
    check.add_argument("file")
    push = sub.add_parser("send")
    push.add_argument("file")
    push.add_argument("--chat", required=True)
    push.add_argument("--caption")
    args = parser.parse_args()

    with open(args.file, "rb") as handle:
        data = handle.read()
    result = measure(data)
    print(json.dumps(result))
    if result["verdict"] == "too_large":
        return 1
    if args.command == "check":
        return 0

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("TELEGRAM_BOT_TOKEN is not set", file=sys.stderr)
        return 2
    answer = send(token, data.decode(), args.chat, args.caption)
    if not answer.get("ok"):
        print(answer.get("description"), file=sys.stderr)
        return 1
    print(json.dumps({"message_id": answer["result"]["message_id"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
