---
name: tg-markdown-to-rich
description: "Use when converting Markdown documents, reports, or any text content into a Telegram Rich Message for delivery via a bot. Triggers: \"send markdown to Telegram\", \"convert doc to rich message\", \"publish report to bot\", \"format markdown for sendRichMessage\", \"telegram rich message from file\". Produces an InputRichMessage JSON object ready for Telegram Bot API 10.2 sendRichMessage, including explicit file_id or URL media bindings."
license: MIT
---

# tg-markdown-to-rich

The converter uses Python 3 standard library only. Direct sending requires network access to
`api.telegram.org` and `TELEGRAM_BOT_TOKEN`.

Converts a Markdown file (or stdin) into a Telegram `InputRichMessage` JSON
object. The output uses the `markdown` field of `InputRichMessage` and is ready
to pass directly to [`sendRichMessage`](../../reference/rich-messages-spec.md).

See also: [`../tg-rich-messages/SKILL.md`](../tg-rich-messages/SKILL.md) for
composing rich messages programmatically.

---

## Usage

```bash
# File input → stdout JSON
python3 scripts/md2rich.py document.md

# Pipe stdin
cat report.md | python3 scripts/md2rich.py

# Additional flags
python3 scripts/md2rich.py document.md --rtl
python3 scripts/md2rich.py document.md --skip-entity-detection
python3 scripts/md2rich.py document.md \
  --media cover=photo=AgAC...file_id \
  --media voice=voice_note=https://cdn.example.com/briefing.ogg

# Send directly via Telegram Bot API
TELEGRAM_BOT_TOKEN=<token> python3 scripts/md2rich.py document.md \
  --send --chat-id <chat_id>
```

Output is a JSON object:

```json
{
  "markdown": "# Title\n\n![](tg://photo?id=cover)",
  "media": [
    {"id": "cover", "media": {"type": "photo", "media": "AgAC...file_id"}}
  ]
}
```

Pass this as the `rich_message` parameter to `sendRichMessage`.

---

## Markdown → Rich block mapping

| Markdown syntax | Rich block / inline |
|---|---|
| `# H1` … `###### H6` | `heading` block (size 1–6) |
| Paragraph text | `paragraph` block |
| `**bold**` / `__bold__` | `bold` inline |
| `*italic*` / `_italic_` | `italic` inline |
| `` `code` `` | `code` inline |
| `~~strikethrough~~` | `strikethrough` inline |
| `==marked==` | `marked` inline |
| `\|\|spoiler\|\|` | `spoiler` inline |
| `` ```lang … ``` `` | `pre` block (with language) |
| `[text](url)` | `url` inline |
| `[text](mailto:…)` | `email_address` inline |
| `[text](tel:…)` | `phone_number` inline |
| `[text](tg://user?id=…)` | `text_mention` inline |
| `$LaTeX$` | `mathematical_expression` inline |
| `$$LaTeX$$` / ` ```math` | `mathematical_expression` block |
| `---` | `divider` block |
| `> text` | `blockquote` block |
| `- item` / `* item` | `list` block (unordered) |
| `1. item` | `list` block (ordered) |
| `- [ ] task` / `- [x] task` | `list` block with checkbox |
| GFM table `\| … \|` | `table` block |
| `![alt](https://…)` (block-level) | `photo` block (with optional caption from title) |
| `[^id]: …` footnote | `reference` inline + `reference_link` |
| `<u>` / `<ins>` | `underline` inline (HTML pass-through) |
| `<sub>` / `<sup>` | `subscript` / `superscript` inline |
| `<aside>…<cite>…</cite></aside>` | `pullquote` block |
| `<details [open]><summary>…</summary>…</details>` | `details` block |
| `<tg-collage>…</tg-collage>` | `collage` block |
| `<tg-slideshow>…</tg-slideshow>` | `slideshow` block |

---

## Limits enforced (exit 1 on violation)

| Limit | Value |
|---|---|
| Max characters (UTF-8) | 32 768 |
| Max blocks (incl. nested) | 500 |
| Max nesting depth | 16 |
| Max media blocks | 50 |
| Max table columns | 20 |

---

## Unsupported inputs and fallback behavior

| Input | Behavior |
|---|---|
| `tg://photo`, `tg://video`, `tg://audio` | Validated against repeatable `--media ID=TYPE=SOURCE` bindings |
| `file_id` or HTTP/HTTPS source | Sent in JSON through `InputRichMessage.media` |
| `attach://name` source | Generated successfully; `--send` rejects it because upload requires a multipart file part |
| Nested blocks inside table cells | GFM spec disallows this; content treated as inline text (Telegram cells accept only inline formatting) |
| Other non-HTTP media URI | Warning to stderr; passed through for Telegram validation |
| `<tg-map>` HTML tag | Passed through unchanged; not generatable from plain Markdown |
| `RichBlockThinking` | Not producible from Markdown (only valid in `sendRichMessageDraft`) |
| HTML tags not in Rich HTML spec | Passed through; Telegram will ignore unknown tags |

---

## References

- Canonical spec: [`../../reference/rich-messages-spec.md`](../../reference/rich-messages-spec.md)
- Related skill: [`../tg-rich-messages/SKILL.md`](../tg-rich-messages/SKILL.md)
