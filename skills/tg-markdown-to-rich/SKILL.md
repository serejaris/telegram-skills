---
name: tg-markdown-to-rich
description: >
  Use when converting Markdown documents, reports, or any text content into a
  Telegram Rich Message for delivery via a bot. Triggers on: "send markdown to
  Telegram", "convert doc to rich message", "publish report to bot", "format
  markdown for sendRichMessage", "telegram rich message from file". Produces a
  JSON object (InputRichMessage) ready for the Telegram Bot API 10.1
  sendRichMessage method.
---

# tg-markdown-to-rich

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

# Send directly via Telegram Bot API
TELEGRAM_BOT_TOKEN=<token> python3 scripts/md2rich.py document.md \
  --send --chat-id <chat_id>
```

Output is a JSON object:

```json
{
  "markdown": "# Title\n\nContent..."
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
| Block-level media with non-http/https URL | Warning to stderr; passed through as-is (Telegram will likely reject it) |
| Nested blocks inside table cells | GFM spec disallows this; content treated as inline text (Telegram cells accept only inline formatting) |
| `data:` image URIs | Passed through with a warning; Telegram only accepts http/https media URLs |
| `<tg-map>` HTML tag | Passed through unchanged; not generatable from plain Markdown |
| `RichBlockThinking` | Not producible from Markdown (only valid in `sendRichMessageDraft`) |
| HTML tags not in Rich HTML spec | Passed through; Telegram will ignore unknown tags |

---

## References

- Canonical spec: [`../../reference/rich-messages-spec.md`](../../reference/rich-messages-spec.md)
- Related skill: [`../tg-rich-messages/SKILL.md`](../tg-rich-messages/SKILL.md)
