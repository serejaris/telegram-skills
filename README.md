# telegram-skills

**Agent Skills for Telegram Bot API 10.2 Rich Messages** — works with Claude Code, Codex CLI, Cursor, and any agent supporting the [Agent Skills standard (agentskills.io)](https://agentskills.io). Teach your AI agent to send structured documents, tables, galleries, maps, uploaded media, and streaming AI replies from any Telegram bot.

Bot API 10.1 (June 11, 2026) introduced [Rich Messages](https://core.telegram.org/bots/api#rich-message-formatting-options): bots can send document-grade structured messages and stream AI-generated replies with a native "thinking" block. Bot API 10.2 (July 14, 2026) added outgoing block JSON plus explicit media bindings, including Telegram `file_id`, HTTP URLs, and multipart uploads.

No major bot library supports it yet. These skills work through raw HTTP calls to the Bot API — no dependencies, any stack.

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

## Skills

| Skill | What it does |
|---|---|
| [`tg-rich-messages`](skills/tg-rich-messages/) | Core reference: markup, outgoing block JSON, media bindings, limits and raw HTTP sending |
| [`tg-markdown-to-rich`](skills/tg-markdown-to-rich/) | Convert Markdown into a rich message and bind `file_id` or URL media |
| [`tg-rich-streaming`](skills/tg-rich-streaming/) | Stream LLM output into a chat: draft animation, thinking block, mandatory finalization |
| [`tg-rich-digest`](skills/tg-rich-digest/) | Digest/report pattern: headings, lists, collapsible sections, photo collage, map embed |

## Reference

- [`reference/rich-messages-spec.md`](reference/rich-messages-spec.md) — full extracted spec: every type, every field, all limits (Bot API 10.2)
- Official: [Bot API docs](https://core.telegram.org/bots/api) · [changelog](https://core.telegram.org/bots/api-changelog) · demo bot [@RichTextDemoBot](https://t.me/RichTextDemoBot)

## License

MIT
