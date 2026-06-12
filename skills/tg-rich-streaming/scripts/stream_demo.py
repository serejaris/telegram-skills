#!/usr/bin/env python3
"""
tg-rich-streaming demo — simulates LLM token streaming with sendRichMessageDraft.

Usage:
    TELEGRAM_BOT_TOKEN=<token> python3 stream_demo.py --chat-id <integer>

Requires Python 3.8+. No third-party dependencies.
"""

import argparse
import json
import os
import random
import time
import urllib.error
import urllib.request


# ---------------------------------------------------------------------------
# Simulated LLM output — replace with real SSE/iterator in production
# ---------------------------------------------------------------------------

DEMO_CHUNKS = [
    "Here is a quick summary of the **Rich Message streaming** pattern:\n\n",
    "## How it works\n\n",
    "1. The bot sends a `sendRichMessageDraft` immediately — this opens an ",
    "animated preview visible only to the user.\n",
    "2. As the model generates text, the draft is updated with the same ",
    "`draft_id`. The client animates each update.\n",
    "3. When generation is complete, `sendRichMessage` is called with the ",
    "full text — this creates the **permanent** message in the chat.\n\n",
    "## Key constraints\n\n",
    "- Drafts are ephemeral (~30 s window).\n",
    "- `sendRichMessageDraft` works **only in private chats**.\n",
    "- `RichBlockThinking` is valid only inside a draft — never in the ",
    "final message.\n\n",
    "---\n\n",
    "That's the complete streaming loop. Swap `DEMO_CHUNKS` for a real LLM ",
    "iterator and you're done.",
]


def fake_stream(chunks: list[str], delay: float = 0.4):
    """Yield text chunks with a simulated delay."""
    for chunk in chunks:
        time.sleep(delay + random.uniform(0.0, 0.15))
        yield chunk


# ---------------------------------------------------------------------------
# Bot API helpers
# ---------------------------------------------------------------------------

def bot_request(token: str, method: str, payload: dict) -> dict:
    url = f"https://api.telegram.org/bot{token}/{method}"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {method}: {body}") from exc


def send_draft(token: str, chat_id: int, draft_id: int, markdown: str) -> None:
    bot_request(token, "sendRichMessageDraft", {
        "chat_id": chat_id,
        "draft_id": draft_id,
        "rich_message": {"markdown": markdown},
    })


def send_final(token: str, chat_id: int, markdown: str) -> int:
    result = bot_request(token, "sendRichMessage", {
        "chat_id": chat_id,
        "rich_message": {"markdown": markdown},
    })
    return result["result"]["message_id"]


# ---------------------------------------------------------------------------
# Streaming loop
# ---------------------------------------------------------------------------

THROTTLE_SECONDS = 1.5   # minimum gap between draft updates
THINKING_MARKDOWN = "<tg-thinking>Thinking…</tg-thinking>"


def run_stream(token: str, chat_id: int) -> None:
    draft_id = random.randint(1, 2**31 - 1)   # non-zero, per spec
    accumulated = ""
    last_sent_at = 0.0

    print(f"[stream] draft_id={draft_id}  chat_id={chat_id}")

    # Step 1: open draft with Thinking block
    print("[stream] opening draft with Thinking block…")
    send_draft(token, chat_id, draft_id, THINKING_MARKDOWN)
    last_sent_at = time.monotonic()

    # Step 2: update draft as "tokens" arrive
    for chunk in fake_stream(DEMO_CHUNKS):
        accumulated += chunk
        print(f"[stream] +{len(chunk)} chars  total={len(accumulated)}", end="\r")

        now = time.monotonic()
        if now - last_sent_at >= THROTTLE_SECONDS:
            send_draft(token, chat_id, draft_id, accumulated)
            last_sent_at = now

    print()  # newline after the \r progress line

    # Step 3: mandatory finalization — draft is ephemeral, this creates
    # the permanent message; omitting this step causes the draft to vanish
    print("[stream] finalizing with sendRichMessage…")
    message_id = send_final(token, chat_id, accumulated)
    print(f"[stream] done — permanent message_id={message_id}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Demo: stream simulated LLM output via sendRichMessageDraft",
    )
    parser.add_argument(
        "--chat-id",
        type=int,
        required=True,
        help="Integer ID of a private chat (not @username — drafts are private-only)",
    )
    args = parser.parse_args()

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        parser.error("Set TELEGRAM_BOT_TOKEN environment variable before running.")

    run_stream(token, args.chat_id)


if __name__ == "__main__":
    main()
