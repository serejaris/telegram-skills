# telegram-skills

**Claude Code skills for Telegram Bot API 10.1 Rich Messages** — teach your AI agent to send structured documents, tables, galleries, maps, and streaming AI replies from any Telegram bot.

Bot API 10.1 (June 11, 2026) introduced [Rich Messages](https://core.telegram.org/bots/api#rich-message-formatting-options): bots can now send document-grade structured messages (section headings, tables, collapsible sections, photo collages, slideshows, maps, math) and stream AI-generated replies with a native "thinking" block — essentially Instant View articles, right in the chat.

No major bot library supports it yet. These skills work through raw HTTP calls to the Bot API — no dependencies, any stack.

## Skills

| Skill | What it does |
|---|---|
| [`tg-rich-messages`](skills/tg-rich-messages/) | Core reference: all block & inline types, JSON structure, limits and traps, raw HTTP sending |
| [`tg-markdown-to-rich`](skills/tg-markdown-to-rich/) | Convert Markdown into a rich message — write docs, send documents |
| [`tg-rich-streaming`](skills/tg-rich-streaming/) | Stream LLM output into a chat: draft animation, thinking block, mandatory finalization |
| [`tg-rich-digest`](skills/tg-rich-digest/) | Digest/report pattern: headings, lists, collapsible sections, photo collage, map embed |

## Install

Copy the skills you need into your skills directory:

```bash
# personal (all projects)
cp -r skills/* ~/.claude/skills/

# or per-project
cp -r skills/* your-project/.claude/skills/
```

Then just ask your agent — e.g. *"send this report to my Telegram channel as a rich message"*.

## Reference

- [`reference/rich-messages-spec.md`](reference/rich-messages-spec.md) — full extracted spec: every type, every field, all limits (Bot API 10.1)
- Official: [Bot API docs](https://core.telegram.org/bots/api) · [changelog](https://core.telegram.org/bots/api-changelog) · demo bot [@RichTextDemoBot](https://t.me/RichTextDemoBot)

## License

MIT
