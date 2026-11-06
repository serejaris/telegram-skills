---
name: tg-widgets
description: "Use when building or sending a Telegram message widget (HTML bubble, HTMLBubbles, `sendWidget`, `messageMediaWidget`, Bot API 10.4): an interactive HTML, CSS and JS program inside a chat bubble, such as a game, poll, calculator or live ticker. Follows Telegram's own widget-sandbox documentation and records where live delivery differs from it. Not for Mini Apps or Rich Messages."
license: MIT
---

# tg-widgets

A widget is one self-contained HTML document that a bot sends as a message. It runs in the chat bubble with no window, no server and no network.

Telegram's repository [`TelegramMessenger/widget-sandbox`](https://github.com/TelegramMessenger/widget-sandbox) is the source of truth. This skill points to it and adds only what a live check showed. Telegram has not announced widgets, the public Bot API docs stop at 10.3, and names may change until 10.4 ships. Checked against v0.6.0 on 2026-11-06.

## Read first

Read the current version before writing code. The repository has no license file, so this skill links to it and does not copy it.

| Need | File in `docs/` |
|---|---|
| Rules for writing a widget. The section "Agent block" stands alone: use it as your instructions | [`widget-runtime-profile.md`](https://raw.githubusercontent.com/TelegramMessenger/widget-sandbox/main/docs/widget-runtime-profile.md) |
| `TelegramWidget` API: state, requests, links, haptics, wallet | [`sdk-v1.md`](https://raw.githubusercontent.com/TelegramMessenger/widget-sandbox/main/docs/sdk-v1.md) |
| Sending, size limits, errors, Bot API names | [`tgw-format.md`](https://raw.githubusercontent.com/TelegramMessenger/widget-sandbox/main/docs/tgw-format.md) |
| Every CSS, HTML and JS feature, in or out | [`profile-v1.md`](https://raw.githubusercontent.com/TelegramMessenger/widget-sandbox/main/docs/profile-v1.md) |

Starting points from the same repository: `corpus/interactive` (poll, tic-tac-toe, live ticker, promo code) and `corpus/bot-demos` with its bot `scripts/bot-demos.ts`.

## Steps

1. Read the Agent block.
2. Write the widget. Anything outside the profile is removed silently while the rest keeps running, so check each feature you rely on.
3. Measure as the server does:

   ```bash
   python3 scripts/widget_tool.py check widget.html
   ```

4. Optional: run Telegram's harness from a clone of the repository. It prints what the profile removed and who gets each press. Review the code before running it. This skill has not run it.

   ```bash
   corepack pnpm tsx packages/core/scripts/sandbox-node.ts widget.html --width 360
   ```

5. Send to your private chat with the bot. The tool sends once and never retries: after a timeout the message may already be delivered.

   ```bash
   TELEGRAM_BOT_TOKEN=... python3 scripts/widget_tool.py send widget.html --chat CHAT_ID --caption "Tap the water to feed"
   ```

6. Open it on a phone. A successful `sendWidget` proves only that the server accepted it: clients below layer 233 show an unsupported-media stub with the caption, so write a caption that makes sense alone.

## Limits

From the documentation. The Agent block has the full list.

| Limit | Value |
|---|---|
| HTML | 32768 bytes |
| After zlib level 9 | 4096 bytes; aim for 3800 if you cannot measure |
| Bubble | 200–600 px wide, phones about 320–430; up to 600 px tall, the rest is clipped, nothing scrolls |
| CPU | 300 ms per second, one task up to 500 ms |
| Memory, nodes | 8 MB, 2000 nodes |
| Canvas | 4000 commands per canvas per task, 2048×2048 pixels in total |
| Paint | 16 elements with blur, filter or opacity below 1 |
| `localStorage` | 4 KB per message, per device |
| `chat_data`, `public_data` | 1024 bytes of text each |
| Request from the widget | 1–64 bytes, the answer up to 1024 bytes |

Not available: network, WebGL, libraries, video, audio, form controls, keyboard, `vh`, inner scrolling, `text-shadow`, 3D CSS transforms, `shadowBlur`, `globalCompositeOperation`, `getImageData`, `alert`. `window.TelegramWidget` is undefined outside Telegram, so guard it.

## Input

Vertical drags belong to the chat, whatever `touch-action` says. A canvas or game control takes `touch-action: none`, a horizontal slider takes `pan-y`, everything else stays `auto`. The first 10 px decide the whole press: a drag that starts sideways on a claimed element stays with the widget on both axes, and one that starts up or down goes to the chat. On `pointercancel`, undo what `pointerdown` started.

## Delivery: documentation and live check

The documentation allows more than the live API accepted. Live means real requests on 2026-11-06 with production bots. Recheck before you plan around it.

| Target | Documentation | Live |
|---|---|---|
| `api.telegram.org/bot<token>/sendWidget` | beta path only | 404 |
| `api.telegram.org/beta/bot<token>/sendWidget` | works | works with a normal token |
| Private chat with the bot | allowed | works, rendered on an iPhone |
| Group or supergroup with the bot | allowed | supergroup and a channel's discussion group refused: `INPUT_MEDIA_WIDGET_NOT_ALLOWED`. Basic group not checked |
| Channel, direct | not allowed yet | refused, same error |
| Inline mode | allowed | refused in a channel, and for a query from the private chat with the bot |
| `forwardMessage` | allowed to any chat | refused: `the message can't be forwarded` |
| `copyMessage` | refused | refused |

To put a widget in front of a channel audience today, publish a post with a video and a `t.me/<bot>?start=...` link, and let the bot send the widget in the private chat.

## Bot API

| Method | Purpose |
|---|---|
| `sendWidget` | `chat_id`, `html`, `width`, `height` (0 = auto), `chat_data`, `public_data`, `caption`, `allow_queries`, `is_shared`, `reply_markup` |
| `sendSharedWidget` | post an existing shared widget again by `widget_id` |
| `editMessageWidgetData` | change `chat_data` or `public_data` of one message silently; `message is not modified` counts as done |
| `editSharedWidgetData` | change the state of a shared widget everywhere, `cache_time` 5–3600 s |
| `answerWidgetQuery` | answer the `widget_query` or `shared_widget_query` update, always, or the widget gets `TIMEOUT` |

The HTML never changes after sending. Only the bot changes the state.

## Examples

`examples/` holds widgets built with this skill and opened on an iPhone. They are not official and show one author's look. Sizes after zlib level 9:

| File | Bytes |
|---|---|
| [`aquarium-pixel.html`](examples/aquarium-pixel.html) | 4080 |
| [`night-deploy-pixel.html`](examples/night-deploy-pixel.html) | 4086 |
| [`night-deploy-textmode.html`](examples/night-deploy-textmode.html) | 4071 |
| [`textmode-panel.html`](examples/textmode-panel.html) | 2134 |
