---
name: tg-rich-digest
description: "Use when sending daily or weekly digests, community summaries, status reports, or newsletters through a Telegram bot as one structured rich message instead of a wall of plain text. Triggers: \"send weekly digest\", \"post summary to channel\", \"newsletter via bot\", \"community report\", \"daily status update\", \"format report as rich message\"."
license: MIT
---

# tg-rich-digest

Send a digest or report as a single structured Telegram Rich Message (Bot API 10.2) — section headings, topic lists, collapsible long-tail, photo collage, map embed, and a footer — all in one document-grade message.

## Overview

A digest is a structured document, not a wall of text. Rich Messages let you organize it with real headings, lists, collapsible sections, and embedded media — readable on any screen, no HTML page required.

This skill covers the **digest/report pattern** specifically. For the complete block reference see [`../tg-rich-messages/SKILL.md`](../tg-rich-messages/SKILL.md). To convert an existing Markdown report see [`../tg-markdown-to-rich/SKILL.md`](../tg-markdown-to-rich/SKILL.md).

---

## Anatomy of a Digest

Recommended block sequence:

```
[heading h2]   — digest title + date range
[paragraph]    — 1–3 sentence lead: what happened, key number
[heading h3]   — topic 1
[list]         — 3–7 bullet items for topic 1
[heading h3]   — topic 2
[list]         — ...
[details]      — "All links / Full list" — long-tail, closed by default
[divider]      — visual separator before footer
[collage]      — photo report (optional)
[map]          — event location (optional)
[footer]       — date, source, issue number
```

Each element below is shown as **HTML markup**, the string placed inside
`InputRichMessage.html`. Bot API 10.2 also accepts `InputRichMessage.blocks` for code-built
documents.

> **Note:** When you receive the message back, `Message.rich_message` contains the parsed `RichBlock` JSON (e.g. `{"type": "heading", ...}`). That structure is receive-only — you cannot send it.

### Heading

```html
<h2>Weekly Digest &mdash; Jun 9&ndash;15</h2>
```

`<h1>`–`<h6>` map to heading sizes 1–6. Use `<h2>` for the digest title, `<h3>` for topic sections.

### Lead paragraph

```html
<p>This week the community hit <b>1,200 members</b>. Three tools shipped, one hot thread ran 80+ replies.</p>
```

### Topic section

```html
<h3>Top Discussions</h3>
<ul>
  <li><a href="https://example.com/thread/42">LLM context limits &mdash; practical patterns</a> &mdash; 81 replies</li>
  <li><a href="https://example.com/thread/55">Prompt caching deep dive</a> &mdash; 80% cost reduction reported</li>
</ul>
```

For ordered lists use `<ol>` with optional `start`, `type` (`"1"`, `"a"`, `"A"`, `"i"`, `"I"`), and `reversed` attributes on `<ol>`, or `value` on individual `<li>`.

### Details block — long-tail

Use `<details>` for content most readers skip: full link lists, raw stats, appendices. Omit `open` to collapse by default.

```html
<details><summary>All links this week (9)</summary>
<ol>
  <li><a href="https://example.com/thread/42">LLM context limits &mdash; practical patterns</a></li>
  <li><a href="https://example.com/thread/55">Prompt caching deep dive</a></li>
  <li><a href="https://github.com/example/promptkit">promptkit v0.4 release notes</a></li>
</ol>
</details>
```

Add `open` attribute (`<details open>`) only for critical content that should be visible by default.

### Divider

```html
<hr/>
```

### Photo collage

Public **HTTP or HTTPS URLs** can be used directly. For Telegram `file_id` values or uploads,
use `tg://photo?id=...`, `tg://video?id=...`, or `tg://audio?id=...` plus
`InputRichMessage.media`.

```html
<tg-collage>
  <figure><img src="https://example.com/photos/meetup-1.jpg"/><figcaption>Berlin meetup · June 10<cite>Photo: @photo_credit</cite></figcaption></figure>
  <img src="https://example.com/photos/meetup-2.jpg"/>
  <img src="https://example.com/photos/meetup-3.jpg"/>
</tg-collage>
```

Mix `<img>` and `<video src="https://...">` inside `<tg-collage>` freely. Wrap in `<details>` when photos are supplemental.

### Map embed

```html
<tg-map lat="52.5200" long="13.4050" zoom="15"/>
```

`zoom` must be 13–20.

### Footer

```html
<footer>AI Builders Community &mdash; Issue #24 &mdash; Week of June 9&ndash;15, 2026</footer>
```

---

## Media Patterns

Media can use public HTTP/HTTPS URLs directly. Existing Telegram `file_id` values and new
multipart uploads use explicit Bot API 10.2 media bindings:

```json
{
  "html": "<h2>Daily</h2><img src=\"tg://photo?id=cover\"/>",
  "media": [
    {"id": "cover", "media": {"type": "photo", "media": "AgAC...file_id"}}
  ]
}
```

For a new upload, set `media` to `attach://cover_file`, send multipart/form-data, and attach
the binary under the `cover_file` part name.

### Photo collage

Group multiple photos (and optionally videos) into a single tile layout. Use `<figure>` with `<figcaption>` and `<cite>` for attribution.

```html
<tg-collage>
  <figure>
    <img src="https://example.com/photos/meetup-1.jpg"/>
    <figcaption>Photos from the June meetup<cite>Photo: @photographer_handle</cite></figcaption>
  </figure>
  <img src="https://example.com/photos/meetup-2.jpg"/>
  <video src="https://example.com/videos/highlight.mp4"></video>
</tg-collage>
```

Mix `<img>` and `<video>` freely inside `<tg-collage>`.

### Slideshow — sequential media

Use `<tg-slideshow>` when order matters (tutorial steps, before/after, event sequence):

```html
<tg-slideshow>
  <figure><img src="https://example.com/slides/step-1.jpg"/><figcaption>Step 1: initial setup</figcaption></figure>
  <figure><img src="https://example.com/slides/step-2.jpg"/><figcaption>Step 2: configure</figcaption></figure>
</tg-slideshow>
```

### Collage inside details — expand to see photos

Wrap a collage in `<details>` when photos are supplemental and should not dominate the digest on first glance:

```html
<details><summary>Expand to see photo report (6 photos)</summary>
<tg-collage>
  <figure><img src="https://example.com/photos/meetup-berlin-1.jpg"/><figcaption>Community meetup &mdash; Berlin &mdash; 2026-06-10</figcaption></figure>
  <img src="https://example.com/photos/meetup-berlin-2.jpg"/>
  <img src="https://example.com/photos/meetup-berlin-3.jpg"/>
</tg-collage>
</details>
```

### Map embed — event location

One static location tile, no interactive markers. `zoom` must be 13–20.

```html
<tg-map lat="52.5200" long="13.4050" zoom="15"/>
```

---

## Length Budgeting

| Limit | Value |
|---|---|
| Max UTF-8 characters (incl. alt-text, formulas) | **32 768** |
| Max blocks (all nested: list items, table rows, details content, quotation blocks) | **500** |
| Max nesting levels | **16** |
| Max media attachments (photos + videos + audio) | **50** |
| Max table columns | **20** |

### Counting blocks

Every `items` entry in a list counts as one block. Every `blocks` entry inside `details` counts. Nested list items each count individually. A collage with 8 photos = 1 (`collage`) + 8 (`photo`) = 9 blocks.

### Overflow strategy

When a digest is near limits, cut in this order:

1. **Trim details content first.** Move excess links to a follow-up message or external page.
2. **Reduce list depth.** Flatten nested lists to a single level.
3. **Split into two messages.** End message 1 with a divider + `"Continued →"` footer; open message 2 with a heading `"(continued)"`.
4. **Drop media last.** Collage/slideshow consume both block budget and media budget — remove if text is the priority.

Pre-calculate block count before sending: count top-level blocks + sum of all nested arrays.

---

## Sending the Digest

Use `sendRichMessage`. Supply exactly one of `html`, `markdown`, or `blocks` inside
`InputRichMessage`.

Minimal call (raw HTTP):

```bash
curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendRichMessage" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": $CHAT_ID,
    "rich_message": {
      "markdown": "## Weekly Digest\n\nLead paragraph.\n\n### Top Topics\n\n- Item one\n- Item two\n\n---\n\n<footer>Issue #1 · 2026-06-15</footer>"
    }
  }'
```

For channels pass `chat_id` as `"@channelname"`. The bot must have permission to send the relevant media types if the digest includes photos or video.

---

## Compatibility Note

Rich Message rendering on older Telegram clients is **not documented by Telegram**. Before sending to your full audience:

1. Test with `sendRichMessage` to a single private chat or a staging channel.
2. Check visually in both mobile and desktop clients.
3. Use the official demo bot [@RichTextDemoBot](https://t.me/RichTextDemoBot) to preview rendering.

---

## Related Skills

- [`../tg-rich-messages/SKILL.md`](../tg-rich-messages/SKILL.md) — complete block and inline type reference
- [`../tg-markdown-to-rich/SKILL.md`](../tg-markdown-to-rich/SKILL.md) — convert existing Markdown into a rich message
- [`../../reference/rich-messages-spec.md`](../../reference/rich-messages-spec.md) — canonical API spec (Bot API 10.2)
