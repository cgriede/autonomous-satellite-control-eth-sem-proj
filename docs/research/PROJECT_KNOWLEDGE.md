# Project knowledge index

**Purpose:** Single entry point for agents. The semester report and code README must be **assembled from these artifacts**, not inferred from chat or guessed from code alone.

**Skills:** [experiment-knowledge-pipeline](../../.cursor/skills/experiment-knowledge-pipeline/SKILL.md) · [document-research](../../.cursor/skills/document-research/SKILL.md) · [hypothesis-research-literature](../../.cursor/skills/hypothesis-research-literature/SKILL.md) · [hypothesis-experiment-cycle](../../.cursor/skills/hypothesis-experiment-cycle/SKILL.md) · [generate-code-readme](../../.cursor/skills/generate-code-readme/SKILL.md) · [generate-research-report](../../.cursor/skills/generate-research-report/SKILL.md)

---

## Why this exists

| Risk | How stored knowledge helps |
|------|----------------------------|
| **Duplicate experiments** | Status board + JSON verdicts + decision log show what already ran |
| **Scope creep** | [DECISIONS.md](DECISIONS.md) records paths **rejected or deferred** with rationale |
| **Opaque reasoning** | Investigation notes capture literature → hypothesis → evidence → next step |
| **Report/README guesswork** | Deliverable skills read only the layers below |

---

## Knowledge layers (read in this order for new work)

| Layer | Location | What it stores |
|-------|----------|----------------|
| **0 — Index** | This file | Map of all layers; end-of-project commands |
| **1 — Decisions** | [DECISIONS.md](DECISIONS.md) | Accepted / rejected / deferred choices and why |
| **2 — Literature** | [README.md](README.md), PDFs, [LITERATURE_HIGHLIGHTS.md](LITERATURE_HIGHLIGHTS.md) | External claims, section pointers |
| **3 — Investigations** | `docs/research/*-investigation.md`, topic notes | Synthesis, diagnostics, experiment order |
| **4 — Experiment pipeline** | [docs/experiments/pipeline/](../experiments/pipeline/) · [STATUS_*.md](../ml/experiments/STATUS_2026-06.md) | One MD per exp (charter→closeout); orchestrator skill; global run mutex |
| **5 — Experiment artifacts** | `backend/scripts/experiments/<slug>/results/*.json`, `*_analysis.md` | Verdicts, KPIs, parity, debug |
| **6 — Hypothesis docs** | `backend/scripts/experiments/<slug>/<hypothesis>.md` | Frozen question, literature basis, KPI |
| **7 — Code / ML record** | [docs/presentation/](../presentation/), [docs/ml/](../ml/) | Constants, reward defs, implementation checklist |
| **8 — Report narrative** | [docs/report/semester-project/report-direction-log.md](../report/semester-project/report-direction-log.md) | Audience, tone, non-goals, framing (not results numbers) |

Chat and agent transcripts are **not** source of truth. If it is not in a layer above, it was not decided.

---

## Gates (before new research or experiments)

1. Read **DECISIONS.md** — do not re-open rejected paths unless the user explicitly reverses a decision (then append a new row).
2. Read **STATUS** board — do not duplicate arms with verdict `supported` / `falsified` / `inconclusive` unless the hypothesis doc states a **new** frozen input.
3. Grep `results/*.json` and `*_analysis.md` for the same `experiment_id` or KPI.
4. Read relevant **investigation notes** for the topic (e.g. [model-size-investigation.md](model-size-investigation.md)).
5. Only then: literature search or fork.

---

## What to write when (thought-process capture)

| Event | Write to |
|-------|----------|
| Literature review spanning a topic | Investigation note + README index (`document-research`) |
| “We will / won't do X” | [DECISIONS.md](DECISIONS.md) |
| Paper acquired or highlighted | PDF + `LITERATURE_HIGHLIGHTS.md` |
| Hypothesis fork planned | `<slug>/<hypothesis>.md` literature basis |
| Arm finished | JSON + analysis card + STATUS closeout line |
| Investigation conclusion changes plan | Update investigation note **and** DECISIONS if scope changed |

Every investigation note should include: **reasoning chain**, **decisions taken**, **experiments already run** (links), **deferred/rejected**, **open questions**.

---

## End of project — two agent commands

When implementation and experiments are frozen:

| Command | Skill | Output |
|---------|-------|--------|
| **`/generate-code-readme`** | [generate-code-readme](../../.cursor/skills/generate-code-readme/SKILL.md) | Repo / subsystem README from layers 5–7 |
| **`/generate-research-report`** | [generate-research-report](../../.cursor/skills/generate-research-report/SKILL.md) | Report sections / outline from layers 1–8 |

Both skills **must cite file paths** for every claim. Missing layer → state gap explicitly; do not invent.

---

## Investigation notes (index)

| Note | Topic |
|------|--------|
| [model-size-investigation.md](model-size-investigation.md) | MPO network sizing, input dim, capacity diagnostics |
| [shutter-threshold-investigation.md](shutter-threshold-investigation.md) | Exp 1 reasoning; verdict table in [pipeline/4-documentation/01-shutter-threshold.md](../experiments/pipeline/4-documentation/01-shutter-threshold.md) |
| [mpo-learning-collapse-investigation.md](mpo-learning-collapse-investigation.md) | Why MPO never learns; "KL explosion" = symptom of unconstrained M-step; feeds Exp 8 |

Add rows in [README.md](README.md) when new notes land.
