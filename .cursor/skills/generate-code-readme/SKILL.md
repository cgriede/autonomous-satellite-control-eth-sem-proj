---
name: generate-code-readme
description: >-
  Assembles or updates project/subsystem README from stored knowledge layers
  (presentation docs, ml docs, experiment JSON, DECISIONS) — no guessing.
  Use at project closeout, when the user says /generate-code-readme, or when
  onboarding docs must reflect decided architecture and experiment outcomes.
disable-model-invocation: true
---

# Generate Code README

Produce a **code-oriented README** (repo root, `backend/`, or subsystem) by **reading stored layers only**. See [`PROJECT_KNOWLEDGE.md`](../../../docs/research/PROJECT_KNOWLEDGE.md).

## When to use

- User: `/generate-code-readme`, "write the project README from our docs"
- Closeout after experiments frozen
- Onboarding doc must match **decided** behavior, not aspirational design

## Read first (mandatory — no skipping)

| Layer | Path |
|-------|------|
| Index | [`docs/research/PROJECT_KNOWLEDGE.md`](../../../docs/research/PROJECT_KNOWLEDGE.md) |
| Decisions | [`docs/research/DECISIONS.md`](../../../docs/research/DECISIONS.md) |
| ML / implementation | [`docs/ml/`](../../../docs/ml/), [`docs/presentation/`](../../../docs/presentation/) |
| Experiment results | `backend/scripts/experiments/*/results/*.json`, `*_analysis.md` |
| Status | [`docs/ml/experiments/STATUS_*.md`](../../../docs/ml/experiments/) |
| User manual (if exists) | [`docs/user-manual.md`](../../../docs/user-manual.md) |

If a section lacks source material, write **`TBD — no stored decision`**; do not infer from code comments alone without cross-check.

## Output

Default target: **`README.md`** at scope user specifies (repo root or `backend/README.md`). Ask if unclear.

### Required sections

1. **Purpose** — from report-direction-log + presentation (one paragraph)
2. **Architecture** — canonical paths (`simulation/run_simulation`, `episode_runner`, render view-only) citing presentation/code
3. **Environment** — conda `auto-sat` / ASC per python-runtime-environment skill
4. **Train / eval entry points** — scripts with flags; cite user-manual or presentation
5. **Observation & action** — dims, encoder summary; cite `docs/presentation/machine-learning.md`
6. **Experiment history (summary)** — table from JSON verdicts + STATUS; link `docs/research/`
7. **Out of scope / rejected** — bullet list from DECISIONS `rejected`/`deferred`
8. **References** — file paths only

### Rules

- Every factual claim → `(source: path)` or markdown link
- Verdicts only from `results/*.json` `verdict` field or analysis cards
- Do not list experiments as "planned" if STATUS says DONE or DECISIONS says rejected
- Do not duplicate full investigation notes — link `docs/research/*.md`

## Workflow

```text
1. Read PROJECT_KNOWLEDGE + DECISIONS + STATUS
2. Collect JSON verdicts (glob results/*.json)
3. Read presentation + ml docs for constants and commands
4. Draft README sections per template above
5. List gaps: missing layers needed for complete README
6. User review before overwrite of existing README (ask if large diff)
```

## Anti-patterns

- Guessing hyperparameters not in presentation/ml docs
- Omitting rejected paths (reader will repeat scope creep)
- Copying chat transcript
- Claiming "SOTA" or performance numbers not in JSON/analysis cards

## Checklist

```text
- [ ] All sections cite a stored file
- [ ] Experiment table matches JSON + STATUS
- [ ] Rejected/deferred from DECISIONS included
- [ ] Gaps section for missing sources
```

## Related

- Narrative report: [`generate-research-report`](../generate-research-report/SKILL.md)
- Maintain layers: [`document-research`](../document-research/SKILL.md)
