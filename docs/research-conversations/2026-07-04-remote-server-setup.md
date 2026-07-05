# Remote server setup — operator Q&A

**Date:** 2026-07-04  
**Scope:** Remote training/server setup, dependencies, install and run how-to  
**Author:** Operator Q&A captured from Cursor chat  
**Status:** in progress

Related:

- [user-manual.md](../user-manual.md) — local run paths
- [python-runtime-environment skill](../../.cursor/skills/python-runtime-environment/SKILL.md) — conda env `auto-sat` on local machines

---

## Session log

| When (UTC) | Note |
|------------|------|
| 2026-07-04T13:00:00Z | Session opened — logging via `/log-answered-questions` |

---

## Q: Can we log this conversation and have a skill for it?

**Asked:** Log the full conversation about setting up the remote server (dependencies, how to install). Want a `/skill` usable in Ask mode that writes down all questions answered.

### Answer

Yes. Use the **user skill** **`log-answered-questions`**:

- **Location:** `~/.cursor/skills/dev-skills/log-answered-questions/` (works in any workspace).
- **Invoke:** `/log-answered-questions` in chat (or say "log this Q&A").
- **Output file (this session):** `docs/research-conversations/2026-07-04-remote-server-setup.md` (this file).
- **Ask mode:** The skill only appends markdown under `docs/research-conversations/` — no code edits. If Ask mode blocks writes, the agent emits a paste-ready markdown block; switch to Agent mode to append automatically.

**During the setup chat:** ask questions as usual; run `/log-answered-questions` whenever you want the thread flushed to disk (end of session, or after each major topic). Variants:

- `/log-answered-questions this turn` — latest exchange only
- `/log-answered-questions full` — entire thread (deduped)

**Not the same as:**

- `/document-research` — experiment reasoning + DECISIONS.md
- `/learn-skill` — agent anti-patterns → skills/rules

Subsequent Q&A about the remote server will be appended below as new `## Q:` sections.

---
