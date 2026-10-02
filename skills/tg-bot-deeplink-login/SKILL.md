---
name: tg-bot-deeplink-login
description: "Use when building a Telegram login flow that should open Telegram app/Desktop via a bot deep link instead of showing the web OAuth phone form. Pattern: website creates one-time key, opens a t.me bot start link, bot webhook confirms the key, website polls status and receives an app session. Examples: TGStat-style login, login through Telegram bot, avoid oauth.telegram.org phone popup."
license: MIT
---

# tg-bot-deeplink-login

Use this pattern when the desired UX is: click a website button -> Telegram app/Desktop opens -> user presses Start in the bot -> bot shows a confirmation button -> user taps it -> button disappears -> website becomes logged in.

## Reference Pattern

TGStat uses this shape on `/login`:

```html
<a href="https://t.me/tg_analytics_bot?start=<one-time-key>"
   data-telegram-auth-button="<one-time-key>"
   data-login-url="/auth"
   target="_blank">
  Sign in with Telegram
</a>
```

The important part is the `t.me/<bot>?start=<key>` deep link. It opens Telegram instead of showing the `oauth.telegram.org` phone form.

## Server Contract

Implement three endpoints:

```http
POST /api/auth/telegram-deeplink/start
```

Creates a one-time login challenge:

```json
{
  "key": "random-url-safe-token",
  "bot_username": "kruzhok_crm_bot",
  "deep_link": "https://t.me/kruzhok_crm_bot?start=random-url-safe-token",
  "expires_at": 1782216000
}
```

```http
POST /api/auth/telegram-deeplink/webhook
X-Telegram-Bot-Api-Secret-Token: <optional secret>
```

Telegram sends updates here.

On `/start <key>`:

1. read `message.from.username`;
2. normalize username without `@`;
3. check `ALLOWED_TELEGRAM_USERS`;
4. verify the challenge exists and is still pending;
5. send a bot message with one inline callback button, for example `Подтвердить вход`.

The `/start` message must not complete the session by itself.

On callback data such as `login:<key>` or `auth_<key>`:

1. read `callback_query.from.username`;
2. check `ALLOWED_TELEGRAM_USERS`;
3. mark challenge complete with app session payload;
4. call `editMessageReplyMarkup` without `reply_markup` so the inline button disappears;
5. answer the callback with a short confirmation.

```http
GET /api/auth/telegram-deeplink/status/{key}
```

Returns pending/expired/complete. On complete, returns the normal app session token:

```json
{
  "status": "complete",
  "token": "app-session-token",
  "user": {"username":"serejaris","role":"serezha","name":"Сережа"}
}
```

## Frontend Contract

One visible button:

```text
Войти через Telegram
```

On click:

1. call `/api/auth/telegram-deeplink/start`;
2. open `deep_link` in a new tab/window (`target=_blank`) so OS/browser can hand off to Telegram app;
3. poll `/status/{key}` every 1-2 seconds until `complete`, `expired`, or timeout;
4. save returned app session token and navigate into the app.

## Security Rules

- Keys must be random URL-safe tokens, single-use, and short-lived (5 minutes is enough).
- Store only the challenge key, expiry, status, and final app session payload.
- Verify the webhook secret header when `TELEGRAM_WEBHOOK_SECRET` is configured.
- Do not trust a username from the browser. The confirming username must come from Telegram webhook `message.from`.
- Keep the existing app session token format separate from the login challenge key.
- Keep classic Telegram Login Widget/OAuth as optional fallback only when product asks for it.

## Telegram Setup

Set webhook after deploy:

```bash
curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://<app-domain>/api/auth/telegram-deeplink/webhook",
    "secret_token": "'"${TELEGRAM_WEBHOOK_SECRET}"'"
  }'
```

Use `getWebhookInfo` to verify the active URL.
