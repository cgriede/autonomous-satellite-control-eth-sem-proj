# Agent learnings log

Durable record of **breakthroughs** (do this) and **anti-patterns** (never do this).  
Invoke **`/learn-skill`** (see [`.cursor/commands/learn-skill.md`](../commands/learn-skill.md)) to sweep skills/rules after adding entries here.

## Entry format

```markdown
### YYYY-MM-DD — short-id

- **Type:** breakthrough | anti-pattern
- **Learning:** One imperative sentence.
- **Evidence:** What happened (session, bug, review) — optional but recommended.
- **Applied to:** comma-separated skill/rule names, or `pending`
- **Status:** pending | applied | superseded
```

---

### 2026-06-03 — backlog-xlsx-preflight

- **Type:** anti-pattern
- **Learning:** When backlog or sprint status is requested, preflight `backlog.xlsx` via `backlog_xlsx.py check`; if the workbook is missing, ask the user where it lives — never silently use `backlog.md` as the live board.
- **Evidence:** Session review updated only `backlog.md` until user pointed out missing xlsx workflow.
- **Applied to:** pm-briefing, pm-backlog-review, minimal-feature-cycle, learn-skill (POINTER), bulk-change-triage-commit (N/A), minimal-feature-review (POINTER), new-skill-integration (N/A), all other skills (N/A), all rules (N/A)
- **Status:** applied

---

### 2026-06-03 — check-existing-before-create-skill

- **Type:** anti-pattern
- **Learning:** Before creating a new skill or slash command, glob `.cursor/skills/**/SKILL.md` and `.cursor/commands/` — extend the existing artifact instead of duplicating.
- **Evidence:** User asked to add learn-skill; workflow already existed under `.cursor/skills/learn-skill/` and needed refinement only.
- **Applied to:** learn-skill, new-skill-integration
- **Status:** applied

---

### 2026-06-03 — human-confirm-before-review-ship

- **Type:** anti-pattern
- **Learning:** After a review fix, never commit or treat the slice as shipped until the user explicitly confirms human verification passed — passing pytest or agent-run notebook output is not sufficient.
- **Evidence:** Safe-mode movement-constraints review: agent attempted a production commit immediately after tests passed; user rejected because they had not re-verified notebook/MP4 behavior.
- **Applied to:** minimal-feature-review, minimal-feature-cycle (POINTER), bulk-change-triage-commit (POINTER), visual-output-verification (POINTER), learn-skill (POINTER), all other skills (N/A), all rules (N/A)
- **Status:** applied
