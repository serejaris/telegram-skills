# Telegram Bot API 10.3: Rich Message Formatting Reference

**API version:** 10.3
**Release date:** August 24, 2026
**Checked against the official pages on:** October 30, 2026. Bot API 10.3 was still the latest version on that date.
**Source:** https://core.telegram.org/bots/api

---

## Bot UI additions in 10.3

Primary sources: [InlineKeyboardButton](https://core.telegram.org/bots/api#inlinekeyboardbutton), [RichMessageButton](https://core.telegram.org/bots/api#richmessagebutton), [InputRichBlockButtons](https://core.telegram.org/bots/api#inputrichblockbuttons), [InputRichBlockTable](https://core.telegram.org/bots/api#inputrichblocktable).

- Inline keyboard `style`: `danger` (red), `success` (green), `primary` (blue). Omit for the app default. `link` is invalid on inline keyboard buttons.
- RichMessageButton accepts `danger`, `success`, `primary`, and `link`; `link` is allowed only with `callback_data`. Rich button text may contain plain text, custom emoji, and date-time entities. Exactly one action is required; callback data is 1–64 bytes.
- InputRichBlockButtons: `{"type":"buttons","buttons":[RichMessageButton,...],"align":"left"}`. One row contains 1–8 buttons. Optional alignment: `left`, `center`, `right`.
- Tables accept `is_compact: true`. Every cell requires `align` (`left|center|right`) and `valign` (`top|middle|bottom`); omitted cell text makes it invisible.
- Expandable quotations use `type: "expandable_blockquote"`, literal `text: RichText` and optional `credit` (not nested blocks or `is_open`).
- Document blocks use `type: "document"`, `document: InputMediaDocument`, optional rich `caption`; the nested media caption is ignored. Markup media references also support `tg://document?id=...`.
- `sendRichMessage` accepts `ephemeral_message_parameters`; draft methods accept `can_stop` and `keep_on_stop`. Ephemeral delivery and generation stopping require their own application lifecycle.

`sendRichMessage` creates a message. `editMessageText` updates a known message with exactly one of `text` or `rich_message`; there is no `editRichMessage` method. Keep the returned Bot API `message_id` and bind callbacks to the actual screen message. A timeout or 5xx has an unknown delivery outcome; do not blindly send a duplicate.

Direct block text is literal RichText, not HTML markup. Dynamic strings should remain strings; do not HTML-escape them before JSON encoding. Use `skip_entity_detection: true` when automatic mentions and links are unwanted. Native JSON uses `{"type":"pre","text":"{...}","language":"json"}`.

---

## Limits

Official list: [Rich Message Limits](https://core.telegram.org/bots/api#rich-message-limits).

| Limit | Value |
|---|---|
| UTF-8 characters in the rich message text, including custom emoji alternative text and formula source | **32,768** |
| Blocks, including nested blocks, list items, ordered list items, table rows, quotation blocks and details blocks | **500** |
| Levels of nested formatting and blocks | **16** |
| Media attachments in total | **50** |
| Columns in a table | **20** |
| Buttons in one `buttons` block | **1–8** |
| `InputRichMessageMedia.id` | 1–64 characters, `A-Z`, `a-z`, `0-9`, `_`, `-` |
| `callback_data` of a rich button | 1–64 bytes |
| `InputRichBlockMap` | `zoom` 0–24; `width` and `height` 0–10,000 each, at most 10,000 in total; ratio at most 20 |

---

## Known bugs

Practitioner reports from public trackers, not documented behavior. Status checked on 2026-10-30; recheck the link before you design around one.

| Symptom | Report | Filed | Status |
|---|---|---|---|
| `editMessageText` with `rich_message` drops custom emoji that `sendRichMessage` kept. The call returns `ok: true`. Reproduced with `html` and `blocks`. | [tdlib/telegram-bot-api#865](https://github.com/tdlib/telegram-bot-api/issues/865) | 2026-07-04 | open |
| The same loss in supergroups when the original message is not a reply. Not reproduced in basic groups. | [tdlib/telegram-bot-api#904](https://github.com/tdlib/telegram-bot-api/issues/904) | 2026-09-28 | open |
| After an edit of an inline message, custom emoji turn into plain Unicode in groups, supergroups and channels. Private chats are not affected. | [tdlib/telegram-bot-api#880](https://github.com/tdlib/telegram-bot-api/issues/880) | 2026-07-30 | open |
| `chosen_inline_result` arrives without `inline_message_id` when the result uses `InputRichMessageContent` with rich buttons. Callback queries from those buttons carry it. A maintainer replied that the update exists for statistics and is not guaranteed. | [tdlib/telegram-bot-api#895](https://github.com/tdlib/telegram-bot-api/issues/895) | 2026-08-28 | open |

The three custom emoji reports describe different conditions; a shared cause is not established. Treat any edit of a rich message with custom emoji as lossy: check the result in a real client, or resend instead of editing.

---

## Methods

### sendRichMessage

Sends a rich message. If the message contains a block with a media element, the bot must have the right to send that media to the chat. On success, the sent [Message] is returned.

| Parameter | Type | Required | Description |
|---|---|---|---|
| business_connection_id | String | Optional | Unique identifier of the business connection on behalf of which the message will be sent. A bot can send rich messages on behalf of a business account only if the corresponding user can send rich messages. |
| chat_id | Integer or String | **Yes** | Unique identifier for the target chat or username of the target bot, supergroup or channel in the format `@username` |
| message_thread_id | Integer | Optional | Unique identifier for the target message thread (topic) of a forum; for forum supergroups and private chats of bots with forum topic mode enabled only |
| direct_messages_topic_id | Integer | Optional | Identifier of the direct messages topic to which the message will be sent; required if the message is sent to a direct messages chat |
| ephemeral_message_parameters | EphemeralMessageParameters | Optional | Parameters of the ephemeral message to send (10.3) |
| rich_message | InputRichMessage | **Yes** | The message to be sent |
| disable_notification | Boolean | Optional | Sends the message silently. Users will receive a notification with no sound. |
| protect_content | Boolean | Optional | Protects the contents of the sent message from forwarding and saving |
| allow_paid_broadcast | Boolean | Optional | Pass *True* to allow up to 1000 messages per second, ignoring broadcasting limits for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance. |
| message_effect_id | String | Optional | Unique identifier of the message effect to be added to the message; for private chats only |
| suggested_post_parameters | SuggestedPostParameters | Optional | A JSON-serialized object containing the parameters of the suggested post to send; for direct messages chats only. If the message is sent as a reply to another suggested post, then that suggested post is automatically declined. |
| reply_parameters | ReplyParameters | Optional | Description of the message to reply to |
| reply_markup | InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply | Optional | Additional interface options |

The method has no `link_preview_options` parameter, and neither does `InputRichMessage`.

---

### sendMessageDraft

Streams a partial plain-text message to a user while it is being generated. The draft is ephemeral and acts as a temporary 30-second preview. Once the output is finalized, call `sendMessage` with the complete message to persist it. Returns *True* on success. Added in 9.3, available to all bots since 9.5.

| Parameter | Type | Required | Description |
|---|---|---|---|
| chat_id | Integer | **Yes** | Unique identifier for the target **private chat** |
| message_thread_id | Integer | Optional | Unique identifier for the target message thread |
| draft_id | Integer | **Yes** | Unique identifier of the message draft; must be non-zero. Changes to drafts with the same identifier are animated. Otherwise, the draft is replaced without animation. |
| text | String | Optional | 0–4096 characters after entities parsing. Pass an empty text to show a "Thinking…" placeholder. |
| parse_mode | String | Optional | Mode for parsing entities in the message text |
| entities | Array of MessageEntity | Optional | Special entities; can be specified instead of *parse_mode* |
| can_stop | Boolean | Optional | Pass *True* to show a button that stops further drafts; the bot receives the `stopped_message_generation` update (10.3) |
| keep_on_stop | Boolean | Optional | Pass *True* to keep the draft in the chat when the button is pressed. The draft still disappears after a short time or when the bot sends a message; to preserve it, send it as a new message (10.3) |

---

### sendRichMessageDraft

Streams a partial rich message to a user while it is being generated. **The draft is ephemeral and acts as a temporary 30-second preview**: once the output is finalized, you **must** call `sendRichMessage` with the complete message to persist it. Returns *True* on success.

> **Important:** `sendRichMessageDraft` works only for **private chats** (`chat_id` is an Integer, not a String or `@username`).

| Parameter | Type | Required | Description |
|---|---|---|---|
| chat_id | Integer | **Yes** | Unique identifier for the target **private chat** |
| message_thread_id | Integer | Optional | Unique identifier for the target message thread |
| draft_id | Integer | **Yes** | Unique identifier of the message draft; must be non-zero. Changes to drafts with the same identifier are animated. Otherwise, the draft is replaced without animation. |
| rich_message | InputRichMessage | **Yes** | The partial message to be streamed. Direct upload of new files and explicit upload of files by a URL aren't supported. |
| can_stop | Boolean | Optional | Pass *True* to show a button that stops further drafts; the bot receives the `stopped_message_generation` update |
| keep_on_stop | Boolean | Optional | Pass *True* to keep the draft in the chat when the button is pressed. The draft still disappears after a short time or when the bot sends a message; to preserve it, send it as a new message |

### MessageGenerationStopped

The `stopped_message_generation` update of the class `Update` (10.3).

| Field | Type | Description |
|---|---|---|
| chat | Chat | Chat in which the message is generated |
| message_thread_id | Integer | *Optional*. Identifier of the message thread in which the message is generated |
| draft_id | Integer | Identifier of the message draft which was stopped |

---

### editMessageText (rich_message parameter)

Edits text, rich and game messages. On success, returns the edited Message, or *True* for inline messages.

The `text` and `rich_message` parameters are mutually exclusive: exactly one is required.

| Parameter | Type | Required | Description |
|---|---|---|---|
| business_connection_id | String | Optional | Unique identifier of the business connection on behalf of which the message to be edited was sent |
| chat_id | Integer or String | Optional | Required if *inline_message_id* is not specified. |
| message_id | Integer | Optional | Required if *inline_message_id* is not specified. |
| inline_message_id | String | Optional | Required if *chat_id* and *message_id* are not specified. |
| text | String | Optional | New text of the message, 1-4096 characters after entity parsing; **required if *rich_message* isn't specified** |
| parse_mode | String | Optional | Mode for parsing entities in the message text |
| entities | Array of MessageEntity | Optional | Special entities; can be specified instead of *parse_mode* |
| link_preview_options | LinkPreviewOptions | Optional | Link preview generation options for the message. Applies to `text` edits; `InputRichMessage` has no such field. |
| **rich_message** | **InputRichMessage** | **Optional** | **New rich content of the message; required if *text* isn't specified. Direct upload of new files and explicit upload of files by a URL aren't supported when an inline message is edited.** |
| reply_markup | InlineKeyboardMarkup | Optional | A JSON-serialized object for an inline keyboard |

---

## Root types

### RichMessage

A rich formatted message. Received in `Message`, not used for sending.

| Field | Type | Description |
|---|---|---|
| blocks | Array of RichBlock | Content of the message |
| is_rtl | Boolean | *Optional*. *True*, if the rich message must be shown right-to-left |

`Message.rich_message` has the type `RichMessage`, not `InputRichMessage`.

---

### InputRichMessage

Describes a rich message to be sent. Exactly **one** of the fields *html*, *markdown* or *blocks* must be used.

| Field | Type | Description |
|---|---|---|
| blocks | Array of InputRichBlock | *Optional*. Content described directly as outgoing block entities |
| html | String | *Optional*. Content of the rich message described using HTML formatting |
| markdown | String | *Optional*. Content of the rich message described using Markdown formatting |
| media | Array of InputRichMessageMedia | *Optional*. Media referenced from `html` or `markdown` via `tg://photo?id=`, `tg://video?id=`, `tg://document?id=`, or `tg://audio?id=` |
| is_rtl | Boolean | *Optional*. Pass *True* if the rich message must be shown right-to-left |
| skip_entity_detection | Boolean | *Optional*. Pass *True* to skip automatic detection of entities (URLs, email addresses, username mentions, hashtags, cashtags, bot commands, phone numbers) |

`media` is used with `html` or `markdown`. Direct `blocks` embed `InputMedia*` objects in their
media blocks and don't need indirection through `InputRichMessage.media`.

### InputRichMessageMedia

Binds an identifier from the markup to the media being sent.

| Field | Type | Description |
|---|---|---|
| id | String | Identifier used in a `tg://photo?id=`, `tg://video?id=`, `tg://document?id=`, or `tg://audio?id=` link. Length 1–64; allowed characters: `A-Z`, `a-z`, `0-9`, `_`, `-` |
| media | InputMediaAnimation or InputMediaAudio or InputMediaDocument or InputMediaPhoto or InputMediaVideo or InputMediaVoiceNote | Media to send. Everything except the media itself and its properties is ignored |

`InputMedia*.media` supports the standard Telegram file forms:

- Telegram `file_id` (recommended for an already uploaded file);
- public HTTP/HTTPS URL;
- `attach://<name>` with a matching multipart/form-data file part named `<name>`.

JSON requests can use `file_id` and HTTP/HTTPS URLs. `attach://` requires multipart/form-data;
the JSON-serialized `rich_message` is one form field and each upload is another form field.

### InputRichBlock

Bot API 10.2 added outgoing equivalents for the rich block types, and 10.3 extended them. There are 24 types. Their JSON shape follows the
received `RichBlock` shape, with nested content typed as `InputRichBlock` and media fields typed
as `InputMedia*`.

| Input type | Required content |
|---|---|
| InputRichBlockParagraph | `{"type":"paragraph","text":RichText}` |
| InputRichBlockSectionHeading | `{"type":"heading","text":RichText,"size":1..6}` |
| InputRichBlockPreformatted | `{"type":"pre","text":RichText,"language"?}` |
| InputRichBlockFooter | `{"type":"footer","text":RichText}` |
| InputRichBlockDivider | `{"type":"divider"}` |
| InputRichBlockMathematicalExpression | `{"type":"mathematical_expression","expression":"..."}` |
| InputRichBlockAnchor | `{"type":"anchor","name":"..."}` |
| InputRichBlockList | `{"type":"list","items":InputRichBlockListItem[]}` |
| InputRichBlockBlockQuotation | `{"type":"blockquote","blocks":InputRichBlock[],"credit"?}` |
| InputRichBlockExpandableBlockQuotation | `{"type":"expandable_blockquote","text":RichText,"credit"?}` |
| InputRichBlockPullQuotation | `{"type":"pullquote","text":RichText,"credit"?}` |
| InputRichBlockCollage | `{"type":"collage","blocks":InputRichBlock[],"caption"?}` |
| InputRichBlockSlideshow | `{"type":"slideshow","blocks":InputRichBlock[],"caption"?}` |
| InputRichBlockTable | `{"type":"table","cells":RichBlockTableCell[][],"is_bordered"?,"is_striped"?,"is_compact"?,"caption"?}` |
| InputRichBlockDetails | `{"type":"details","summary":RichText,"blocks":InputRichBlock[],"is_open"?}` |
| InputRichBlockMap | `{"type":"map","location":Location,"zoom"?:0..24,"width"?:0..10000,"height"?:0..10000,"caption"?}` |
| InputRichBlockButtons | `{"type":"buttons","buttons":RichMessageButton[1..8],"align"?}` |
| InputRichBlockAnimation | `{"type":"animation","animation":InputMediaAnimation,"caption"?}` |
| InputRichBlockAudio | `{"type":"audio","audio":InputMediaAudio,"caption"?}` |
| InputRichBlockDocument | `{"type":"document","document":InputMediaDocument,"caption"?}` |
| InputRichBlockPhoto | `{"type":"photo","photo":InputMediaPhoto,"caption"?}` |
| InputRichBlockVideo | `{"type":"video","video":InputMediaVideo,"caption"?}` |
| InputRichBlockVoiceNote | `{"type":"voice_note","voice_note":InputMediaVoiceNote,"caption"?}` |
| InputRichBlockThinking | `{"type":"thinking","text":RichText}`; draft-only |

For `InputRichBlockAnimation`, `Audio`, `Document`, `Photo`, `Video`, and `VoiceNote`, the caption inside the
nested `InputMedia*` object is ignored. Put the rich caption in the block's `caption`.

### InputRichBlockListItem

| Field | Type | Description |
|---|---|---|
| blocks | Array of InputRichBlock | Content of the item |
| has_checkbox | True | *Optional*. Show a checkbox |
| is_checked | True | *Optional*. Show a checked checkbox |
| value | Integer | *Optional*. Explicit numeric value for ordered lists |
| type | String | *Optional*. Label type: `a`, `A`, `i`, `I`, or `1` |

---

### RichMessageButton

A button in a rich message (10.3). Exactly one of the fields other than `text` and `style` must be used.

| Field | Type | Description |
|---|---|---|
| text | RichText | Text of the button. May contain only plain text, RichTextCustomEmoji and RichTextDateTime entities. |
| style | String | *Optional*. One of `danger`, `success`, `primary`, or `link` (a regular link without borders). `link` is allowed only for callback buttons. |
| url | String | *Optional*. HTTP or tg:// URL to open when the button is pressed |
| callback_data | String | *Optional*. Data sent in a callback query, 1–64 bytes |
| web_app | WebAppInfo | *Optional*. Web App launched when the button is pressed. Private chats between a user and the bot only; not supported for messages sent on behalf of a business account. |
| login_url | LoginUrl | *Optional*. HTTPS URL used to authorize the user automatically. Not supported for ephemeral messages. |
| switch_inline_query | String | *Optional*. Prompts the user to select a chat and inserts the bot's username and the query. Not supported in channel direct messages chats and on behalf of a business account. |
| switch_inline_query_current_chat | String | *Optional*. Inserts the bot's username and the query in the current chat. Not supported in channels, channel direct messages chats and on behalf of a business account. |
| switch_inline_query_chosen_chat | SwitchInlineQueryChosenChat | *Optional*. Prompts the user to select a chat of the specified type. Not supported in channel direct messages chats and on behalf of a business account. |
| copy_text | CopyTextButton | *Optional*. Copies the specified text to the clipboard |
| disabled | DisabledButton | *Optional*. The button is disabled and does nothing |

---

### InputRichMessageContent

The content of a rich message sent as the result of an inline query. A subtype of `InputMessageContent`, added in 10.1.

Used in the results of inline queries, guest queries and Web App queries.

| Field | Type | Description |
|---|---|---|
| rich_message | InputRichMessage | The message to be sent. Only previously uploaded files may be used in the message. |

---

### RichText

A rich formatted text. It can be:
- a **String** for plain text;
- an **Array of RichText**, which concatenates the texts;
- **any of the types below** (26 types).

**All subtypes:** RichTextBold, RichTextItalic, RichTextUnderline, RichTextStrikethrough, RichTextSpoiler, RichTextDateTime, RichTextTextMention, RichTextSubscript, RichTextSuperscript, RichTextMarked, RichTextCode, RichTextCustomEmoji, RichTextMathematicalExpression, RichTextUrl, RichTextEmailAddress, RichTextPhoneNumber, RichTextBankCardNumber, RichTextMention, RichTextHashtag, RichTextCashtag, RichTextBotCommand, RichTextButton, RichTextAnchor, RichTextAnchorLink, RichTextReference, RichTextReferenceLink

---

### RichBlock

A block in a rich formatted message. It can be any of 24 types:

RichBlockParagraph, RichBlockSectionHeading, RichBlockPreformatted, RichBlockFooter, RichBlockDivider, RichBlockMathematicalExpression, RichBlockAnchor, RichBlockList, RichBlockBlockQuotation, RichBlockExpandableBlockQuotation, RichBlockPullQuotation, RichBlockCollage, RichBlockSlideshow, RichBlockTable, RichBlockDetails, RichBlockMap, RichBlockButtons, RichBlockAnimation, RichBlockAudio, RichBlockDocument, RichBlockPhoto, RichBlockVideo, RichBlockVoiceNote, RichBlockThinking

---

### RichBlockCaption

A caption of a rich block (photo, video, audio, animation, document, map, collage, slideshow).

| Field | Type | Description |
|---|---|---|
| text | RichText | Block caption |
| credit | RichText | *Optional*. Block credit, corresponds to HTML tag `<cite>` |

---

### RichBlockTableCell

A table cell.

| Field | Type | Description |
|---|---|---|
| text | RichText | *Optional*. Text in the cell. If omitted, then the cell is invisible. |
| is_header | True | *Optional*. *True*, if the cell is a header cell |
| colspan | Integer | *Optional*. The number of columns the cell spans if it is bigger than 1 |
| rowspan | Integer | *Optional*. The number of rows the cell spans if it is bigger than 1 |
| align | String | Horizontal cell content alignment. Must be one of "left", "center", or "right". |
| valign | String | Vertical cell content alignment. Must be one of "top", "middle", or "bottom". |

---

### RichBlockListItem

A list item.

| Field | Type | Description |
|---|---|---|
| label | String | Label of the item |
| blocks | Array of RichBlock | The content of the item |
| has_checkbox | True | *Optional*. *True*, if the item has a checkbox |
| is_checked | True | *Optional*. *True*, if the item has a checked checkbox |
| value | Integer | *Optional*. For ordered lists, the numeric value of the item label |
| type | String | *Optional*. For ordered lists, type of label: "a" (lowercase letters), "A" (uppercase letters), "i" (lowercase Roman numerals), "I" (uppercase Roman numerals), or "1" (decimal numbers) |

---

## Blocks (RichBlock*)

### RichBlockParagraph

A text paragraph, corresponding to the HTML tag `<p>`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"paragraph"** |
| text | RichText | Text of the block |

---

### RichBlockSectionHeading

A section heading, corresponding to the HTML tags `<h1>`, `<h2>`, `<h3>`, `<h4>`, `<h5>`, or `<h6>`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"heading"** |
| text | RichText | Text of the block |
| size | Integer | Relative size of the text font; 1-6, 1 is the largest, 6 is the smallest |

---

### RichBlockPreformatted

A preformatted (code) block, corresponding to the HTML tags `<pre>` and `<code>`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"pre"** |
| text | RichText | Text of the block |
| language | String | *Optional*. The programming language of the text |

---

### RichBlockFooter

A footer, corresponding to the HTML tag `<footer>`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"footer"** |
| text | RichText | Text of the block |

---

### RichBlockDivider

A divider, corresponding to the HTML tag `<hr/>`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"divider"** |

---

### RichBlockMathematicalExpression

A block with a mathematical expression in LaTeX format, corresponding to the custom HTML tag `<tg-math-block>`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"mathematical_expression"** |
| expression | String | The mathematical expression in LaTeX format |

---

### RichBlockAnchor

A block with an anchor, corresponding to the HTML tag `<a>` with the `name` attribute.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"anchor"** |
| name | String | The name of the anchor |

---

### RichBlockList

A list of blocks, corresponding to the HTML tags `<ul>` or `<ol>` with nested `<li>`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"list"** |
| items | Array of RichBlockListItem | Items of the list |

---

### RichBlockBlockQuotation

A block quotation, corresponding to the HTML tag `<blockquote>`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"blockquote"** |
| blocks | Array of RichBlock | Content of the block |
| credit | RichText | *Optional*. Credit of the block |

---

### RichBlockExpandableBlockQuotation

A block quotation that can be expanded or collapsed back, corresponding to the HTML tag `<blockquote>` with the custom attribute `expandable` (10.3).

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"expandable_blockquote"** |
| text | RichText | Content of the block |
| credit | RichText | *Optional*. Credit of the block |

---

### RichBlockPullQuotation

A center-aligned quotation, roughly corresponding to the HTML tag `<aside>`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"pullquote"** |
| text | RichText | Text of the block |
| credit | RichText | *Optional*. Credit of the block |

---

### RichBlockCollage

A collage, corresponding to the custom HTML tag `<tg-collage>`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"collage"** |
| blocks | Array of RichBlock | Elements of the collage |
| caption | RichBlockCaption | *Optional*. Caption of the block |

---

### RichBlockSlideshow

A slideshow, corresponding to the custom HTML tag `<tg-slideshow>`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"slideshow"** |
| blocks | Array of RichBlock | Elements of the slideshow |
| caption | RichBlockCaption | *Optional*. Caption of the block |

---

### RichBlockTable

A table, corresponding to the HTML tag `<table>`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"table"** |
| cells | Array of Array of RichBlockTableCell | Cells of the table |
| is_bordered | True | *Optional*. *True*, if the table has borders |
| is_compact | True | *Optional*. Compact cell indents (10.3) |
| is_striped | True | *Optional*. *True*, if the table is striped |
| caption | RichText | *Optional*. Caption of the table |

---

### RichBlockDetails

An expandable block, corresponding to the HTML tag `<details>`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"details"** |
| summary | RichText | Always shown summary of the block |
| blocks | Array of RichBlock | Content of the block |
| is_open | True | *Optional*. *True*, if the content of the block is visible by default |

---

### RichBlockMap

A block with a map, corresponding to the custom HTML tag `<tg-map>`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"map"** |
| location | Location | Location of the center of the map |
| zoom | Integer | Map zoom level (received RichBlockMap); outgoing InputRichBlockMap.zoom is optional, 0–24 |
| width | Integer | Expected width of the map |
| height | Integer | Expected height of the map |
| caption | RichBlockCaption | *Optional*. Caption of the block |

---

### RichBlockButtons

A block with a list of buttons shown in one row, corresponding to the custom HTML tag `<tg-button-row>` (10.3).

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"buttons"** |
| buttons | Array of RichMessageButton | The buttons |
| align | String | *Optional*. Horizontal alignment of the buttons: "left", "center", or "right" |

---

### RichBlockAnimation

A block with an animation, corresponding to the HTML tag `<video>`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"animation"** |
| animation | Animation | The animation |
| has_spoiler | True | *Optional*. *True*, if the media preview is covered by a spoiler animation |
| caption | RichBlockCaption | *Optional*. Caption of the block |

---

### RichBlockAudio

A block with a music file, corresponding to the HTML tag `<audio>`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"audio"** |
| audio | Audio | The audio |
| caption | RichBlockCaption | *Optional*. Caption of the block |

---

### RichBlockDocument

A block with a general file, corresponding to the custom HTML tag `<tg-document>` (10.3).

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"document"** |
| document | Document | The document |
| caption | RichBlockCaption | *Optional*. Caption of the block |

---

### RichBlockPhoto

A block with a photo, corresponding to the HTML tag `<img>`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"photo"** |
| photo | Array of PhotoSize | Available sizes of the photo |
| has_spoiler | True | *Optional*. *True*, if the media preview is covered by a spoiler animation |
| caption | RichBlockCaption | *Optional*. Caption of the block |

---

### RichBlockVideo

A block with a video, corresponding to the HTML tag `<video>`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"video"** |
| video | Video | The video |
| has_spoiler | True | *Optional*. *True*, if the media preview is covered by a spoiler animation |
| caption | RichBlockCaption | *Optional*. Caption of the block |

---

### RichBlockVoiceNote

A block with a voice message, corresponding to the HTML tag `<audio>`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"voice_note"** |
| voice_note | Voice | The voice note |
| caption | RichBlockCaption | *Optional*. Caption of the block |

---

### RichBlockThinking

A "Thinking…" placeholder block, corresponding to the custom HTML tag `<tg-thinking>`.

**Hard constraint:** it can be used **only** in `sendRichMessageDraft`. It can't be received in messages and is never stored in a Message.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"thinking"** |
| text | RichText | Text of the block. See https://t.me/addemoji/AIActions for examples of custom emoji recommended for usage in the block. |

---

## Inline text (RichText*)

### RichTextBold

Bold text.

| Field | Type | Description |
|---|---|---|
| type | String | always **"bold"** |
| text | RichText | The text |

---

### RichTextItalic

Italic text.

| Field | Type | Description |
|---|---|---|
| type | String | always **"italic"** |
| text | RichText | The text |

---

### RichTextUnderline

Underlined text.

| Field | Type | Description |
|---|---|---|
| type | String | always **"underline"** |
| text | RichText | The text |

---

### RichTextStrikethrough

Strikethrough text.

| Field | Type | Description |
|---|---|---|
| type | String | always **"strikethrough"** |
| text | RichText | The text |

---

### RichTextSpoiler

Text hidden behind a spoiler.

| Field | Type | Description |
|---|---|---|
| type | String | always **"spoiler"** |
| text | RichText | The text |

---

### RichTextDateTime

Formatted date and time.

| Field | Type | Description |
|---|---|---|
| type | String | always **"date_time"** |
| text | RichText | The text |
| unix_time | Integer | The Unix time associated with the entity |
| date_time_format | String | The string that defines the formatting of the date and time. See date-time entity formatting for more details. |

---

### RichTextTextMention

A mention of a Telegram user by identifier.

| Field | Type | Description |
|---|---|---|
| type | String | always **"text_mention"** |
| text | RichText | The text |
| user | User | The mentioned user |

---

### RichTextSubscript

Subscript text.

| Field | Type | Description |
|---|---|---|
| type | String | always **"subscript"** |
| text | RichText | The text |

---

### RichTextSuperscript

Superscript text.

| Field | Type | Description |
|---|---|---|
| type | String | always **"superscript"** |
| text | RichText | The text |

---

### RichTextMarked

Marked (highlighted) text.

| Field | Type | Description |
|---|---|---|
| type | String | always **"marked"** |
| text | RichText | The text |

---

### RichTextCode

Monospace text (inline code).

| Field | Type | Description |
|---|---|---|
| type | String | always **"code"** |
| text | RichText | The text |

---

### RichTextCustomEmoji

A custom emoji.

| Field | Type | Description |
|---|---|---|
| type | String | always **"custom_emoji"** |
| custom_emoji_id | String | Unique identifier of the custom emoji. Use getCustomEmojiStickers to get full information about the sticker. |
| alternative_text | String | Alternative emoji for the custom emoji |

---

### RichTextMathematicalExpression

An inline mathematical expression.

| Field | Type | Description |
|---|---|---|
| type | String | always **"mathematical_expression"** |
| expression | String | The expression in LaTeX format |

---

### RichTextUrl

Text with a link.

| Field | Type | Description |
|---|---|---|
| type | String | always **"url"** |
| text | RichText | The text |
| url | String | URL of the link |

---

### RichTextEmailAddress

Text with an email address.

| Field | Type | Description |
|---|---|---|
| type | String | always **"email_address"** |
| text | RichText | The text |
| email_address | String | The email address |

---

### RichTextPhoneNumber

Text with a phone number.

| Field | Type | Description |
|---|---|---|
| type | String | always **"phone_number"** |
| text | RichText | The text |
| phone_number | String | The phone number |

---

### RichTextBankCardNumber

Text with a bank card number.

| Field | Type | Description |
|---|---|---|
| type | String | always **"bank_card_number"** |
| text | RichText | The text |
| bank_card_number | String | The bank card number |

---

### RichTextMention

A mention by username.

| Field | Type | Description |
|---|---|---|
| type | String | always **"mention"** |
| text | RichText | The text |
| username | String | The username |

---

### RichTextHashtag

A hashtag.

| Field | Type | Description |
|---|---|---|
| type | String | always **"hashtag"** |
| text | RichText | The text |
| hashtag | String | The hashtag |

---

### RichTextCashtag

A cashtag.

| Field | Type | Description |
|---|---|---|
| type | String | always **"cashtag"** |
| text | RichText | The text |
| cashtag | String | The cashtag |

---

### RichTextBotCommand

A bot command.

| Field | Type | Description |
|---|---|---|
| type | String | always **"bot_command"** |
| text | RichText | The text |
| bot_command | String | The bot command |

---

### RichTextButton

A button inside rich text, corresponding to the custom HTML tag `<tg-button>` (10.3).

| Field | Type | Description |
|---|---|---|
| type | String | always **"button"** |
| button | RichMessageButton | The button |

---

### RichTextAnchor

An anchor point for in-document navigation.

| Field | Type | Description |
|---|---|---|
| type | String | always **"anchor"** |
| name | String | The name of the anchor |

---

### RichTextAnchorLink

A link to an anchor.

| Field | Type | Description |
|---|---|---|
| type | String | always **"anchor_link"** |
| text | RichText | The link text |
| anchor_name | String | The name of the anchor. If the name is empty, then the link brings back to the top of the message. |

---

### RichTextReference

A reference definition. Corresponds to `<tg-reference name="...">...</tg-reference>`.

| Field | Type | Description |
|---|---|---|
| type | String | always **"reference"** |
| text | RichText | Text of the reference |
| name | String | The name of the reference |

---

### RichTextReferenceLink

A link to a reference. Corresponds to `<a href="#...">`.

| Field | Type | Description |
|---|---|---|
| type | String | always **"reference_link"** |
| text | RichText | The link text |
| reference_name | String | The name of the reference |

---

## Formatting: Markdown and HTML syntax

### Rich Markdown style

Pass the content in the `markdown` field of `InputRichMessage`. Syntax:

````
**bold text**          # or __bold text__
*italic text*          # or _italic text_
~~strikethrough text~~
`inline fixed-width code`
==marked text==
||spoiler||

[inline URL](https://t.me/)
[inline e-mail](mailto:user@example.com)
[inline phone number](tel:+123456789)
[inline mention of a user](tg://user?id=123456789)
![👍](tg://emoji?id=5368324170671202286)
![22:45 tomorrow](tg://time?unix=1647531900&format=wDT)
$x^2 + y^2$           # inline LaTeX formula

# Heading 1
## Heading 2  ...  ###### Heading 6

```python
print('preformatted code block')
```

---                    # divider

- unordered list item
* unordered list item
+ unordered list item

1. ordered list item

- [ ] task list item
- [x] completed task list item

>Block quotation line

![](https://example.com/photo.jpg)               # photo block
![](https://example.com/video.mp4)               # video block
![](https://example.com/audio.mp3)               # audio block
![](https://example.com/audio.ogg)               # voice note block
![](https://example.com/animation.gif)           # animation block
![](https://example.com/document.zip)            # document block

![](https://example.com/photo.jpg "Photo caption")  # with a caption

| Header 1 | Header 2 |
|:---------|:--------:|
| left     | center   |

Text with a reference[^id1].
[^id1]: Definition of the footnote.

$$E = mc^2$$           # block LaTeX formula
```math
E = mc^2
```

<details open><summary>Summary with **bold text**</summary>
### Details heading
</details>

<tg-collage>
![](https://example.com/photo.jpg)
</tg-collage>

<tg-slideshow>
![](https://example.com/photo.jpg)
</tg-slideshow>
````

Features without Markdown syntax use HTML tags:
```html
<u>underlined</u>, <ins>underlined</ins>
<sub>subscript</sub>
<sup>superscript</sup>
<a name="chapter-1"></a>
<aside>Pull quote<cite>The Author</cite></aside>
<details open><summary>Title</summary>Content</details>
<tg-map lat="41.9" long="12.5" zoom="14"/>
<tg-button-row align="left"><tg-button type="url" url="https://t.me">url</tg-button></tg-button-row>
```

### Rich HTML style

Pass the content in the `html` field of `InputRichMessage`.

Supported tags:
- `<b>`, `<strong>` — bold
- `<i>`, `<em>` — italic
- `<u>`, `<ins>` — underline
- `<s>`, `<strike>`, `<del>` — strikethrough
- `<code>` — inline code (a programming language can't be set on a standalone `code`)
- `<mark>` — marked/highlight
- `<sub>` — subscript
- `<sup>` — superscript
- `<tg-spoiler>` — spoiler
- `<a href="https://...">` — URL link
- `<a href="mailto:...">` — email link
- `<a href="tel:...">` — phone link
- `<a href="tg://user?id=...">` — inline user mention
- `<a href="#anchor-name">` — in-document anchor link
- `<a name="anchor-name"></a>` — anchor definition
- `<tg-reference name="...">...</tg-reference>` — reference definition
- `<tg-emoji emoji-id="...">fallback</tg-emoji>` — custom emoji
- `<img src="tg://emoji?id=..."/>` — custom emoji (alternative syntax)
- `<tg-time unix="..." format="...">text</tg-time>` — datetime
- `<tg-math>LaTeX</tg-math>` — inline formula
- `<h1>`...`<h6>` — headings
- `<p>` — paragraph
- `<pre>` — preformatted block
- `<pre><code class="language-python">...</code></pre>` — with a language
- `<footer>` — footer
- `<hr/>` — divider
- `<ul><li>...</li></ul>` — unordered list
- `<ol><li>...</li></ol>` — ordered list (attributes: `start`, `type`, `reversed`)
- `<ol><li value="7" type="i">...</li></ol>` — explicit item value
- `<ul><li><input type="checkbox" checked>...</li></ul>` — checkbox item
- `<blockquote>...<cite>The Author</cite></blockquote>` — block quotation
- `<blockquote expandable>...<cite>The Author</cite></blockquote>` — expandable block quotation
- `<aside>...<cite>The Author</cite></aside>` — pull quotation
- `<img src="https://..."/>` — photo block
- `<video src="https://..."></video>` — video block (or animation for .gif)
- `<audio src="https://...mp3"></audio>` — audio block
- `<audio src="https://...ogg"></audio>` — voice note block
- `<tg-document src="https://..."></tg-document>` — document block
- `<figure><img src="..." tg-spoiler/><figcaption>Caption<cite>Credit</cite></figcaption></figure>` — media with a caption and a spoiler
- `<tg-map lat="..." long="..." zoom="..."/>` — map block
- `<tg-collage>...</tg-collage>` — collage
- `<tg-slideshow>...</tg-slideshow>` — slideshow
- `<table bordered striped compact><caption>...</caption><tr><th>...</th><td colspan="2" rowspan="2" align="left" valign="top">...</td></tr></table>` — table
- `<details>` / `<details open>` — collapsible block with `<summary>`
- `<tg-math-block>LaTeX</tg-math-block>` — block formula
- `<tg-button type="url" url="https://t.me">...</tg-button>` — inline button; `type` is `url`, `callback_data`, `web_app`, `login_url`, `switch_inline_query`, `switch_inline_query_current_chat`, `switch_inline_query_chosen_chat`, `copy_text`, or `disabled`
- `<tg-button-row align="left">...</tg-button-row>` — button row

`<tg-thinking>Thinking...</tg-thinking>` is available only in `sendRichMessageDraft`.

**Supported HTML entities:** all numerical ones, plus `&lt;`, `&gt;`, `&amp;`, `&quot;`, `&apos;`, `&nbsp;`, `&hellip;`, `&mdash;`, `&ndash;`, `&lsquo;`, `&rsquo;`, `&ldquo;`, `&rdquo;`.

---

## Constraints and notes

### Media

- Media can be specified **only as separate blocks**, never inline.
- In markup a media block takes one of two sources: a direct HTTP/HTTPS URL, or a `tg://photo|video|document|audio?id=` link bound through `InputRichMessage.media`. The bound `InputMedia*.media` is a `file_id`, a URL, or a multipart `attach://` upload.
- The official formatting notes still say "Media blocks support only HTTP and HTTPS URLs". Read that sentence as the rule for a literal URL in markup: the introduction to the same section allows `tg://` links "to reuse previously uploaded files or upload a new file".
- The media type of a direct URL is determined by the MIME type and the URL. The type of a bound item comes from the nested `InputMedia*` object.
- In Markdown syntax, the optional title after the URL is used as the caption.
- Photo, video and animation blocks support the `tg-spoiler` attribute that hides the preview; `has_spoiler` exists only on those three received block types.

### Automatic entity detection

Plain URLs, email addresses, username mentions, hashtags, cashtags, bot commands, phone numbers and bank card numbers are detected by default. To disable detection, pass `skip_entity_detection: True` in `InputRichMessage`.

Telegram clients show an "Open this link?" alert with the full URL before following an inline link.

### Link previews

`sendRichMessage` and `InputRichMessage` have no `link_preview_options`, so a rich message gets no link preview control. If the post needs a large preview or a chosen preview URL, use `sendMessage`.

### Custom emoji

The formatting rules allow custom emoji for bots that purchased additional usernames on Fragment, or in messages the bot sends directly to private, group and supergroup chats when the bot's owner has Telegram Premium. Channels aren't named in the second case, so don't rely on custom emoji in a channel post without a Fragment username. Rich messages from a bot to a channel with custom emoji were not tested live for this reference. See also [Known bugs](#known-bugs) for edits.

### Drafts

- A draft is **ephemeral**: a 30-second preview that isn't stored in the chat.
- After the output is finalized, you **must** call `sendRichMessage` (or `sendMessage` for `sendMessageDraft`) with the complete message.
- `draft_id` must be non-zero; changes to drafts with the same `draft_id` are **animated**.
- Drafts work **only in private chats** (`chat_id` is an Integer, not `@username`).
- `RichBlockThinking` can be used **only** in `sendRichMessageDraft`. Recommended custom emoji for it: https://t.me/addemoji/AIActions

### Rich Markdown compatibility

- Rich Markdown is **compatible with GitHub Flavored Markdown** where possible.
- It can contain arbitrary HTML; supported rich message HTML tags are parsed as in Rich HTML style.
- Nested markdown inside inline HTML tags is parsed. Markdown isn't parsed inside block HTML tags other than `<details>`, `<tg-collage>` and `<tg-slideshow>`, so only HTML tags can be used there.

### Tables

- Table cells can contain **only inline formatting**, not blocks.

### Formulas

- Formula source is treated as **raw LaTeX**.

### Anchors and links

- An empty `<a name="..."></a>` on its own creates an anchor for navigation via `<a href="#...">`.
- `RichTextAnchorLink` with an empty `anchor_name` links to the top of the message.

### `<figcaption>` and `<cite>`

- Inside `<figcaption>`, use `<cite>` to specify caption credit.

### `<details>` / RichBlockDetails

- The body of the block can contain rich message content.
- The `open` attribute or the `is_open: True` field shows the block expanded by default.

### InputRichMessageContent in inline, guest and Web App results

- `InputRichMessageContent` is a subtype of `InputMessageContent`.
- It is allowed in the results of **inline queries**, **guest queries** and **Web App queries**.
- It has a single field, `rich_message: InputRichMessage`, and only previously uploaded files may be used in it.
- `ChosenInlineResult.inline_message_id` isn't reliable for this content; see [Known bugs](#known-bugs).

### editMessageText

- The `text` and `rich_message` parameters are mutually exclusive: exactly one is required.
- `editMessageMedia` can "replace a text or a rich message with a media".

### sendRichMessage and allow_paid_broadcast

- With `allow_paid_broadcast: True`, up to 1000 messages per second are allowed for **0.1 Telegram Stars** per message, withdrawn from the bot's balance.

### Message.rich_message

- The field is *Optional* and is present only if the message is rich-formatted.

### Map zoom

- The outgoing `InputRichBlockMap.zoom` is optional and accepts **0–24**; the received `RichBlockMap.zoom` describes the actual scale.

### Ordered lists: numbering types

- `type` in `RichBlockListItem` and `<ol type="...">`: `"a"` (lowercase letters), `"A"` (uppercase letters), `"i"` (lowercase Roman numerals), `"I"` (uppercase Roman numerals), `"1"` (decimal numbers).
- The attributes `start` (first number), `reversed` (reverse order) and `value` (explicit value of an item) are supported.

### Client support

- The documentation names no rendering restrictions by chat type (channels, groups, private chats) except:
  - `message_effect_id`: private chats only
  - `sendMessageDraft` and `sendRichMessageDraft`: private chats only
  - `suggested_post_parameters`: direct messages chats only
  - `RichMessageButton.web_app`: private chats between a user and the bot only
- Media rights: if a rich message contains a media block, the bot must have the matching right in the chat.
