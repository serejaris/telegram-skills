# Deterministic Python bot UI

`rich_ui.py` is a pure Python, MIT-licensed helper. It is not a bot framework and makes no HTTP requests. Python 3.9+; no third-party dependency. It supports **literal-string RichText** and a narrow outgoing block subset: `heading`, `paragraph`, `pre`, `table`, `details`, `photo`.

```python
from rich_ui import build_blocks_message, styled_button

rich_message = build_blocks_message([
    {'type': 'heading', 'size': 2, 'text': 'Result'},
    {'type': 'table', 'is_compact': True, 'cells': [
        [{'text': 'Option', 'align': 'left', 'valign': 'top', 'is_header': True},
         {'text': 'Probability', 'align': 'right', 'valign': 'top', 'is_header': True}],
        [{'text': 'A < B & C', 'align': 'left', 'valign': 'top'},
         {'text': '72%', 'align': 'right', 'valign': 'top'}],
    ]},
    {'type': 'details', 'summary': 'API details', 'blocks': [
        {'type': 'pre', 'text': '{"probability":0.72}', 'language': 'json'},
    ]},
])
markup = {'inline_keyboard': [[
    styled_button('New question', callback_data='new', style='primary'),
    styled_button('Back', callback_data='back'),
]]}
# Pass these objects to your existing authorized HTTP transport:
# sendRichMessage(chat_id=..., rich_message=rich_message, reply_markup=markup)
```

## Screen hierarchy and restrained color

Start with a short heading, a plain explanation of what the bot does and why it helps, and a clear next action. Brevity should preserve the information a newcomer needs to understand the product. Keep provider configuration and technical details in contextual About/help views; put quotas, reset times and rate limits in a dedicated limits view or a relevant status.

- Give each screen at most one `primary` CTA. A screen with equally important choices can use neutral buttons throughout.
- Leave secondary navigation, Back, ordinary Cancel, About, limits and copy actions neutral by omitting `style`.
- Use `success` only for confirmed success or an explicit desirable commit. A bonus offer, an eligibility check or an unverified result does not establish success.
- Use `danger` only for a genuinely destructive action, such as deleting saved data; an ordinary wizard exit is neutral. Describe the consequence and require the appropriate confirmation for the product.
- Do not apply a color to every button. Color is a semantic cue, supported by concise labels and screen context. Check the actual mobile outcome and adjust hierarchy when user feedback shows visual overload.

The helper continues to support every documented style; these rules guide product composition and do not alter wire semantics.

## Onboarding for decision and inference bots

Explain the application in familiar terms before naming model primitives: an app receives text, asks a question with criteria, and uses the returned decision for its next step. Show **input → criteria → result** with one concrete example. Clarify what the surrounding code does and what the bot merely evaluates; a decision preview does not execute a command or control a browser.

Offer a free catalogue and free case preview before paid or quota-consuming inference. A preview shows why the task matters, the exact input and the criteria. Give it one explicit primary action such as “Run example · 1 request”; opening a card, reading its source, returning to a cached result and viewing API details should not silently repeat inference. A clear action label can express the quota boundary without a repeated paragraph about free viewing. Use contextual actions such as “Check my command” or “Evaluate my task” and explain exactly what the user should send next. Apply request limits to actual inference separately from navigation.

Use plausible tasks from the audience's work. Present each criterion as a separate named option with a short explanation. Keep model instructions, injection defenses and serialization details out of this human explanation. Natural-language input belongs in ordinary readable text; use `pre` for actual code and JSON.

For mechanisms that need a diagram, show input, evaluation, decision and the application's next action distinctly. Use few nodes, large labels and restrained color; static illustrations must not pretend to show a measured live answer. Check legibility at the actual chat width. Keep accessible vector sources and export an image for native `photo` blocks.

Use source-backed case cards and label provenance accurately: our observed experiment, an external project, or a synthetic teaching adaptation. An external repository proves its published implementation, not your deployment or a universal reliability claim. Identify adapted prompts as adaptations; do not imply they are the author's original inputs. Keep the source link available. Put longer attribution and scope notes in a closed `details` block such as “About this example”, so the initial screen prioritizes purpose, input, criteria and next action. Keep any necessary immediate limitation visible.

After inference, explain how the decision could be used, show actual returned values, and distinguish probabilities and model confidence from verified facts. Do not manufacture missing probabilities or substitute recorded demo numbers for a live result. Keep raw JSON accessible in a native `pre` block with `language: "json"`. Review onboarding against observed product outcomes and adjust explanation as well as visual hierarchy.

## Helper contract

- `build_blocks_message(blocks, *, skip_entity_detection=True) -> dict`: detached `InputRichMessage`; `ValueError` for malformed or unsupported data. It has exactly one content field, `blocks`. Literal strings remain unchanged, including `<`, `&`, Unicode and JSON. Do not HTML-escape them.
- `styled_button(text, *, callback_data=None, url=None, copy_text=None, style=None) -> dict`: native `InlineKeyboardButton`; exactly one supported action. `copy_text` is a string and becomes `{'text': ...}`. Callbacks must be 1–64 UTF-8 **bytes**. Copy text is 1–256 characters. URLs use HTTP, HTTPS or `tg`.
- Styles: omitted, `danger`, `success`, `primary`. The separate `RichMessageButton` type allows `link` for callbacks; this helper intentionally builds inline keyboard buttons.
- Optional True-only fields must be `True` or omitted. All table cells require `align` and `valign`; explicit empty text is allowed. Invisible cells can omit `text`.
- Preflight: 32768 Unicode code points in supported text fields; 500 blocks including table rows; 16 block nesting levels; at most 20 table columns. Telegram documents “UTF-8 characters”; this helper does **not** claim the text limit is UTF-8 bytes or fully emulate server parsing. Table spans also remain subject to server layout validation.
- Photos use `{'type':'photo','photo':{'type':'photo','media':'attach://diagram'},'caption':{'text':'Short explanation'}}`. A caption is optional and supports a literal `text` field. The media reference supports a file ID, HTTP/HTTPS URL or `attach://name`; attachment names and file IDs in this subset contain only ASCII letters, digits, hyphens and underscores. The helper counts at most 50 photo blocks, including nested blocks, and captions count toward the text limit. It does not read files or verify file existence, image dimensions or upload bindings.
- Other media, caption credit/entity trees, photo modifiers, inline rich buttons, dates, quotations and other blocks are outside this helper. Use the official schema/reference directly when they are needed; never bypass the validator by assuming an unsupported payload is validated.

## Send, edit and callback lifecycle

Create with `sendRichMessage`. Store the acknowledged Bot API `message_id` privately. Update with `editMessageText(chat_id=..., message_id=..., rich_message=..., reply_markup=...)`; exactly one of `text` and `rich_message` is used. There is no `editRichMessage` method.

Acknowledge callbacks separately. Verify caller ownership, screen message ID and state before editing; old buttons must not apply the latest cached answer to an unrelated screen. Navigation can use cached content without repeating expensive work. A generation request and a navigation action need separate application rate/quota rules.

A timeout, 429 or 5xx can leave delivery unknown. Do not assume nothing was sent, duplicate blindly, or fall back by sending another message. An HTML fallback can be an explicit product path after a definite unsupported-method/payload rejection; preserve complete JSON and escape dynamic HTML text. A validation error is local and has no delivery side effect.

For a local diagram, use multipart/form-data in the same authorized send or edit call: JSON-serialize `rich_message` and `reply_markup` into form fields, include the target fields, and attach the PNG under exactly the name after `attach://`. Bind only packaged/allowlisted files. An ordinary chat message can be edited with new files; inline messages have stricter upload restrictions. Do not create a separate visible upload message just to obtain a file ID.

## Pin and update

Vendor the exact helper plus repository MIT license, or load it from a pinned checkout. Record repository URL, full upstream commit, source path and SHA-256 digest. Avoid tracking `main` dynamically in a production image. On updates, compare upstream source, refresh digest and run helper plus consumer transport/presentation tests. No package registry release is required.

```bash
python3 -m unittest discover -s skills/tg-rich-messages/tests -v
python3 -m unittest discover -s skills/tg-markdown-to-rich/tests -v
```

Primary contracts: [InputRichMessage](https://core.telegram.org/bots/api#inputrichmessage), [sendRichMessage](https://core.telegram.org/bots/api#sendrichmessage), [editMessageText](https://core.telegram.org/bots/api#editmessagetext), [styled inline buttons](https://core.telegram.org/bots/api#inlinekeyboardbutton), [compact tables](https://core.telegram.org/bots/api#inputrichblocktable), [JSON preformatted blocks](https://core.telegram.org/bots/api#inputrichblockpreformatted), [photo blocks](https://core.telegram.org/bots/api#inputrichblockphoto).
