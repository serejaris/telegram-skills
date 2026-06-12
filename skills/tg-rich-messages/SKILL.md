---
name: tg-rich-messages
description: "Use when sending structured or richly formatted messages from a Telegram bot — tables, section headings, collapsible blocks, photo galleries, maps, math formulas, audio, or streaming AI responses. Also use for understanding rich message types and limits when plain sendMessage with parse_mode HTML/Markdown is not sufficient."
license: MIT
compatibility: "Requires network access to api.telegram.org; sending requires TELEGRAM_BOT_TOKEN env var; scripts need Python 3 stdlib only."
---

# tg-rich-messages

## Overview

Bot API 10.1 (June 11, 2026) added **Rich Messages**: document-grade structured messages
delivered directly in chat. Think Instant View articles — headings, tables, collage,
slideshow, map, math, collapsible blocks — but sent by a bot via `sendRichMessage`.

**Use `sendRichMessage` instead of `sendMessage` when you need:**

| Need | Mechanism |
|---|---|
| Section headings (h1–h6) | `RichBlockSectionHeading` |
| Tables with header rows / spanning cells | `RichBlockTable` |
| Collapsible sections | `RichBlockDetails` |
| Photo grid or slide deck | `RichBlockCollage` / `RichBlockSlideshow` |
| Embedded map | `RichBlockMap` |
| LaTeX math (inline or block) | `RichTextMathematicalExpression` / `RichBlockMathematicalExpression` |
| Streaming AI reply with "Thinking…" block | `sendRichMessageDraft` + `RichBlockThinking` |
| Footnotes / anchor links | `RichTextReference` / `RichTextAnchorLink` |

Plain `sendMessage` with `parse_mode: HTML` still covers bold/italic/code/spoiler/links
for simple formatting. Move to `sendRichMessage` only when you need structural blocks.

---

## Sending: InputRichMessage

`sendRichMessage` takes an `InputRichMessage` object in its `rich_message` field.
`InputRichMessage` carries the **entire message as a markup string** — either HTML or
Markdown — in exactly one of its two fields:

| Field | When to use |
|---|---|
| `html` | Rich HTML with Telegram-specific tags |
| `markdown` | GitHub-Flavored Markdown + Telegram extensions |

Do not pass both. Do not pass a block-JSON structure — the API accepts markup strings only.

Optional fields on `InputRichMessage`:

| Field | Type | Purpose |
|---|---|---|
| `is_rtl` | Boolean | Render message right-to-left |
| `skip_entity_detection` | Boolean | Disable auto-detection of URLs, emails, mentions, etc. |

---

## Sending: HTTP calls

### curl (HTML mode)

```bash
curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendRichMessage" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": '"$CHAT_ID"',
    "rich_message": {
      "html": "<h2>Weekly Report</h2><p>Highlights from the past week.</p><table bordered><tr><th>Item</th><th>Value</th></tr><tr><td>Sales</td><td><b>142</b></td></tr></table>"
    }
  }'
```

### Python (stdlib, HTML mode)

```python
import json
import os
import urllib.request

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = int(os.environ["CHAT_ID"])

payload = {
    "chat_id": CHAT_ID,
    "rich_message": {
        "html": (
            "<h2>Weekly Report</h2>"
            "<p>Highlights from the past week.</p>"
            "<table bordered>"
            "<tr><th>Item</th><th>Value</th></tr>"
            "<tr><td>Sales</td><td><b>142</b></td></tr>"
            "</table>"
        )
    },
}

req = urllib.request.Request(
    f"https://api.telegram.org/bot{TOKEN}/sendRichMessage",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(req) as resp:
    result = json.load(resp)
```

### Python (stdlib, Markdown mode)

```python
payload = {
    "chat_id": CHAT_ID,
    "rich_message": {
        "markdown": (
            "## Weekly Report\n\n"
            "Highlights from the past week.\n\n"
            "| Item | Value |\n"
            "|------|-------|\n"
            "| Sales | **142** |\n"
        )
    },
}
```

See [`examples.md`](examples.md) for more complete examples including streaming drafts,
collages, and details blocks.

---

## Block types — quick reference

### Structural blocks

| Type string | HTML tag | Purpose | Key fields |
|---|---|---|---|
| `paragraph` | `<p>` | Text paragraph | `text: RichText` |
| `heading` | `<h1>`–`<h6>` | Section heading | `text`, `size: 1–6` (1 = largest) |
| `pre` | `<pre>` | Preformatted / code block | `text`, `language?: string` |
| `footer` | `<footer>` | Footer text | `text: RichText` |
| `divider` | `<hr/>` | Horizontal rule | _(no content fields)_ |
| `anchor` | `<a name="...">` | Named anchor point | `name: string` |
| `mathematical_expression` | `<tg-math-block>` | Block LaTeX formula | `expression: string` |
| `list` | `<ul>` / `<ol>` | Ordered or unordered list | `items: RichBlockListItem[]` |
| `blockquote` | `<blockquote>` | Block quotation | `blocks: RichBlock[]`, `credit?: RichText` |
| `pullquote` | `<aside>` | Centered pull quote | `text`, `credit?: RichText` |
| `details` | `<details>` | Collapsible section | `summary: RichText`, `blocks: RichBlock[]`, `is_open?: true` |
| `table` | `<table>` | Data table | `cells: RichBlockTableCell[][]`, `is_bordered?`, `is_striped?`, `caption?: RichText` |
| `map` | `<tg-map>` | Static embedded map | `location: Location`, `zoom: 13–20`, `width`, `height`, `caption?` |
| `collage` | `<tg-collage>` | Photo/video grid | `blocks: RichBlock[]`, `caption?: RichBlockCaption` |
| `slideshow` | `<tg-slideshow>` | Swipeable photo/video deck | `blocks: RichBlock[]`, `caption?: RichBlockCaption` |
| `photo` | `<img>` | Photo block | `photo: PhotoSize[]`, `has_spoiler?: true`, `caption?` |
| `video` | `<video>` | Video block | `video: Video`, `has_spoiler?: true`, `caption?` |
| `animation` | `<video>` (gif) | Animation / GIF block | `animation: Animation`, `has_spoiler?: true`, `caption?` |
| `audio` | `<audio>` (mp3) | Audio / music block | `audio: Audio`, `caption?` |
| `voice_note` | `<audio>` (ogg) | Voice message block | `voice_note: Voice`, `caption?` |
| `thinking` | `<tg-thinking>` | "Thinking…" placeholder **(draft only)** | `text: RichText` |

> **`thinking` is only valid in `sendRichMessageDraft`.** It cannot appear in `sendRichMessage` and is never stored in a Message.

### Inline text types (RichText)

| Type string | HTML tag | Purpose | Extra fields |
|---|---|---|---|
| `bold` | `<b>` | Bold | `text` |
| `italic` | `<i>` | Italic | `text` |
| `underline` | `<u>` | Underline | `text` |
| `strikethrough` | `<s>` | Strikethrough | `text` |
| `spoiler` | `<tg-spoiler>` | Hidden spoiler text | `text` |
| `marked` | `<mark>` | Highlight | `text` |
| `code` | `<code>` | Inline monospace | `text` |
| `subscript` | `<sub>` | Subscript | `text` |
| `superscript` | `<sup>` | Superscript | `text` |
| `custom_emoji` | `<tg-emoji>` | Custom emoji | `custom_emoji_id`, `alternative_text` |
| `mathematical_expression` | `<tg-math>` | Inline LaTeX | `expression: string` |
| `date_time` | `<tg-time>` | Formatted timestamp | `text`, `unix_time: int`, `date_time_format: string` |
| `text_mention` | `<a href="tg://user?id=...">` | User mention by ID | `text`, `user: User` |
| `mention` | auto-detected | Username mention | `text`, `username: string` |
| `url` | `<a href="https://...">` | URL link | `text`, `url: string` |
| `email_address` | `<a href="mailto:...">` | Email link | `text`, `email_address: string` |
| `phone_number` | `<a href="tel:...">` | Phone link | `text`, `phone_number: string` |
| `bank_card_number` | auto-detected | Bank card highlight | `text`, `bank_card_number: string` |
| `hashtag` | auto-detected | Hashtag | `text`, `hashtag: string` |
| `cashtag` | auto-detected | Cashtag | `text`, `cashtag: string` |
| `bot_command` | auto-detected | Bot command | `text`, `bot_command: string` |
| `anchor` | `<a name="...">` (inline) | Inline anchor point | `name: string` |
| `anchor_link` | `<a href="#...">` | Link to anchor | `text`, `anchor_name: string` (empty = top) |
| `reference` | `<tg-reference name="...">` | Footnote definition | `text`, `name: string` |
| `reference_link` | `<a href="#...">` (ref) | Link to footnote | `text`, `reference_name: string` |

---

## Markdown quick syntax

```
**bold**   *italic*   __bold__   _italic_
~~strikethrough~~   `code`   ==marked==   ||spoiler||

[Link text](https://example.com)
[Email](mailto:user@example.com)
[Phone](tel:+1234567890)
[Mention user](tg://user?id=123456789)
![custom emoji](tg://emoji?id=5368324170671202286)
![timestamp label](tg://time?unix=1647531900&format=wDT)
$inline LaTeX formula$
$$block LaTeX formula$$

# H1  ## H2  ...  ###### H6

```python
code block with language
```

---   (divider)

- unordered item        1. ordered item
- [ ] task              - [x] done task

> blockquote line

![](https://example.com/photo.jpg)           # photo block
![](https://example.com/photo.jpg "Caption") # with caption
![](https://example.com/video.mp4)           # video block
![](https://example.com/track.mp3)           # audio block
![](https://example.com/note.ogg)            # voice note
![](https://example.com/anim.gif)            # animation

| Col 1 | Col 2 |
|:------|------:|
| left  | right |

Text[^fn1].   [^fn1]: Footnote text.

<details open><summary>**Bold title**</summary>
Content here.
</details>

<tg-collage>
![](https://example.com/a.jpg)
![](https://example.com/b.jpg)
</tg-collage>

<tg-map lat="48.8566" long="2.3522" zoom="14"/>
```

---

## Limits & traps

| Limit | Value |
|---|---|
| Max UTF-8 characters (text, alt-text, formulas) | **32 768** |
| Max blocks (including nested: list items, table rows, blockquote/details blocks) | **500** |
| Max nesting levels | **16** |
| Max media attachments (photos, videos, audio) | **50** |
| Max table columns | **20** |
| Map zoom range | **13–20** |

### Critical constraints

**`InputRichMessage` is markup-only.** Pass the message as an HTML string (`html` field)
or a Markdown string (`markdown` field). Never pass a block-JSON tree directly to the API.
The structured `RichBlock` / `RichText` types exist only in received `Message.rich_message`
(type `RichMessage`).

**Media blocks: URL only, top-level only.**
- Media must be specified as separate blocks, not inline in text.
- Only HTTP/HTTPS URLs are accepted — file_id is not supported.
- Type is inferred from MIME type / URL extension.

**Table cells: inline formatting only.**
No blocks (`<p>`, `<ul>`, `<img>`, etc.) inside `<td>` / `<th>`. Only inline tags.

**`RichBlockThinking` is draft-only.**
Can only appear in `sendRichMessageDraft`. Never in `sendRichMessage`. Never stored in a
Message object.

**`sendRichMessageDraft` is private-chat only.**
`chat_id` must be an Integer. `@username` strings are not accepted.

**`editMessageText`: `text` and `rich_message` are mutually exclusive.**
Pass exactly one. Sending both (or neither) is an error.

**Map is static, no markers.**
`RichBlockMap` renders a static tile at the given location and zoom level. No pins,
no interactivity.

**Block count includes nesting.**
The 500-block limit counts every `RichBlockListItem`, every table row, every block inside
`blockquote` / `details`. Deep nesting exhausts the budget fast.

**Collage and slideshow accept both photos and videos.**
`blocks` can mix `photo` and `video` blocks. Both may also be placed inside a `details`
block as collapsible media.

---

## Common mistakes

| Mistake | Fix |
|---|---|
| Passing a JSON block array as `rich_message` | Pass the markup string in `rich_message.html` or `rich_message.markdown` |
| Using `file_id` for media | Use a public HTTP/HTTPS URL |
| Putting `<img>` or `<video>` inline in `<p>` | Move media to its own block, outside `<p>` |
| Adding block elements inside `<td>` | Only inline tags inside table cells |
| Using `RichBlockThinking` in `sendRichMessage` | `thinking` is valid only in `sendRichMessageDraft` |
| Calling `sendRichMessageDraft` with `@username` | Use numeric `chat_id` (Integer) |
| Sending `text` and `rich_message` together in `editMessageText` | Pass exactly one |
| Forgetting to call `sendRichMessage` after streaming | Draft expires after 30 s — always finalize with full message |
| Assuming zoom 1–20 for map | Valid range is **13–20** |
| Using `skip_entity_detection` for manual link formatting | Set it to `true` to prevent double-detection when you already mark up URLs manually |

---

## Full spec

All types, all fields, all format details: [`../../reference/rich-messages-spec.md`](../../reference/rich-messages-spec.md)
