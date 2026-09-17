# telegram-skills maintainer contract

This public repository contains generic Agent Skills, Bot API reference, examples, and dependency-free helpers. Keep credentials, private identities, chat histories, runtime URLs, and consumer-specific production evidence outside it.

Verify behavior against the official Telegram Bot API. Preserve untracked and unrelated changes. Runtime helpers must be deterministic, network-free unless explicitly documented otherwise, and tested against malformed inputs and documented limits. Record consumer provenance with an upstream commit, content digest, and MIT license when vendoring.

Use Beads (`bd prime`, `bd ready`, `bd update`, `bd close`) for durable work tracking. GitHub issues may expose the public outcome. Do not create markdown task lists. Commit and push only with active authorization; package registry publication is a separate action.

Run relevant helper tests before publishing. Unknown delivery outcomes after timeouts or server errors must never be treated as proof of failure or retried blindly. Sending, editing, and live Telegram operations require the consumer's authorized target and delivery workflow.
