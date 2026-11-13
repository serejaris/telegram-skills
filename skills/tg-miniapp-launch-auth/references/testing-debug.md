# Testing and debugging a Mini App

From the [official page](https://core.telegram.org/bots/webapps#testing-mini-apps), checked on 2026-10-30 except where a line says otherwise. None of it was run on a device for this skill.

## Test environment

It is fully separate from production: create a new user account and a new bot with @BotFather there.

| Client | Login |
|---|---|
| iOS | Tap the Settings icon 10 times > Accounts > Login to another account > Test |
| Telegram Desktop | ☰ Settings > Shift + Alt + right click "Add Account" > Test Server |
| macOS | Click the Settings icon 10 times to open the Debug Menu, ⌘ + click "Add Account", log in by phone number |

- Bot API requests go to `https://api.telegram.org/bot<token>/test/METHOD_NAME`.
- HTTP links without TLS are allowed for the Mini App here.
- Validate `signature` from this environment with the test key, not the production key.
- The attachment menu can be tried here: `/setattach` in @BotFather on the test server.

## Inspectors

| Client | Steps |
|---|---|
| iOS | Tap the Settings icon 10 times, turn on Allow Web View Inspection, connect by USB, open Safari on a Mac > Develop > your device, launch the app |
| Android | Enable USB debugging. In Telegram Settings, scroll down, press and hold the version number twice, choose Enable WebView Debug. Open `chrome://inspect/#devices` in Chrome and launch the app |
| Desktop on Windows and Linux | Beta version: Settings > Advanced > Experimental settings > Enable webview inspection, then right click > Inspect. Not supported on Telegram Desktop for macOS |
| Telegram macOS | Beta version: click the Settings icon 5 times, enable "Debug Mini Apps", then right click > Inspect Element |

The tma.js docs add one iOS step that the official page lacks: turn on Web Inspector in the phone's Safari settings.

## Outside Telegram

A page opened in a plain browser has no launch parameters. A tunnel to localhost and an SDK mock are community practice, not an official path. Use them for layout only: a mock can't prove `initData` validation, safe areas or the keyboard behavior listed in [client pitfalls](../../tg-miniapp-ui/client-pitfalls.md).

A real `initData` string holds a user's name and id. Record fixtures from a test account, and keep that bot's token out of the repository.
