---
name: tg-widgets
description: "Use when building or sending a Telegram message widget (HTML bubble, HTMLBubbles, `sendWidget`, `messageMediaWidget`, Bot API 10.4): an interactive HTML, CSS and JS program inside a chat bubble, such as a game, poll, calculator or live ticker. Covers where widgets can be delivered, size and runtime limits, what the sandbox removes, and how to fit 3D and games into 4 KB. Not for Mini Apps or Rich Messages."
license: MIT
---

# tg-widgets

A widget is one self-contained HTML document that a bot sends as a message. It runs in the chat bubble with no window, no server and no network.

Status on 2026-11-06. Telegram has not announced widgets and the public Bot API docs stop at 10.3. The contract comes from Telegram's own repository [`TelegramMessenger/widget-sandbox`](https://github.com/TelegramMessenger/widget-sandbox) (v0.6.0): `docs/tgw-format.md`, `docs/widget-runtime-profile.md`, `docs/sdk-v1.md`. Method names may change until 10.4 ships. Recheck before relying on this.

Each fact below is marked **live** (a real request on 2026-11-06, one production bot) or **docs** (the repository only).

## Delivery

| Target | Result | Source |
|---|---|---|
| `https://api.telegram.org/bot<token>/sendWidget` | 404, the method does not exist on the public path | live |
| `https://api.telegram.org/beta/bot<token>/sendWidget` | works with a normal production token | live |
| Private chat with the bot | works, confirmed rendering on an iOS phone | live |
| Supergroup with the bot as admin, also a channel's discussion group | `INPUT_MEDIA_WIDGET_NOT_ALLOWED` | live, 2026-11-06; docs say allowed |
| Channel, direct | `INPUT_MEDIA_WIDGET_NOT_ALLOWED` | live |
| `forwardMessage` to anywhere, also with `is_shared` | `the message can't be forwarded`; the sent message has `has_protected_content: true` even with `protect_content: false` | live, contradicts docs |
| `copyMessage` | refused | live, matches docs |
| Inline mode, `InputWidgetMessageContent` or `InputSharedWidgetMessageContent` | `answerInlineQuery` fails with `INPUT_MEDIA_WIDGET_NOT_ALLOWED` in a channel; the widget content also failed for the query from the private chat with the bot | live, 2026-11-06; docs say allowed |
| User account (MTProto) | `INPUT_MEDIA_WIDGET_NOT_ALLOWED`, only bots may send | docs |

A successful `sendWidget` proves the server accepted it. It does not prove anyone saw it: each client decides whether to render, and clients below layer 233 show an unsupported-media stub with the caption. So always write a caption that makes sense alone, and confirm on a real device.

## Send

```bash
python3 scripts/widget_tool.py check widget.html
TELEGRAM_BOT_TOKEN=... python3 scripts/widget_tool.py send widget.html --chat CHAT_ID --caption "Tap the water to feed"
```

The tool sends once and never retries: after a timeout the message may already be delivered.

| Method | Purpose |
|---|---|
| `sendWidget` | `chat_id`, `html`, `width`, `height` (0 = auto), `chat_data`, `public_data`, `caption`, `allow_queries`, `is_shared`, `reply_markup` |
| `sendSharedWidget` | post an existing shared widget again by `widget_id` |
| `editMessageWidgetData` | change `chat_data` or `public_data` of one message silently; live: works, and an unchanged value returns `message is not modified`, which counts as done |
| `editSharedWidgetData` | change the state of a shared widget everywhere, with `cache_time` 5–3600 s |
| `answerWidgetQuery` | answer the `widget_query` or `shared_widget_query` update, up to 1024 bytes, always answer or the widget gets `TIMEOUT` |

The HTML never changes after sending. Only the bot changes the state, up to 1024 bytes of text in each field. A request from the widget carries up to 64 bytes and the bot always learns who tapped.

## Limits

| Limit | Value |
|---|---|
| HTML | 32768 bytes |
| **After zlib level 9** | **4096 bytes, the limit you actually hit** (live: `INPUT_MEDIA_WIDGET_TOO_LARGE`) |
| Bubble | 200–600 px wide, phones about 320–430; up to 600 px tall, the rest is clipped, nothing scrolls |
| CPU | 300 ms per second, one task up to 500 ms |
| Memory, nodes | 8 MB, 2000 nodes |
| Canvas | 4000 commands per canvas per task, 2048×2048 pixels in total |
| Paint | 16 elements with blur, filter or opacity below 1; past it the widget stops |
| `localStorage` | 4 KB, per message, per device |

Press articles that quote only "32 KB" or "64 MB memory" are out of date or incomplete.

## Not in the sandbox

No network (`fetch` throws `NetworkDisabledError`, live), WebGL, three.js or any library, video, audio, form controls, keyboard, `vh`, inner scrolling, `text-shadow`, 3D CSS transforms, `shadowBlur`, `globalCompositeOperation`, `getImageData`, `alert`. A removed feature is silent: the rest of the widget keeps running.

Input: taps and pointer events only. **Vertical drags always scroll the chat**, so no joysticks or vertical sliders. Claim horizontal drags with `touch-action: pan-y` and holds with `touch-action: none`. Calls that need a real tap (`openLink`, `copyText`, `request`) go in a `click` handler.

Use `--tg-theme-*` CSS variables or paint the whole bubble yourself. `window.TelegramWidget` is undefined outside Telegram, so guard it.

## Writing to fit

- Measure as the server does after every change: `widget_tool.py check`. Target 3800, ship at most 4096.
- Non-ASCII text compresses badly. Cutting Russian strings saved more than renaming identifiers (renaming saved about 40 bytes of 4300).
- Repeated code compresses well, unique data does not. Generate scenes procedurally.
- Run logic and drawing at about 30 fps and keep under 2000 canvas commands a frame. JS runs in an interpreter without JIT.

## Look and speed

What a real iPhone accepted on 2026-11-06, with desktop numbers measured at 4x CPU throttle:

| Approach | Result on the phone | Example |
|---|---|---|
| Low-resolution canvas (one pixel = 3 CSS px, `image-rendering: pixelated`), ordered dithering, palette ramps | smooth, liked | [`examples/aquarium-pixel.html`](examples/aquarium-pixel.html), [`examples/night-deploy-pixel.html`](examples/night-deploy-pixel.html) |
| Grid of glyphs on canvas, about 44 columns, runs of `fillRect` + `fillText` | works, liked | [`examples/textmode-panel.html`](examples/textmode-panel.html), [`examples/night-deploy-textmode.html`](examples/night-deploy-textmode.html) |
| Full-resolution vector canvas with gradients | laggy, disliked | none |
| ASCII in 7 stacked `<pre>` layers, 76 columns | laggy, layers went missing; cause unknown | none |

- A desktop throttle test does not predict the phone: the 7-layer `<pre>` version looked fine on desktop. Check on a phone.
- Size is `zlib.compress(html, 9)`. Use terser and nothing else: RegPack came out larger after zlib, and unpacking with Roadroller takes seconds.
- Draw text with a 5×5 bitmap font on a pixel canvas: a system font breaks the look. Keep only the glyphs you use.
- Draw Cyrillic one glyph per cell on a glyph grid: the fallback font may not be monospaced.
- Paint static backgrounds once on their own canvas and redraw only the moving layer.
- `drawImage` from a canvas outside the DOM works on iOS, so a sprite atlas costs one call per sprite.
- Generate instead of storing: a seed saved in `localStorage` gives each viewer a different scene from the same code.
- Use a 16:9 frame: height is `round(width * 9 / 16)`, set from JS.

## 3D without WebGL

Project triangles yourself and paint them back to front on a canvas. A low-poly aquarium fit in 4 KB at under 1800 canvas calls a frame.

- Rotate by camera yaw and tilt, divide by depth, sort by mean depth, fill flat-shaded triangles.
- Precompute static triangles and their shade; project them every frame.
- Force large base geometry (floor, stand) to draw first with a depth bias: sorting by mean depth fails on big triangles.
- Cache colour strings per shade level rather than building them for every triangle.
- Prefer one horizontal drag for the camera and a tap for the action, and tell them apart by distance moved.

## Games

Examples above are survivors-genre games under 4 KB. Horizontal drags need `touch-action: pan-y`, vertical drags belong to the chat, and `pointercancel` must stop the action. On a low frame rate, make projectiles slower with a larger hit radius.

## Getting a widget into a channel

Direct sending, forwarding, inline mode, a supergroup and the channel's discussion group all fail live (2026-11-06), so neither a channel post nor a group can carry a widget today. The working alternative is a post with a video and a `t.me/<bot>?start=...` link that sends the widget in the private chat.

Before announcing widgets as a feature of your channel, send one to your own phone and check it.
