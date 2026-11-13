# Telegram Skills for AI Agents

**Telegram skills** are [Agent Skills](https://agentskills.io) (folders with a `SKILL.md` file) that teach an AI agent how to work with Telegram. This library gives Claude Code, Codex CLI, Cursor and any other compatible agent a Telegram skill for each job: sending Rich Messages (tables, galleries, maps, collapsible sections), streaming AI replies, building interactive HTML widgets, running polls, publishing sticker packs and writing channel digests from any bot. Every skill calls the Bot API over raw HTTP, so no bot framework is required.

Guide (in Russian): [Telegram skills for Claude Code and Codex](https://sereja.tech/blog/telegram-skills-claude-code/).

## Skills

| Skill | What it does |
|---|---|
| [`tg-rich-messages`](skills/tg-rich-messages/SKILL.md) | Core reference: markup, outgoing block JSON, media bindings and uploads, preflight, limits, raw HTTP sending |
| [`tg-markdown-to-rich`](skills/tg-markdown-to-rich/SKILL.md) | Convert Markdown into a rich message and bind `file_id`, URL, or uploaded media |
| [`tg-rich-streaming`](skills/tg-rich-streaming/SKILL.md) | Stream LLM output into a chat: draft animation, thinking block, mandatory finalization |
| [`tg-polls`](skills/tg-polls/SKILL.md) | Polls and quizzes from a bot or a user account: text + poll in one message via description, media, 12 options, all poll settings and limits |
| [`tg-rich-digest`](skills/tg-rich-digest/SKILL.md) | Digest and channel-article patterns: flat layout, preview + collapsed full version, media as evidence, preflight gate |
| [`tg-reply-rewrite`](skills/tg-reply-rewrite/SKILL.md) | Rewrite a raw agent reply for a non-engineer on a phone: what happened and how urgent, what it means, a ready sentence to send back, every fact unchanged |
| [`tg-operator-cards`](skills/tg-operator-cards/SKILL.md) | Cards a bot sends to its own operator about one event (payment, order, enrollment): outcome and person on the first line, one fact per line, warning in place of the normal line, decision footer, escaped dynamic text |
| [`tg-widgets`](skills/tg-widgets/SKILL.md) | Interactive HTML message widgets (HTML bubbles, `sendWidget`): how to write them by Telegram's docs, limits, input, state, which chats accept a widget in production |
| [`tg-sticker-pack`](skills/tg-sticker-pack/SKILL.md) | Static stickers from a meme frame or video: cutout, caption on top (WordArt, Impact, tags), offline format check, publishing through @Stickers from a user account or `createNewStickerSet` from a bot |

## Install

**Universal (recommended)**

```bash
npx skills add serejaris/telegram-skills

# Install a single skill
npx skills add serejaris/telegram-skills --skill tg-rich-messages
```

**Claude Code (native marketplace)**

```bash
/plugin marketplace add serejaris/telegram-skills
/plugin install telegram-skills@telegram-skills
```

**Codex CLI**

```bash
npx skills add serejaris/telegram-skills
# or manually: cp -r skills/* ~/.agents/skills/
# Inside a clone of this repo, skills are auto-discovered via .agents/skills/
```

**Manual copy**

```bash
# Claude Code
cp -r skills/* ~/.claude/skills/

# Codex CLI / other agents
cp -r skills/* ~/.agents/skills/

# or per-project
cp -r skills/* your-project/.claude/skills/
cp -r skills/* your-project/.agents/skills/
```

Then ask your agent — e.g. *"send this report to my Telegram channel as a rich message"*.

## Bot API versions

Bot API 10.1 (June 11, 2026) introduced [Rich Messages](https://core.telegram.org/bots/api#rich-message-formatting-options): bots can send document-grade structured messages and stream AI-generated replies with a native "thinking" block. Bot API 10.2 (July 14, 2026) added outgoing block JSON plus explicit media bindings, including Telegram `file_id`, HTTP URLs, and multipart uploads.

Bot API 10.3 (August 24, 2026) adds native rich-message button rows and compact tables. Styled inline keyboard buttons use `primary`, `success`, and `danger`. The dependency-free [Python UI helper](skills/tg-rich-messages/scripts/rich_ui.py) builds validated literal block payloads and native inline buttons; it performs no network calls. See [consumer integration](skills/tg-rich-messages/consumer-integration.md).

Polls (Bot API 9.1–10.1): up to 12 options, a 1024-char description with media, so a post and its poll fit in one message. See [`tg-polls`](skills/tg-polls/SKILL.md).

## Reference

- [`reference/rich-messages-spec.md`](reference/rich-messages-spec.md) — core extracted spec, limits and Bot API 10.3 UI additions
- Official: [Bot API docs](https://core.telegram.org/bots/api) · [changelog](https://core.telegram.org/bots/api-changelog) · demo bot [@RichTextDemoBot](https://t.me/RichTextDemoBot)

## License

MIT
