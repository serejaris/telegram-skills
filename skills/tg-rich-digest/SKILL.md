---
name: tg-rich-digest
description: >
  Use when sending daily or weekly digests, community summaries, status reports, or newsletters
  through a Telegram bot as one structured rich message — instead of a wall of plain text.
  Triggers: "send weekly digest", "post summary to channel", "newsletter via bot",
  "community report", "daily status update", "format report as rich message".
---

# tg-rich-digest

Send a digest or report as a single structured Telegram Rich Message (Bot API 10.1) — section headings, topic lists, collapsible long-tail, photo collage, map embed, and a footer — all in one document-grade message.

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
[footer]       — date, source, issue number
```

### Heading block

```json
{ "type": "heading", "text": "Weekly Digest · Jun 9–15", "size": 2 }
```

`size` 1–6 (1 = largest). Use `size: 2` for digest title, `size: 3` for topic sections.

### Lead paragraph

```json
{ "type": "paragraph", "text": "This week the community hit 1,200 members. Three tools shipped, one hot thread ran 80+ replies." }
```

### Topic section

```json
{ "type": "heading", "text": "Top Discussions", "size": 3 },
{
  "type": "list",
  "items": [
    {
      "label": "•",
      "blocks": [{ "type": "paragraph", "text": { "type": "url", "text": "LLM context limits — practical patterns", "url": "https://example.com/thread/42" } }]
    },
    {
      "label": "•",
      "blocks": [{ "type": "paragraph", "text": "Prompt caching hit 80% savings for one member's pipeline" }]
    }
  ]
}
```

`label` is a plain string — the bullet character. For ordered lists set `value` (integer) and optionally `type` (`"1"`, `"a"`, `"A"`, `"i"`, `"I"`).

### Details block — long-tail

Use `details` for content that most readers skip: full link lists, raw stats, appendices.

```json
{
  "type": "details",
  "summary": "All links this week (12)",
  "is_open": false,
  "blocks": [
    {
      "type": "list",
      "items": [
        { "label": "1", "blocks": [{ "type": "paragraph", "text": { "type": "url", "text": "Article title", "url": "https://example.com/1" } }] },
        { "label": "2", "blocks": [{ "type": "paragraph", "text": { "type": "url", "text": "Tool release", "url": "https://example.com/2" } }] }
      ]
    }
  ]
}
```

Omit `is_open` or set `false` — block collapses by default. Set `true` only for critical content.

### Divider

```json
{ "type": "divider" }
```

### Footer

```json
{ "type": "footer", "text": "AI Builders Community · Issue #24 · 2026-06-15" }
```

---

## Media Patterns

### Photo collage

Group multiple photos (and optionally videos) into a single tile layout. `caption` is optional; add `credit` for attribution.

```json
{
  "type": "collage",
  "blocks": [
    { "type": "photo", "photo": [{ "file_id": "PHOTO_FILE_ID_1", "file_unique_id": "…", "width": 1280, "height": 960, "file_size": 204800 }] },
    { "type": "photo", "photo": [{ "file_id": "PHOTO_FILE_ID_2", "file_unique_id": "…", "width": 1280, "height": 960, "file_size": 198400 }] },
    { "type": "video", "video": { "file_id": "VIDEO_FILE_ID_1", "file_unique_id": "…", "width": 1280, "height": 720, "duration": 15, "file_size": 2097152 } }
  ],
  "caption": {
    "text": "Photos from the June meetup",
    "credit": "Photo: @photographer_handle"
  }
}
```

Mix `photo` and `video` blocks freely inside `collage.blocks`.

### Slideshow — sequential media

Use `slideshow` when order matters (tutorial steps, before/after, event sequence):

```json
{
  "type": "slideshow",
  "blocks": [
    { "type": "photo", "photo": [{ "file_id": "SLIDE_1", "file_unique_id": "…", "width": 1920, "height": 1080, "file_size": 307200 }] },
    { "type": "photo", "photo": [{ "file_id": "SLIDE_2", "file_unique_id": "…", "width": 1920, "height": 1080, "file_size": 298000 }] }
  ],
  "caption": { "text": "Step-by-step setup guide" }
}
```

### Collage inside details — expand to see photos

Wrap a collage in `details` when photos are supplemental and should not dominate the digest on first glance:

```json
{
  "type": "details",
  "summary": "Expand to see photo report (6 photos)",
  "is_open": false,
  "blocks": [
    {
      "type": "collage",
      "blocks": [
        { "type": "photo", "photo": [{ "file_id": "P1", "file_unique_id": "…", "width": 1280, "height": 960, "file_size": 204800 }] },
        { "type": "photo", "photo": [{ "file_id": "P2", "file_unique_id": "…", "width": 1280, "height": 960, "file_size": 196600 }] }
      ],
      "caption": { "text": "Community meetup · Berlin · 2026-06-10" }
    }
  ]
}
```

### Map embed — event location

One static location tile, no interactive markers. `zoom` must be 13–20. Provide `width` and `height` as display hints.

```json
{
  "type": "map",
  "location": { "latitude": 52.5200, "longitude": 13.4050 },
  "zoom": 15,
  "width": 600,
  "height": 300,
  "caption": { "text": "Meetup venue — Berlin Mitte" }
}
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

Use `sendRichMessage`. Supply content as `html` or `markdown` inside `InputRichMessage` — pick one, not both.

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
- [`../../reference/rich-messages-spec.md`](../../reference/rich-messages-spec.md) — canonical API spec (Bot API 10.1)
