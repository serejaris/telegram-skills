# One post, two branches

The same channel post built as a classic message and as a rich message. Chat id and URLs are placeholders. Both payloads were checked for shape and limits against the docs on 2026-10-30; neither was sent to Telegram.

## Classic: `sendPhoto`

The photo carries the text in a caption, so the visible text must fit in 1024 characters.

```json
{
  "chat_id": "@your_channel",
  "photo": "https://example.com/release.jpg",
  "caption": "<b>Release 2.0 is out</b>\n\nFaster sync and a new export.\n\n<blockquote expandable>Sync now runs in the background. Export writes CSV and JSON.</blockquote>\n\nGo live: <tg-time unix=\"1798761600\" format=\"wDT\">Friday</tg-time>\n<a href=\"https://example.com/changelog\">Changelog</a>",
  "parse_mode": "HTML",
  "show_caption_above_media": true
}
```

## Rich: `sendRichMessage`

```json
{
  "chat_id": "@your_channel",
  "rich_message": {
    "html": "<h2>Release 2.0 is out</h2><img src=\"https://example.com/release.jpg\"/><p>Faster sync and a new export.</p><ul><li>Sync now runs in the background.</li><li>Export writes CSV and JSON.</li></ul><p>Go live: <tg-time unix=\"1798761600\" format=\"wDT\">Friday</tg-time></p><p><a href=\"https://example.com/changelog\">Changelog</a></p>"
  }
}
```

## Differences

| | Classic | Rich |
|---|---|---|
| Title | bold line | real heading |
| Details | expandable quote | list, or `<details>` to collapse |
| Text limit | 1024 in a caption | 32768 |
| Photo | message media, can be spoilered | a block at any position, with its own caption |
| Link preview | `sendPhoto` has none; `link_preview_options` applies to a text-only `sendMessage` | no `link_preview_options` |
| Long version | a second message | stays in one message |
| Reader on an old client | sees everything | sees an update placeholder for what the app can't render |
| Later edit | `editMessageCaption` | `editMessageText` with `rich_message`, see the known issues in `tg-rich-messages` |

Take the classic branch for a short announcement with one photo and the rich branch once the post needs a list, a table or more than 1024 characters.
