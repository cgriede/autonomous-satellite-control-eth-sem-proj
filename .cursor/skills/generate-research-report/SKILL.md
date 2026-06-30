---
name: generate-research-report
description: >-
  Assembles semester research report sections from stored knowledge (DECISIONS,
  investigation notes, experiment JSON, report-direction-log, presentation) —
  no guessing. Use at project closeout, /generate-research-report, or when
  drafting Related Work / Methods / Results from repo artifacts.
disable-model-invocation: true
---

# Generate Research Report

Produce **report prose or section outlines** for [`docs/report/semester-project/`](../../../docs/report/semester-project/) by assembling **stored knowledge only**. See [`PROJECT_KNOWLEDGE.md`](../../../docs/research/PROJECT_KNOWLEDGE.md).

## When to use

- User: `/generate-research-report`, "draft report from our research docs"
- Related Work, Methods, or Results need drafting from repo artifacts
- Closeout: ensure narrative matches **decided** direction and **run** experiments

## Read first (mandatory)

| Layer | Path |
|-------|------|
| Narrative constraints | [`docs/report/semester-project/report-direction-log.md`](../../../docs/report/semester-project/report-direction-log.md) |
| Decisions & reasoning | [`docs/research/DECISIONS.md`](../../../docs/research/DECISIONS.md) |
| Investigations | `docs/research/*-investigation.md`, [LITERATURE_HIGHLIGHTS.md](../../../docs/research/LITERATURE_HIGHLIGHTS.md) |
| Literature PDFs | `docs/research/*.pdf` (cite; do not re-summarize without highlights) |
| Experiments | `results/*.json`, `*_analysis.md`, [STATUS_*.md](../../../docs/ml/experiments/) |
| Technical defs | [`docs/presentation/`](../../../docs/presentation/) |
| Code traceability | Hypothesis docs under `backend/scripts/experiments/` |

Chat is not source of truth. Missing evidence → **`[TBD — run not frozen]`** per report-direction-log.

## Output

Default: markdown draft under `docs/report/semester-project/drafts/` named `{section}_{YYYY-MM-DD}.md`, or user-specified LaTeX snippet path. **Do not overwrite `main.tex` without explicit ask.**

### Section mapping

| Report section | Primary sources |
|----------------|-----------------|
| **Abstract / problem** | report-direction-log (narrative spine, non-goals) |
| **Related Work** | LITERATURE_HIGHLIGHTS, investigation notes, local PDFs |
| **Methods — environment** | presentation environment-hyperparameters, machine-learning |
| **Methods — ML** | presentation machine-learning, investigation notes, hypothesis docs |
| **Methods — protocol** | STATUS, experiment JSON `frozen_input`, DECISIONS (dt profile, order) |
| **Results** | JSON KPIs, analysis cards, plots paths — **no numbers** if direction-log says qualitative-only |
| **Discussion** | DECISIONS rejected/deferred, investigation conclusions, limitations from direction-log |
| **Future work** | DECISIONS `deferred` rows only |

### Rules

- Honor **qualitative-only** abstract until user freezes metrics (report-direction-log)
- **Hypothesis-driven** tone; cite forks as tests, not contributions of algorithm novelty
- Every claim → source path or BibTeX key from investigation references
- **Rejected paths** belong in Discussion or Methods (what we tried and ruled out), sourced from DECISIONS
- Do not duplicate experiments not in JSON/analysis cards

## Workflow

```text
1. Read report-direction-log (tone, non-goals, audience)
2. Read DECISIONS + investigations (reasoning arc)
3. Read JSON + analysis cards (evidence)
4. Outline section-by-section with [source: path] bullets
5. Draft prose only where sources exist
6. Gaps list for user (missing runs, missing investigation)
```

## Reasoning arc (for Discussion)

Document the **journey** from stored files:

```text
Problem (direction-log) → literature (highlights) → hypotheses (hypothesis.md)
→ experiments (JSON) → decisions (DECISIONS) → open deferred items
```

## Anti-patterns

- Inventing quantitative headline results
- Claiming MPO algorithm novelty
- Ignoring rejected experiments (reader loses trust in process)
- Related Work from memory instead of local PDF index
- Omitting nb07 baseline comparison framing from direction-log

## Checklist

```text
- [ ] Tone matches report-direction-log
- [ ] Related Work cites local PDFs + investigation notes
- [ ] Results only from JSON/analysis cards; TBD where frozen
- [ ] Discussion includes decision trail (accepted/rejected/deferred)
- [ ] Gaps explicit
```

## Related

- Code README: [`generate-code-readme`](../generate-code-readme/SKILL.md)
- Maintain layers: [`document-research`](../document-research/SKILL.md)
