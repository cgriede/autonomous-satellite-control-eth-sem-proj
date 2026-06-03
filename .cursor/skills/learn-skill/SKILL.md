---
name: learn-skill
description: Captures recent breakthroughs and anti-patterns from the session, records them in .cursor/memory/learnings.md, sweeps every project skill and .cursor rule for applicability, and applies minimal updates so mistakes are not repeated. Use when the user invokes /learn-skill, says learn-skill, capture this learning, or update skills from what we learned.
disable-model-invocation: true
---

# Learn Skill

Turn **recent learnings** into durable agent instructions by updating the right skills and rules — not chat-only memory.

**Invoke:** user runs **`/learn-skill`** (see [`.cursor/commands/learn-skill.md`](../../commands/learn-skill.md)).

## What counts as a learning

| Type | Examples |
|------|----------|
| **breakthrough** | A workflow that worked; a tool path to always use; a verification gate that caught real bugs |
| **anti-pattern** | Silent wrong fallback; skipped preflight; symptom-only fix; violated repo rule discovered late |

## General rule — where to look first

| Situation | Read this |
|-----------|-----------|
| User gave **specific content** with `/learn-skill` (topic, mistake, file, workflow) | **Search the conversation** for that match; treat matching turns as the primary learning source |
| No specific topic (bare `/learn-skill`) | Read the **three latest messages** in the thread (user + assistant), newest first, for breakthroughs and anti-patterns |
| Always (after the above) | **[`.cursor/memory/learnings.md`](../../memory/learnings.md)** — rows with `Status: pending` or missing `Applied to` |
| Optional | Latest dated block in [`backlog.md`](../../../backlog.md) session notes (not the sprint board) |

If nothing concrete is found after these steps, ask: *What should we never do again, or always do?*

## Workflow (follow in order)

### 0. Repo check (when user asks to "add" a skill)

Glob `.cursor/skills/**/SKILL.md` and `.cursor/commands/`. If a match exists, **refine** it; do not create a parallel skill unless the user wants a split.

### 1. Collect learnings

Apply the [general rule](#general-rule--where-to-look-first), then merge with pending rows in `learnings.md`.

Extract **one imperative sentence per learning** (do this / never do this). Prefer the **current session**; older `applied` rows are context only unless the user asks to re-audit.

### 2. Record (append before sweeping)

For each **new** learning, append to `learnings.md` (format in that file):

- Unique `short-id` (kebab-case)
- **Type**, **Learning**, **Evidence**, **Applied to:** `pending`, **Status:** `pending`

Do not duplicate an existing `short-id`.

### 3. Inventory skill and rule surfaces

Scan and build a checklist (read paths; do not rely on memory):

| Surface | Glob |
|---------|------|
| Project skills | `.cursor/skills/**/SKILL.md` |
| Rules | `.cursor/rules/*.mdc` |

Use [reference.md](reference.md) for the skill list and applicability rubric.

### 4. Applicability sweep (mandatory)

For **each** learning (new or still `pending`), evaluate **every** skill and **every** rule:

| Verdict | Meaning |
|---------|---------|
| **UPDATE** | Add a bullet, preflight step, or forbidden pattern |
| **POINTER** | Already correct; one-line cross-link to canonical skill or `learnings.md` |
| **N/A** | Out of scope — state why in one phrase |

**Do not skip skills** because the learning "feels unrelated."

Priority when multiple surfaces match:

1. Always-applied **rules**
2. Skills whose **description** matches the learning domain
3. **POINTER** elsewhere — one canonical home, no paragraph duplication

### 5. Apply updates (minimal diffs)

- Short bullets or preflight steps; match repo tone (imperative; PowerShell `;` not `&&`).
- **Forbidden:** long duplicate paragraphs across skills.
- After edits, set **Applied to** and **Status:** `applied` on each learning row.

### 6. Report to the user

```markdown
## Learn-skill summary

### Context used
- three latest messages | search match: "<topic>" | pending learnings.md | …

### Learnings captured
- [short-id] (type) — one-line learning

### Sweep
| Surface | Verdict | Change |
|---------|---------|--------|
| pm-briefing | UPDATE | … |
| debug-workflow | N/A | … |

### Files touched
- paths

### Still pending
- none | short-ids
```

### 7. Optional follow-ups

| Situation | Next step |
|-----------|-----------|
| New skill to own the learning | [new-skill-integration](../new-skill-integration/SKILL.md) |
| Numeric / env constants | `docs/presentation/` per math-physics rule |
| Backlog / process only | [pm-backlog-review](../pm-backlog-review/SKILL.md) + `backlog.xlsx` row if needed |

## Rules

- **Do not** only update `backlog.md` or chat — `learnings.md` + skills/rules are the durable output.
- **Do not** mark `applied` without reading every `.cursor/skills/**/SKILL.md`.
- **Do not** commit unless the user asked.
- **Do not** treat pytest green or agent-regenerated artefacts as user approval to ship — see learnings.md `human-confirm-before-review-ship` and [minimal-feature-review](../minimal-feature-review/SKILL.md) Phase 5.
- If a learning contradicts a skill bullet, **fix the skill** and note the conflict in the summary.

## Related skills

- [new-skill-integration](../new-skill-integration/SKILL.md)
- [pm-backlog-review](../pm-backlog-review/SKILL.md)
