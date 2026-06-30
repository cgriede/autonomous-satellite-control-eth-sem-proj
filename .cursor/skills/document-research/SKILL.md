---
name: document-research
description: >-
  Captures the project thought process in durable docs: investigation notes,
  decision log entries, and index updates so agents avoid duplicate experiments
  and scope creep. Reads docs/research/PROJECT_KNOWLEDGE.md first. Use when
  documenting research, recording why we rejected or deferred a path, writing
  /document-research, or after any session that should persist beyond chat.
disable-model-invocation: true
---

# Document Research

**North star:** Store **how we reasoned**, not just conclusions — so a future agent can write the code README and research report from files alone, without guessing.

Primary home: [`docs/research/`](../../../docs/research/). Master index: [`PROJECT_KNOWLEDGE.md`](../../../docs/research/PROJECT_KNOWLEDGE.md).

## When to use

- User says "document this", "write it to docs", `/document-research`, or "capture why we decided X"
- After literature review, experiment post-mortem, or scope discussion
- When rejecting or deferring a path (**required:** append [DECISIONS.md](../../../docs/research/DECISIONS.md))
- Before end-of-project deliverables — ensure layers are complete for [`generate-code-readme`](../generate-code-readme/SKILL.md) / [`generate-research-report`](../generate-research-report/SKILL.md)

## Read first (always)

1. [`PROJECT_KNOWLEDGE.md`](../../../docs/research/PROJECT_KNOWLEDGE.md) — layer map and gates
2. [`DECISIONS.md`](../../../docs/research/DECISIONS.md) — do not contradict without new row
3. [`docs/ml/experiments/STATUS_*.md`](../../../docs/ml/experiments/) — pipeline and closeouts
4. Existing investigation notes on the same topic

## What to capture (thought process)

Each documentation pass should make these answerable **from files only**:

| Question | Where |
|----------|--------|
| What did we believe and why? | Investigation note § reasoning |
| What did papers say vs what did **our runs** show? | Investigation note § literature vs evidence |
| What did we **decide**? | [DECISIONS.md](../../../docs/research/DECISIONS.md) row |
| What did we **reject or defer**? | DECISIONS + investigation note § deferred |
| What experiments **already ran**? | Links to JSON, analysis cards, STATUS closeout |
| What's **next** and what's **out of scope**? | Investigation note + DECISIONS |

## Workflow

```text
0. If this closes a pipeline experiment: ensure `## Phase 3` (verdict) and `## Phase 4` (persistence) are appended via `/document-experiment-step` before external investigation note or production promote — see experiment-knowledge-pipeline and learnings.md `pipeline-closeout-before-promote`
1. Read PROJECT_KNOWLEDGE + DECISIONS + STATUS
2. Scope question
3. Gather (local PDFs, runs, code)
4. Draft or update investigation note
5. Append DECISIONS rows for every accept/reject/defer
6. Index (README, LITERATURE_HIGHLIGHTS, PROJECT_KNOWLEDGE table)
7. Cross-link hypothesis docs / STATUS closeout if arm finished
```

### Step 1 — Scope

| Field | Default |
|-------|---------|
| **Research question** | One sentence |
| **Filename** | `docs/research/{topic-slug}.md` or update existing |
| **Decisions to log** | List accept/reject/defer before writing prose |
| **Experiments to reference** | `results/*.json`, run dirs — no duplicate claims |

### Step 2 — Gather

Order: local PDFs + highlights → DECISIONS + STATUS → investigation notes → code/`summary_metrics.json` → web (mark external).

Use [`hypothesis-research-literature`](../hypothesis-research-literature/SKILL.md) to acquire missing PDFs.

### Step 3 — Write the note

Template: [reference.md](reference.md). **Required sections** (adapt headings):

- Reasoning chain (question → literature → hypothesis → evidence)
- **Decisions taken** (link DECISIONS IDs)
- **Rejected / deferred** (with rationale — stops scope creep)
- **Experiments already conducted** (table: slug, arm, verdict, JSON path)
- Open questions

Example: [`model-size-investigation.md`](../../../docs/research/model-size-investigation.md)

### Step 4 — Decision log

For **every** accept / reject / defer in the session, append a row to [DECISIONS.md](../../../docs/research/DECISIONS.md). Reversing an old decision = **new row** with `superseded` reference, not silent overwrite.

### Step 5 — Index

1. [`docs/research/README.md`](../../../docs/research/README.md) — investigation row
2. [`LITERATURE_HIGHLIGHTS.md`](../../../docs/research/LITERATURE_HIGHLIGHTS.md) — cheat-sheet row if experiment mapping
3. [`PROJECT_KNOWLEDGE.md`](../../../docs/research/PROJECT_KNOWLEDGE.md) — investigation table row if new note

### Step 6 — Cross-link

| Target | When |
|--------|------|
| `DECISIONS.md` | Any scope choice |
| `STATUS_*.md` closeout | Arm finished this session |
| `<hypothesis>.md` | Note motivates or closes a fork |
| `docs/presentation/*.md` | Code constants changed (presentation rule) |

## Relationship to other skills

| Skill | Role |
|-------|------|
| [`hypothesis-research-literature`](../hypothesis-research-literature/SKILL.md) | Find papers; short literature basis in hypothesis doc |
| **document-research** | Persist **full reasoning** + decisions + experiment registry links |
| [`hypothesis-experiment-cycle`](../hypothesis-experiment-cycle/SKILL.md) | Run forks; must check DECISIONS + STATUS first |
| [`experiment-knowledge-pipeline`](../experiment-knowledge-pipeline/SKILL.md) | Orchestrator: one MD per exp, stage gates, run mutex |
| [`generate-code-readme`](../generate-code-readme/SKILL.md) | End: assemble README from stored layers |
| [`generate-research-report`](../generate-research-report/SKILL.md) | End: assemble report from stored layers |

Typical sequence: experiment-knowledge-pipeline Phases 0–2 → **document-research** at Phase 3–4 (pipeline append + investigation note + DECISIONS).

## Anti-patterns

- Chat-only conclusions with no file
- New experiment proposal without reading DECISIONS + STATUS + prior JSON
- Deleting or editing old DECISION rows (append only)
- Investigation note without **rejected/deferred** section when scope was discussed
- Claiming an experiment was not run when JSON/analysis card exists
- Duplicating full experiment writeups in investigation notes (link JSON + analysis card)

## Checklist (closeout)

```text
- [ ] Read PROJECT_KNOWLEDGE + DECISIONS + STATUS before writing
- [ ] Pipeline ## Phase 3 / ## Phase 4 updated (if numbered pipeline exp)
- [ ] Investigation note updated (reasoning, evidence, experiments table, deferred)
- [ ] DECISIONS.md rows for all accept/reject/defer
- [ ] README + PROJECT_KNOWLEDGE index updated
- [ ] LITERATURE_HIGHLIGHTS row if applicable
- [ ] STATUS closeout line if arm finished
- [ ] User told paths; gaps listed explicitly
```

## Additional resources

- Note template: [reference.md](reference.md)
- Knowledge layers: [PROJECT_KNOWLEDGE.md](../../../docs/research/PROJECT_KNOWLEDGE.md)
