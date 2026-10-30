# Client pitfalls in Telegram Mini Apps

Practitioner reports from public trackers, not documented behavior. None was reproduced for this file. Status was read from the tracker on 2026-10-30; recheck the link on your client version before you build a workaround. The iOS tracker accepts reports without moderation.

## iOS

| Client | Symptom | What to do | Issue | Filed | Status |
|---|---|---|---|---|---|
| Telegram iOS 12.9 (34442), iOS 26.5.1, iPhone 17 Pro Max | App collapses to 1 px after the keyboard opens: `innerHeight` and `visualViewport.height` become 1, taps stop reaching the page. `viewportStableHeight = 1` comes first. Sporadic. | Test the keyboard on a real iPhone; watch `viewportStableHeight` for a value near 1 and log it | [Telegram-iOS#2235](https://github.com/TelegramMessenger/Telegram-iOS/issues/2235) | 2026-07-16 | open |
| Telegram iOS 12.9.x, `WebApp.version` 9.6 | `requestFullscreen()` is ignored: no `fullscreenChanged`, no `fullscreenFailed`, though `isVersionAtLeast('8.0')` is true | Check `isFullscreen` on a timer; keep a layout without fullscreen | [Telegram-iOS#2241](https://github.com/TelegramMessenger/Telegram-iOS/issues/2241) | 2026-07-20 | open |
| Telegram iOS 12.5.2, iOS 18.3.1 | In fullscreen, `history.back()` leaves the top of the page unpainted until scroll | Check back navigation on a device | [Telegram-iOS#2061](https://github.com/TelegramMessenger/Telegram-iOS/issues/2061) | 2026-03-20 | open |
| Telegram iOS, App Store build of October 2026 | A `t.me/<user>?text=` link loses its text if the app wasn't opened from a chat. Android fills it in every case | Don't rely on prefilled text on iOS | [Telegram-iOS#2354](https://github.com/TelegramMessenger/Telegram-iOS/issues/2354) | 2026-10-02 | open |
| Telegram iOS 13.0 (35303), iOS 16.7.16, iPhone 8 Plus | `shareMessage` sheet doesn't scroll with a tall preview; "Choose recipients" stays below the visible area | Keep the prepared message short | [Telegram-iOS#2375](https://github.com/TelegramMessenger/Telegram-iOS/issues/2375) | 2026-10-14 | open |
| Telegram iOS, dark theme | `setHeaderColor('#hex')` or a BotFather header color gives close and menu buttons light glass even on a dark color; `setHeaderColor('bg_color')` gives dark glass | Use `bg_color` for a dark header | [Telegram-iOS#2420](https://github.com/TelegramMessenger/Telegram-iOS/issues/2420) | 2026-10-30 | open |
| Telegram iOS | Add to Home Screen passes no sign of the launch from the icon: `start_param` stays clean. A Telegram engineer called it intentional | Don't detect the home screen launch through `start_param` | [Telegram-iOS#1979](https://github.com/TelegramMessenger/Telegram-iOS/issues/1979) | 2026-01-11 | closed 2026-03-06, by design |

## Android

| Client | Symptom | What to do | Issue | Filed | Status |
|---|---|---|---|---|---|
| Telegram for Android | No camera in the app: `getUserMedia` doesn't help, and a file input offers only picked photos. Works on iOS. Users confirmed it up to 2026-06-30 | Offer a photo upload path | [tma.js#681](https://github.com/Telegram-Mini-Apps/tma.js/issues/681) | 2025-03-12 | closed 2026-09-10 as outside the package, no client fix found |
| Telegram for Android | Native fullscreen for HTML5 video and iframe players is disabled | Design the player to work inline | [tma.js#865](https://github.com/Telegram-Mini-Apps/tma.js/issues/865) | 2026-03-29 | closed 2026-09-10 as outside the package, no client fix found |

## Desktop

| Client | Symptom | What to do | Issue | Filed | Status |
|---|---|---|---|---|---|
| Telegram Desktop, Windows 11, `WebApp.version` 9.6 | A second `requestWriteAccess()` in a session, or after a reload, never calls the callback | Store the first result and don't ask twice | [tdesktop#30729](https://github.com/telegramdesktop/tdesktop/issues/30729) | 2026-05-25 | open |
| Telegram Desktop 6.9.3, Ubuntu 24.04 | Cookie from the first HTML response isn't sent on later same-origin requests | Send auth in a header; check your Desktop version | [tdesktop#30889](https://github.com/telegramdesktop/tdesktop/issues/30889) | 2026-06-27 | closed 2026-07-31 |
| Telegram Desktop beta, Fedora Linux 44 | `localStorage` is empty when the app is reopened | Keep state on the server; check your Desktop version | [tdesktop#31051](https://github.com/telegramdesktop/tdesktop/issues/31051) | 2026-07-24 | closed 2026-07-29, possible duplicate of #30889 |

## All platforms

| Client | Symptom | What to do | Issue | Filed | Status |
|---|---|---|---|---|---|
| Any, during the `t.me` outage of 2026-07-13 and 14 | `createInvoiceLink` returned a `telegram.me` link that didn't open in the client; tma.js `openTelegramLink` rejected `telegram.me` and `telegram.dog` | Don't hardcode the invoice host. A fallback domain works for posts; test it before using it for invoices and links from the app | [python-telegram-bot#5296](https://github.com/python-telegram-bot/python-telegram-bot/issues/5296), [tma.js#879](https://github.com/Telegram-Mini-Apps/tma.js/issues/879) | 2026-07-14 | both closed 2026-07-14 |

## Older reports, recheck first

Filed before October 2025. Check on a current client before you rely on them.

| Client | Symptom | Issue | Filed | Status |
|---|---|---|---|---|
| Telegram iOS 11.11 and later at the time | The viewport shrinks with the keyboard, as on Android; fields in scrollable containers move and the caret drifts | [tma.js#732](https://github.com/Telegram-Mini-Apps/tma.js/issues/732) | 2025-05-11 | closed 2025-06-24 |
| Telegram iOS | An input in a `sticky` or `absolute` container leaves empty space above the keyboard | [tma.js#737](https://github.com/Telegram-Mini-Apps/tma.js/issues/737) | 2025-05-29 | closed 2025-06-07 |
| Telegram iOS in-app browser | `isTMA()` from tma.js returns true on a plain page opened from a chat link | [tma.js#747](https://github.com/Telegram-Mini-Apps/tma.js/issues/747) | 2025-06-20 | closed 2026-06-09 |
