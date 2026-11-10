---
name: tg-operator-cards
description: "Use when a bot reports one event to the person who runs it — a payment, an order, an enrollment, a moderation decision — in an admin chat or a private chat with the owner. Shapes the message as a card read in two seconds on a phone: outcome and person on the first line, one fact per line, a status footer after the decision. Use tg-rich-messages for tables and long reports."
license: MIT
---

# tg-operator-cards

Input: the facts of one event. Output: a short `sendMessage` text in `parse_mode: HTML` for the operator of the bot. Three shapes share one layout: the **review card** (waits for a decision), the **receipt** (the bot already acted), and the **decision footer** (records who decided and when).

Not for messages to customers, digests of many events ([`tg-rich-digest`](../tg-rich-digest/)), tables ([`tg-rich-messages`](../tg-rich-messages/)), or rewriting agent prose ([`tg-reply-rewrite`](../tg-reply-rewrite/)). Write in the operator's language.

## Rules

1. **First line: outcome and person.** It must make sense alone in a notification preview: `✅ Enrolled: Ada (@ada)`. Bold the outcome and the name. A review card starts with the thing to decide: `🧾 Order #482`.
2. **One fact per line.** Each line starts with one emoji that names the kind of fact: 🧾 order or application, 💳 money, ✉️ delivery to the person. The same emoji means the same kind of fact in every card of the bot. No blank lines inside a card.
3. **Label first, value second.** Bold only the values the operator checks against another system: the amount, the order number. Put values the operator copies in `<code>`: product code, ticket code, ID.
4. **A problem takes the place of the normal line.** Where the card would say what went fine, put ⚠️, what failed, and the next step in one sentence. The card keeps its shape, so the warning line is the one that looks different.
5. **Say what the bot did.** `Confirmation sent`, not `sent him the confirmation`. In languages with grammatical gender this keeps the card correct for every person.
6. **Format numbers for reading.** `19 000 ₽`, not `19000`. Name the moment a date refers to: `Paid … on 08.11`, not a bare date.
7. **No filler.** No "successfully", no "please note", no closing period on a one-fact line.
8. **Escape `&`, `<`, `>` in every dynamic value.** Names come from users. One unescaped `<` and Telegram rejects the whole message with `400 can't parse entities`: the action happened, and the operator saw nothing.
9. **The decision edits the card.** When the operator presses a button, edit the same message with `editMessageText`: the same card text, a footer line, and no decision buttons. One event stays one message in the chat.

## Limits

| Part | Limit | Source |
|---|---|---|
| Card | up to 6 lines | editorial, one glance |
| Line | about 45 characters | editorial, no wrap on a phone |
| `sendMessage` text | 4 096 characters after entity parsing | Bot API |
| `callback_data` | 1–64 bytes | Bot API |

A card that needs more than six lines is a report: send it with tg-rich-messages.

## Examples (invented data)

Receipt, before:

```text
Enrolled: Ada (@ada). Application #77, Autumn cohort.
Recorded payment 19000 ₽ from 08.11.2026 — the ledger will use it.
Ledger row exists, product code cohort_autumn_early.
Sent him the confirmation in a private message.
```

Receipt, after:

```html
✅ <b>Enrolled: Ada</b> (@ada)
🧾 Application <b>#77</b> · Autumn cohort
💳 Paid <b>19 000 ₽</b> on 08.11.2026
📒 Ledger: recorded, code <code>cohort_autumn_early</code>
✉️ Confirmation sent
```

The same receipt when two steps failed (rule 4):

```html
✅ <b>Enrolled: Ada</b> (@ada)
🧾 Application <b>#77</b> · Autumn cohort
💳 Paid <b>19 000 ₽</b> on 08.11.2026
⚠️ Ledger: row not written. Run the same command again, the retry adds it.
⚠️ Message not delivered: the bot is not started or the chat is closed
```

Review card with `Confirm` and `Reject` buttons, then the footer after the decision (rule 9):

```html
🧾 <b>Order #482</b> · pinned post
👤 Ada Lovelace (@ada)
🎟 Tickets: <b>2</b>
💳 Card: <b>80 $</b>
✅ <b>CONFIRMED</b> · Grace, 14:02 · code <code>K7Q2</code>
```

Building a line (rule 8):

```python
from html import escape

head = f"✅ <b>Enrolled: {escape(first_name)}</b> (@{escape(username)})"
```
