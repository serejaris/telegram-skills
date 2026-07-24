# Telegram Bot API 10.2 — Rich Message Formatting: Canonical Reference

**API Version:** 10.2
**Release Date:** July 14, 2026
**Source:** https://core.telegram.org/bots/api

---

## Методы

### sendRichMessage

Отправляет rich message. Если сообщение содержит блок с медиаэлементом, бот должен иметь право отправлять такой тип медиа в чат. При успехе возвращает отправленный [Message].

| Parameter | Type | Required | Description |
|---|---|---|---|
| business_connection_id | String | Optional | Unique identifier of the business connection on behalf of which the message will be sent |
| chat_id | Integer or String | **Yes** | Unique identifier for the target chat or username of the target bot, supergroup or channel in the format `@username` |
| message_thread_id | Integer | Optional | Unique identifier for the target message thread (topic) of a forum; for forum supergroups and private chats of bots with forum topic mode enabled only |
| direct_messages_topic_id | Integer | Optional | Identifier of the direct messages topic to which the message will be sent; required if the message is sent to a direct messages chat |
| rich_message | InputRichMessage | **Yes** | The message to be sent |
| disable_notification | Boolean | Optional | Sends the message silently. Users will receive a notification with no sound. |
| protect_content | Boolean | Optional | Protects the contents of the sent message from forwarding and saving |
| allow_paid_broadcast | Boolean | Optional | Pass *True* to allow up to 1000 messages per second, ignoring broadcasting limits for a fee of 0.1 Telegram Stars per message. The relevant Stars will be withdrawn from the bot's balance. |
| message_effect_id | String | Optional | Unique identifier of the message effect to be added to the message; for private chats only |
| suggested_post_parameters | SuggestedPostParameters | Optional | A JSON-serialized object containing the parameters of the suggested post to send; for direct messages chats only. If the message is sent as a reply to another suggested post, then that suggested post is automatically declined. |
| reply_parameters | ReplyParameters | Optional | Description of the message to reply to |
| reply_markup | InlineKeyboardMarkup or ReplyKeyboardMarkup or ReplyKeyboardRemove or ForceReply | Optional | Additional interface options |

---

### sendRichMessageDraft

Стримит частичное rich message пользователю в процессе генерации. **Черновик эфемерен и действует как временный 30-секундный превью** — после финализации вывода **необходимо** вызвать `sendRichMessage` с полным сообщением для его сохранения в чате. Возвращает *True* при успехе.

> **Важно:** `sendRichMessageDraft` работает только для **приватных чатов** (chat_id — Integer, не String/@username).

| Parameter | Type | Required | Description |
|---|---|---|---|
| chat_id | Integer | **Yes** | Unique identifier for the target **private chat** |
| message_thread_id | Integer | Optional | Unique identifier for the target message thread |
| draft_id | Integer | **Yes** | Unique identifier of the message draft; must be non-zero. Changes to drafts with the same identifier are animated. |
| rich_message | InputRichMessage | **Yes** | The partial message to be streamed |

---

### editMessageText (параметр rich_message)

Метод позволяет редактировать текстовые, rich и game-сообщения. При успехе возвращает отредактированный Message (или True для inline-сообщений).

Контекст: параметр `text` и `rich_message` взаимоисключающие — требуется ровно один из них.

| Parameter | Type | Required | Description |
|---|---|---|---|
| business_connection_id | String | Optional | Unique identifier of the business connection on behalf of which the message to be edited was sent |
| chat_id | Integer or String | Optional | Required if *inline_message_id* is not specified. |
| message_id | Integer | Optional | Required if *inline_message_id* is not specified. |
| inline_message_id | String | Optional | Required if *chat_id* and *message_id* are not specified. |
| text | String | Optional | New text of the message, 1-4096 characters after entity parsing; **required if *rich_message* isn't specified** |
| parse_mode | String | Optional | Mode for parsing entities in the message text |
| entities | Array of MessageEntity | Optional | Special entities; can be specified instead of *parse_mode* |
| link_preview_options | LinkPreviewOptions | Optional | Link preview generation options for the message |
| **rich_message** | **InputRichMessage** | **Optional** | **New rich content of the message; required if *text* isn't specified** |
| reply_markup | InlineKeyboardMarkup | Optional | A JSON-serialized object for an inline keyboard |

---

## Корневые типы

### RichMessage

Rich formatted message (тип для получения из Message, не для отправки).

| Field | Type | Description |
|---|---|---|
| blocks | Array of RichBlock | Content of the message |
| is_rtl | Boolean | *Optional*. *True*, if the rich message must be shown right-to-left |

**Контекст:** Поле `rich_message` класса `Message` имеет тип `RichMessage`.

---

### InputRichMessage

Описывает rich message для отправки. Ровно **одно** из полей *html*, *markdown* или *blocks* должно быть использовано.

| Field | Type | Description |
|---|---|---|
| blocks | Array of InputRichBlock | *Optional*. Content described directly as outgoing block entities |
| html | String | *Optional*. Content of the rich message described using HTML formatting |
| markdown | String | *Optional*. Content of the rich message described using Markdown formatting |
| media | Array of InputRichMessageMedia | *Optional*. Media referenced from `html` or `markdown` via `tg://photo?id=`, `tg://video?id=`, or `tg://audio?id=` |
| is_rtl | Boolean | *Optional*. Pass *True* if the rich message must be shown right-to-left |
| skip_entity_detection | Boolean | *Optional*. Pass *True* to skip automatic detection of entities (URLs, email addresses, username mentions, hashtags, cashtags, bot commands, phone numbers) |

`media` is used with `html` or `markdown`. Direct `blocks` embed `InputMedia*` objects in their
media blocks and don't need indirection through `InputRichMessage.media`.

### InputRichMessageMedia

Связывает идентификатор из markup с отправляемым медиа.

| Field | Type | Description |
|---|---|---|
| id | String | Identifier used in a `tg://photo?id=`, `tg://video?id=`, or `tg://audio?id=` link. Length 1–64; allowed characters: `A-Z`, `a-z`, `0-9`, `_`, `-` |
| media | InputMediaAnimation or InputMediaAudio or InputMediaPhoto or InputMediaVideo or InputMediaVoiceNote | Media to send. Caption and unrelated `InputMedia*` fields are ignored |

`InputMedia*.media` supports the standard Telegram file forms:

- Telegram `file_id` (recommended for an already uploaded file);
- public HTTP/HTTPS URL;
- `attach://<name>` with a matching multipart/form-data file part named `<name>`.

JSON requests can use `file_id` and HTTP/HTTPS URLs. `attach://` requires multipart/form-data;
the JSON-serialized `rich_message` is one form field and each upload is another form field.

### InputRichBlock

Bot API 10.2 added outgoing equivalents for the rich block types. Their JSON shape follows the
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
| InputRichBlockPullQuotation | `{"type":"pullquote","text":RichText,"credit"?}` |
| InputRichBlockCollage | `{"type":"collage","blocks":InputRichBlock[],"caption"?}` |
| InputRichBlockSlideshow | `{"type":"slideshow","blocks":InputRichBlock[],"caption"?}` |
| InputRichBlockTable | `{"type":"table","cells":RichBlockTableCell[][],...}` |
| InputRichBlockDetails | `{"type":"details","summary":RichText,"blocks":InputRichBlock[],"is_open"?}` |
| InputRichBlockMap | `{"type":"map","location":Location,"zoom":0..24,"width":0..10000,"height":0..10000,"caption"?}` |
| InputRichBlockAnimation | `{"type":"animation","animation":InputMediaAnimation,"caption"?}` |
| InputRichBlockAudio | `{"type":"audio","audio":InputMediaAudio,"caption"?}` |
| InputRichBlockPhoto | `{"type":"photo","photo":InputMediaPhoto,"caption"?}` |
| InputRichBlockVideo | `{"type":"video","video":InputMediaVideo,"caption"?}` |
| InputRichBlockVoiceNote | `{"type":"voice_note","voice_note":InputMediaVoiceNote,"caption"?}` |
| InputRichBlockThinking | `{"type":"thinking","text":RichText}`; draft-only |

For `InputRichBlockAnimation`, `Audio`, `Photo`, `Video`, and `VoiceNote`, the caption inside the
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

### InputRichMessageContent

Представляет содержимое rich message для отправки как результат inline-запроса. Является подтипом `InputMessageContent`.

Использование: в результатах inline-запросов, guest-запросов и Web App запросов.

| Field | Type | Description |
|---|---|---|
| rich_message | InputRichMessage | The message to be sent |

---

### RichText

Представляет rich formatted text. Может быть:
- **String** — обычный текст
- **Array of RichText** — конкатенация текстов
- **Любой из нижеперечисленных типов** (25 типов)

**Список всех подтипов:** RichTextBold, RichTextItalic, RichTextUnderline, RichTextStrikethrough, RichTextSpoiler, RichTextDateTime, RichTextTextMention, RichTextSubscript, RichTextSuperscript, RichTextMarked, RichTextCode, RichTextCustomEmoji, RichTextMathematicalExpression, RichTextUrl, RichTextEmailAddress, RichTextPhoneNumber, RichTextBankCardNumber, RichTextMention, RichTextHashtag, RichTextCashtag, RichTextBotCommand, RichTextAnchor, RichTextAnchorLink, RichTextReference, RichTextReferenceLink

---

### RichBlock

Блок в rich formatted message. Может быть любым из 21 типа:

RichBlockParagraph, RichBlockSectionHeading, RichBlockPreformatted, RichBlockFooter, RichBlockDivider, RichBlockMathematicalExpression, RichBlockAnchor, RichBlockList, RichBlockBlockQuotation, RichBlockPullQuotation, RichBlockCollage, RichBlockSlideshow, RichBlockTable, RichBlockDetails, RichBlockMap, RichBlockAnimation, RichBlockAudio, RichBlockPhoto, RichBlockVideo, RichBlockVoiceNote, RichBlockThinking

---

### RichBlockCaption

Подпись к rich-блоку (photo, video, audio, animation, map, collage, slideshow).

| Field | Type | Description |
|---|---|---|
| text | RichText | Block caption |
| credit | RichText | *Optional*. Block credit, corresponds to HTML tag `<cite>` |

---

### RichBlockTableCell

Ячейка таблицы.

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

Элемент списка.

| Field | Type | Description |
|---|---|---|
| label | String | Label of the item |
| blocks | Array of RichBlock | The content of the item |
| has_checkbox | True | *Optional*. *True*, if the item has a checkbox |
| is_checked | True | *Optional*. *True*, if the item has a checked checkbox |
| value | Integer | *Optional*. For ordered lists, the numeric value of the item label |
| type | String | *Optional*. For ordered lists, type of label: "a" (lowercase letters), "A" (uppercase letters), "i" (lowercase Roman numerals), "I" (uppercase Roman numerals), or "1" (decimal numbers) |

---

## Блоки (RichBlock*)

### RichBlockParagraph

Текстовый параграф, соответствует HTML-тегу `<p>`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"paragraph"** |
| text | RichText | Text of the block |

---

### RichBlockSectionHeading

Заголовок секции, соответствует HTML-тегам `<h1>`, `<h2>`, `<h3>`, `<h4>`, `<h5>`, или `<h6>`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"heading"** |
| text | RichText | Text of the block |
| size | Integer | Relative size of the text font; 1-6, 1 is the largest, 6 is the smallest |

---

### RichBlockPreformatted

Блок с форматированным текстом (code), соответствует HTML-тегам `<pre>` и `<code>`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"pre"** |
| text | RichText | Text of the block |
| language | String | *Optional*. The programming language of the text |

---

### RichBlockFooter

Футер, соответствует HTML-тегу `<footer>`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"footer"** |
| text | RichText | Text of the block |

---

### RichBlockDivider

Разделитель, соответствует HTML-тегу `<hr/>`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"divider"** |

---

### RichBlockMathematicalExpression

Блок с математическим выражением в формате LaTeX, соответствует кастомному HTML-тегу `<tg-math-block>`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"mathematical_expression"** |
| expression | String | The mathematical expression in LaTeX format |

---

### RichBlockAnchor

Блок с якорем, соответствует HTML-тегу `<a>` с атрибутом `name`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"anchor"** |
| name | String | The name of the anchor |

---

### RichBlockList

Список блоков, соответствует HTML-тегам `<ul>` или `<ol>` с вложенными `<li>`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"list"** |
| items | Array of RichBlockListItem | Items of the list |

---

### RichBlockBlockQuotation

Блочная цитата, соответствует HTML-тегу `<blockquote>`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"blockquote"** |
| blocks | Array of RichBlock | Content of the block |
| credit | RichText | *Optional*. Credit of the block |

---

### RichBlockPullQuotation

Выровненная по центру цитата, приблизительно соответствует HTML-тегу `<aside>`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"pullquote"** |
| text | RichText | Text of the block |
| credit | RichText | *Optional*. Credit of the block |

---

### RichBlockCollage

Коллаж, соответствует кастомному HTML-тегу `<tg-collage>`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"collage"** |
| blocks | Array of RichBlock | Elements of the collage |
| caption | RichBlockCaption | *Optional*. Caption of the block |

---

### RichBlockSlideshow

Слайдшоу, соответствует кастомному HTML-тегу `<tg-slideshow>`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"slideshow"** |
| blocks | Array of RichBlock | Elements of the slideshow |
| caption | RichBlockCaption | *Optional*. Caption of the block |

---

### RichBlockTable

Таблица, соответствует HTML-тегу `<table>`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"table"** |
| cells | Array of Array of RichBlockTableCell | Cells of the table |
| is_bordered | True | *Optional*. *True*, if the table has borders |
| is_striped | True | *Optional*. *True*, if the table is striped |
| caption | RichText | *Optional*. Caption of the table |

---

### RichBlockDetails

Раскрываемый блок (collapsible), соответствует HTML-тегу `<details>`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"details"** |
| summary | RichText | Always shown summary of the block |
| blocks | Array of RichBlock | Content of the block |
| is_open | True | *Optional*. *True*, if the content of the block is visible by default |

---

### RichBlockMap

Блок с картой, соответствует кастомному HTML-тегу `<tg-map>`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"map"** |
| location | Location | Location of the center of the map |
| zoom | Integer | Map zoom level; 13-20 |
| width | Integer | Expected width of the map |
| height | Integer | Expected height of the map |
| caption | RichBlockCaption | *Optional*. Caption of the block |

---

### RichBlockAnimation

Блок с анимацией, соответствует HTML-тегу `<video>`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"animation"** |
| animation | Animation | The animation |
| has_spoiler | True | *Optional*. *True*, if the media preview is covered by a spoiler animation |
| caption | RichBlockCaption | *Optional*. Caption of the block |

---

### RichBlockAudio

Блок с музыкальным файлом, соответствует HTML-тегу `<audio>`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"audio"** |
| audio | Audio | The audio |
| caption | RichBlockCaption | *Optional*. Caption of the block |

---

### RichBlockPhoto

Блок с фото, соответствует HTML-тегу `<img>`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"photo"** |
| photo | Array of PhotoSize | Available sizes of the photo |
| has_spoiler | True | *Optional*. *True*, if the media preview is covered by a spoiler animation |
| caption | RichBlockCaption | *Optional*. Caption of the block |

---

### RichBlockVideo

Блок с видео, соответствует HTML-тегу `<video>`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"video"** |
| video | Video | The video |
| has_spoiler | True | *Optional*. *True*, if the media preview is covered by a spoiler animation |
| caption | RichBlockCaption | *Optional*. Caption of the block |

---

### RichBlockVoiceNote

Блок с голосовым сообщением, соответствует HTML-тегу `<audio>`.

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"voice_note"** |
| voice_note | Voice | The voice note |
| caption | RichBlockCaption | *Optional*. Caption of the block |

---

### RichBlockThinking

Блок-плейсхолдер "Thinking…", соответствует кастомному HTML-тегу `<tg-thinking>`.

**Критическое ограничение:** Может использоваться **только** в `sendRichMessageDraft`. Не может быть получен в сообщениях (не хранится в Message).

| Field | Type | Description |
|---|---|---|
| type | String | Type of the block, always **"thinking"** |
| text | RichText | Text of the block. See https://t.me/addemoji/AIActions for examples of custom emoji recommended for usage in the block. |

---

## Инлайн-текст (RichText*)

### RichTextBold

Жирный текст.

| Field | Type | Description |
|---|---|---|
| type | String | always **"bold"** |
| text | RichText | The text |

---

### RichTextItalic

Курсивный текст.

| Field | Type | Description |
|---|---|---|
| type | String | always **"italic"** |
| text | RichText | The text |

---

### RichTextUnderline

Подчёркнутый текст.

| Field | Type | Description |
|---|---|---|
| type | String | always **"underline"** |
| text | RichText | The text |

---

### RichTextStrikethrough

Зачёркнутый текст.

| Field | Type | Description |
|---|---|---|
| type | String | always **"strikethrough"** |
| text | RichText | The text |

---

### RichTextSpoiler

Текст, скрытый спойлером.

| Field | Type | Description |
|---|---|---|
| type | String | always **"spoiler"** |
| text | RichText | The text |

---

### RichTextDateTime

Форматированные дата и время.

| Field | Type | Description |
|---|---|---|
| type | String | always **"date_time"** |
| text | RichText | The text |
| unix_time | Integer | The Unix time associated with the entity |
| date_time_format | String | The string that defines the formatting of the date and time. See date-time entity formatting for more details. |

---

### RichTextTextMention

Упоминание пользователя Telegram по идентификатору.

| Field | Type | Description |
|---|---|---|
| type | String | always **"text_mention"** |
| text | RichText | The text |
| user | User | The mentioned user |

---

### RichTextSubscript

Нижний индекс.

| Field | Type | Description |
|---|---|---|
| type | String | always **"subscript"** |
| text | RichText | The text |

---

### RichTextSuperscript

Верхний индекс.

| Field | Type | Description |
|---|---|---|
| type | String | always **"superscript"** |
| text | RichText | The text |

---

### RichTextMarked

Выделенный (highlight) текст.

| Field | Type | Description |
|---|---|---|
| type | String | always **"marked"** |
| text | RichText | The text |

---

### RichTextCode

Моноширинный текст (инлайн-код).

| Field | Type | Description |
|---|---|---|
| type | String | always **"code"** |
| text | RichText | The text |

---

### RichTextCustomEmoji

Кастомный эмодзи.

| Field | Type | Description |
|---|---|---|
| type | String | always **"custom_emoji"** |
| custom_emoji_id | String | Unique identifier of the custom emoji. Use getCustomEmojiStickers to get full information about the sticker. |
| alternative_text | String | Alternative emoji for the custom emoji |

---

### RichTextMathematicalExpression

Математическое выражение (инлайн).

| Field | Type | Description |
|---|---|---|
| type | String | always **"mathematical_expression"** |
| expression | String | The expression in LaTeX format |

---

### RichTextUrl

Текст со ссылкой.

| Field | Type | Description |
|---|---|---|
| type | String | always **"url"** |
| text | RichText | The text |
| url | String | URL of the link |

---

### RichTextEmailAddress

Текст с email-адресом.

| Field | Type | Description |
|---|---|---|
| type | String | always **"email_address"** |
| text | RichText | The text |
| email_address | String | The email address |

---

### RichTextPhoneNumber

Текст с номером телефона.

| Field | Type | Description |
|---|---|---|
| type | String | always **"phone_number"** |
| text | RichText | The text |
| phone_number | String | The phone number |

---

### RichTextBankCardNumber

Текст с номером банковской карты.

| Field | Type | Description |
|---|---|---|
| type | String | always **"bank_card_number"** |
| text | RichText | The text |
| bank_card_number | String | The bank card number |

---

### RichTextMention

Упоминание по username.

| Field | Type | Description |
|---|---|---|
| type | String | always **"mention"** |
| text | RichText | The text |
| username | String | The username |

---

### RichTextHashtag

Хэштег.

| Field | Type | Description |
|---|---|---|
| type | String | always **"hashtag"** |
| text | RichText | The text |
| hashtag | String | The hashtag |

---

### RichTextCashtag

Кэштег.

| Field | Type | Description |
|---|---|---|
| type | String | always **"cashtag"** |
| text | RichText | The text |
| cashtag | String | The cashtag |

---

### RichTextBotCommand

Команда бота.

| Field | Type | Description |
|---|---|---|
| type | String | always **"bot_command"** |
| text | RichText | The text |
| bot_command | String | The bot command |

---

### RichTextAnchor

Якорь (anchor point) для внутридокументной навигации.

| Field | Type | Description |
|---|---|---|
| type | String | always **"anchor"** |
| name | String | The name of the anchor |

---

### RichTextAnchorLink

Ссылка на якорь.

| Field | Type | Description |
|---|---|---|
| type | String | always **"anchor_link"** |
| text | RichText | The link text |
| anchor_name | String | The name of the anchor. If the name is empty, then the link brings back to the top of the message. |

---

### RichTextReference

Определение сноски (reference). Соответствует `<tg-reference name="...">...</tg-reference>`.

| Field | Type | Description |
|---|---|---|
| type | String | always **"reference"** |
| text | RichText | Text of the reference |
| name | String | The name of the reference |

---

### RichTextReferenceLink

Ссылка на сноску (reference link). Соответствует `<a href="#...">`.

| Field | Type | Description |
|---|---|---|
| type | String | always **"reference_link"** |
| text | RichText | The link text |
| reference_name | String | The name of the reference |

---

## Форматирование: Markdown и HTML синтаксис

### Rich Markdown style

Режим активируется передачей контента в поле `markdown` объекта `InputRichMessage`. Синтаксис:

```
**bold text**          # или __bold text__
*italic text*          # или _italic text_
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
$x^2 + y^2$           # инлайн-формула LaTeX

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

![](https://example.com/photo.jpg "Photo caption")  # с подписью

| Header 1 | Header 2 |
|:---------|:--------:|
| left     | center   |

Text with a reference[^id1].
[^id1]: Definition of the footnote.

$$E = mc^2$$           # блочная формула LaTeX
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
```

Для функций без Markdown-синтаксиса используются HTML-теги:
```html
<u>underlined</u>, <ins>underlined</ins>
<sub>subscript</sub>
<sup>superscript</sup>
<a name="chapter-1"></a>
<aside>Pull quote<cite>The Author</cite></aside>
<details open><summary>Title</summary>Content</details>
<tg-map lat="41.9" long="12.5" zoom="14"/>
```

### Rich HTML style

Режим активируется передачей контента в поле `html` объекта `InputRichMessage`.

Поддерживаемые теги:
- `<b>`, `<strong>` — bold
- `<i>`, `<em>` — italic
- `<u>`, `<ins>` — underline
- `<s>`, `<strike>`, `<del>` — strikethrough
- `<code>` — inline code (programming language не указывается для standalone code)
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
- `<img src="tg://emoji?id=..."/>` — custom emoji (альтернативный синтаксис)
- `<tg-time unix="..." format="...">text</tg-time>` — datetime
- `<tg-math>LaTeX</tg-math>` — inline formula
- `<h1>`...`<h6>` — headings
- `<p>` — paragraph
- `<pre>` — preformatted block
- `<pre><code class="language-python">...</code></pre>` — с языком
- `<footer>` — footer
- `<hr/>` — divider
- `<ul><li>...</li></ul>` — unordered list
- `<ol><li>...</li></ol>` — ordered list (атрибуты: `start`, `type`, `reversed`)
- `<ol><li value="7" type="i">...</li></ol>` — explicit item value
- `<blockquote>...<cite>The Author</cite></blockquote>` — block quotation
- `<aside>...<cite>The Author</cite></aside>` — pull quotation
- `<img src="https://..."/>` — photo block
- `<video src="https://..."></video>` — video block (или animation для .gif)
- `<audio src="https://...mp3"></audio>` — audio block
- `<audio src="https://...ogg"></audio>` — voice note block
- `<figure><img src="..." tg-spoiler/><figcaption>Caption<cite>Credit</cite></figcaption></figure>` — медиа с подписью и spoiler
- `<tg-map lat="..." long="..." zoom="..."/>` — map block
- `<tg-collage>...</tg-collage>` — collage
- `<tg-slideshow>...</tg-slideshow>` — slideshow
- `<table bordered striped><caption>...</caption><tr><th>...</th><td colspan="2" rowspan="2" align="left" valign="top">...</td></tr></table>` — table
- `<details>` / `<details open>` — collapsible block с `<summary>`
- `<tg-math-block>LaTeX</tg-math-block>` — block formula

**Поддерживаемые HTML entities:** все числовые, а также: `&lt;`, `&gt;`, `&amp;`, `&quot;`, `&apos;`, `&nbsp;`, `&hellip;`, `&mdash;`, `&ndash;`, `&lsquo;`, `&rsquo;`, `&ldquo;`, `&rdquo;`.

---

## Ограничения и заметки

### Числовые лимиты

| Ограничение | Значение |
|---|---|
| Максимум символов UTF-8 в тексте (включая alt-text emoji и формулы) | **32 768** |
| Максимум блоков (включая вложенные, list items, table rows, quotation blocks, details blocks) | **500** |
| Максимум уровней вложенности форматирования и блоков | **16** |
| Максимум медиавложений (photos, videos, audio) | **50** |
| Максимум колонок в таблице | **20** |

### Медиа

- Медиаблоки можно указывать **только как отдельные блоки** — не инлайн.
- Медиаблоки поддерживают **только HTTP и HTTPS URLs**.
- Тип медиа определяется по MIME-типу и URL.
- В Markdown-синтаксисе опциональный заголовок после URL используется как подпись.
- Photo, Video, Animation, Audio поддерживают `tg-spoiler` атрибут для скрытия превью.

### Автоматическое обнаружение сущностей

По умолчанию автоматически детектируются: plain URLs, email addresses, username mentions, hashtags, cashtags, bot commands, phone numbers, bank card numbers. Для отключения передать `skip_entity_detection: True` в `InputRichMessage`.

Telegram clients покажут алерт «Open this link?» с полным URL перед переходом по inline-ссылке.

### sendRichMessageDraft — стриминг

- Черновик **эфемерен**: 30-секундный превью, не сохраняется в чате.
- После финализации **обязательно** вызвать `sendRichMessage` с полным сообщением.
- `draft_id` должен быть ненулевым; изменения черновиков с одинаковым `draft_id` **анимированы**.
- Работает **только в приватных чатах** (chat_id — Integer, не @username).
- `RichBlockThinking` может использоваться **только** в `sendRichMessageDraft`.

### RichBlockThinking

- **Только для** `sendRichMessageDraft` — нельзя получить из Message.
- Рекомендованные кастомные эмодзи для блока: https://t.me/addemoji/AIActions

### Rich Markdown совместимость

- Rich Markdown **совместим с GitHub Flavored Markdown** там, где это возможно.
- Может содержать произвольный HTML; поддерживаемые rich message HTML-теги парсятся согласно Rich HTML style.
- Nested markdown внутри inline HTML-тегов парсится.

### Таблицы

- Ячейки таблиц могут содержать **только inline-форматирование** (не блоки).

### Формулы

- Источник формулы трактуется как **raw LaTeX**.

### Анкоры и ссылки

- Пустой `<a name="..."></a>` сам по себе создаёт якорь для навигации через `<a href="#...">`.
- `RichTextAnchorLink` с пустым `anchor_name` — ссылка на начало сообщения.

### `<figcaption>` и `<cite>`

- Внутри `<figcaption>` можно использовать `<cite>` для указания авторства (caption credit).

### `<details>` / RichBlockDetails

- Тело блока может содержать rich message content.
- Атрибут `open` / поле `is_open: True` — блок раскрыт по умолчанию.

### InputRichMessageContent в inline / guest / Web App

- `InputRichMessageContent` является подтипом `InputMessageContent`.
- Разрешён к использованию в результатах: **inline-запросов**, **guest-запросов** и **Web App запросов**.
- Содержит единственное поле `rich_message: InputRichMessage`.

### editMessageText

- Параметры `text` и `rich_message` взаимоисключающие: требуется ровно один.
- `text` required if `rich_message` isn't specified; `rich_message` required if `text` isn't specified.
- `editMessageMedia` описание явно указывает, что позволяет «replace a text or a rich message with a media».

### sendRichMessage — allow_paid_broadcast

- При `allow_paid_broadcast: True` — до 1000 сообщений в секунду, **0.1 Telegram Stars** за каждое сообщение (списываются с баланса бота).

### Поле rich_message в Message

- `Message.rich_message` имеет тип `RichMessage` (не `InputRichMessage`).
- Поле *Optional* — присутствует только если сообщение является rich-форматированным.

### Zoom карты

- `RichBlockMap.zoom` принимает значения **13–20**.

### Ordered list: типы нумерации

- `type` в `RichBlockListItem` и `<ol type="...">`: `"a"` (строчные буквы), `"A"` (заглавные буквы), `"i"` (строчные римские цифры), `"I"` (заглавные римские цифры), `"1"` (десятичные цифры).
- Поддерживаются атрибуты `start` (начальное число), `reversed` (обратный порядок), `value` (явное значение конкретного элемента).

### Клиентская поддержка

- Документация не содержит явных упоминаний об ограничениях рендеринга по типу чата (каналы/группы/личные чаты) за исключением:
  - `message_effect_id` — только для private chats
  - `sendRichMessageDraft` — только для private chats
  - `suggested_post_parameters` — только для direct messages chats
- Требование прав на отправку медиа: если rich message содержит медиаблок, бот должен иметь соответствующие права в чате.
