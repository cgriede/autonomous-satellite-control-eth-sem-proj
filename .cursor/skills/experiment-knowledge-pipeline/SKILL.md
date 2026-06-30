---
name: experiment-knowledge-pipeline
description: >-
  Orchestrates ML pipeline experiments: five phases (0–4), each documented as one
  append-only block (What / Why / How subsections) in docs/experiments/pipeline/{bin}/{NN}-{slug}.md.
  Use /init-experiment, /start-experiment-step, /document-experiment-step (append phase),
  /close-experiment-step (advance phase + bin move). Chains hypothesis-research-literature,
  hypothesis-experiment-cycle, long-run-watch, document-research, isolated-notebook-hypotheses,
  visual-output-verification, video-frame-inspect. Global run mutex via pipeline_run_guard.
disable-model-invocation: false
---

# Experiment Knowledge Pipeline

**One experiment = one markdown file** under [`docs/experiments/pipeline/{bin}/`](../../../docs/experiments/pipeline/).  
**Index only:** [`README.md`](../../../docs/experiments/pipeline/README.md).

## Core doc rule (mandatory)

**Append only — never rewrite a closed phase.**

- Each **phase** is one top-level block: `## Phase N — …` with **three numbered subsections** (What / Why / How).
- `/document-experiment-step` **appends** the block for the **current** phase only.
- Prior `## Phase 0` … `## Phase N-1` blocks are **read-only** after `/close-experiment-step`.
- Do **not** pre-fill future phases or backfill multiple phases in one write (unless user explicitly requests a migration).

Read [`reference.md`](reference.md) for subsection templates and [`skill-chain.md`](skill-chain.md) for **which child skill to invoke per phase**.

## Skill chain (summary)

```text
Phase 0 → hypothesis-research-literature + planning contract (isolated-notebook-hypotheses)
Phase 1 → hypothesis-experiment-cycle (fork, smoke, JSON + analysis card scaffold)
Phase 2 → hypothesis-experiment-cycle + long-run-watch; spot-check visuals (video-frame-inspect)
Phase 3 → analysis card + document-research; video-frame-inspect if verdict uses video evidence
Phase 4 → document-research + visual-output-verification + report archive (human sign-off)
```

Full per-subsection map: [`skill-chain.md`](skill-chain.md).

## Phases and bins

| Phase | Bin folder | Top-level heading | When it closes |
|-------|------------|-------------------|----------------|
| **0** | `0-initialized/` | `## Phase 0 — Initialized` | Scope + rationale + feasibility frozen |
| **1** | `1-built/` | `## Phase 1 — Built` | Fork scaffolded; smoke passes |
| **2** | `2-run/` | `## Phase 2 — Run` | All arms executed; KPIs recorded |
| **3** | `3-evaluation/` | `## Phase 3 — Evaluation` | Verdict table complete |
| **4** | `4-documentation/` | `## Phase 4 — Documentation` | Promotion + persistence recorded |

`current_phase` in frontmatter is **0–4**. Bin must match `current_phase` (see [`reference.md`](reference.md) § Bin resolver).

## Commands

| Command | Action |
|---------|--------|
| `/init-experiment` | Create `0-initialized/{NN}-{slug}.md` with frontmatter + title only (**no phase body**) |
| `/start-experiment-step` | Work on **current phase** — delegate to child skill; set `phases.<N>.status: in_progress` |
| `/document-experiment-step` | **Append** `## Phase N` + all mandatory subsections for current phase |
| `/close-experiment-step` | Verify phase block exists → `phases.<N>.status: done` → advance `current_phase` → **move bin** → update README + links |

**Order:** finish work → `/document-experiment-step` → `/close-experiment-step`. Do not close without documenting.

## Phase → child skill map

| Phase | Primary skills | Also use |
|-------|----------------|----------|
| **0** | [`hypothesis-research-literature`](../hypothesis-research-literature/SKILL.md) | [`isolated-notebook-hypotheses`](../isolated-notebook-hypotheses/SKILL.md) § Before launching branches |
| **1** | [`hypothesis-experiment-cycle`](../hypothesis-experiment-cycle/SKILL.md) | `isolated-notebook-hypotheses` § Fixed result contract, evidence-first |
| **2** | `hypothesis-experiment-cycle` | [`long-run-watch`](../long-run-watch/SKILL.md), [`visual-output-verification`](../visual-output-verification/SKILL.md), [`video-frame-inspect`](../video-frame-inspect/SKILL.md) |
| **3** | [`document-research`](../document-research/SKILL.md) | `hypothesis-experiment-cycle` + analysis card §1–8; `video-frame-inspect` if video informs verdict |
| **4** | `document-research` | `visual-output-verification`, `video-frame-inspect`, [`minimal-feature-review`](../minimal-feature-review/SKILL.md) (human confirm) |

## Workflow: start phase

```text
1. Locate docs/experiments/pipeline/*/{NN}-{slug}.md; read current_phase + phases.* in frontmatter
2. Confirm file is in the bin matching current_phase
3. Read PROJECT_KNOWLEDGE + DECISIONS + STATUS — respect blocked_by
4. Read skill-chain.md for current phase — invoke listed child skills
5. If current_phase == 2 → pipeline mutex check before launching training
6. Run phase checklist (reference.md)
7. Set phases.<N>.status: in_progress
8. Do NOT append the phase block until /document-experiment-step
9. Do NOT advance current_phase until /close-experiment-step
10. Semantic bugs (action space, warmup contract): **define fix in doc/chat first** — do not edit fork code until user agrees (see learnings.md `define-fix-before-implement-experiment`).
```

## Workflow: document phase

```text
1. Confirm current_phase = N and phases.N not already documented (status != done)
2. Run any child skills not yet done for this phase (skill-chain.md) — e.g. analysis card before Phase 3 append
3. Append ## Phase N — … plus every mandatory ### subsection (reference.md)
4. Fill only this phase — leave earlier phases untouched
5. Phase 2: include video/plot paths in 2.3 if exported; note video-frame-inspect manifest if run
6. Phase 4: 4.3 must list report-archive paths + persistence layers (skill-chain.md checklist)
7. Optional: Follow-up experiment if inconclusive (0.3, 3.3, 4.2)
8. Set phases.<N>.documented_utc in frontmatter (status stays in_progress until close)
```

## Workflow: close phase

```text
1. Verify ## Phase N block exists and subsections are non-empty
2. phases.<N>: status=done, completed_utc
3. current_phase ← N+1 (or stay at 4 when finished)
4. Move doc to bin for new current_phase if changed
5. Update pipeline README Doc column ({bin}/{NN}-{slug}.md)
6. Grep repo; fix stale pipeline paths in STATUS, investigation notes, analysis cards
7. Phase 2 close: clear run_lock_holder
8. Phase 3 close: overall_verdict set in frontmatter
9. Phase 4 close: document-research + user visual sign-off per skill-chain.md
```

## Compute mutex (Phase 2 only)

**One ML pipeline training job per host** ([D-012](../../../docs/research/DECISIONS.md)).

| Mechanism | Path |
|-----------|------|
| Lock | `backend/scripts/experiments/.pipeline_run.lock` |
| Mirror | `docs/experiments/pipeline/.active_run.json` |
| Module | `backend/scripts/experiments/pipeline_run_guard.py` |

Before Phase 2 training: `check_pipeline_run_clear(slug)`. Each `_run_guard.py` calls `acquire_pipeline_run_lock`.

## Promotion boundary

Phase **4.1** records what (if anything) merges to production kernels. No production edits during Phases 0–3 without user-approved promote ([D-003](../../../docs/research/DECISIONS.md)).

**After a successful run or user “promote” request:** complete pipeline closeout first — append Phases 2–4, move doc to `4-documentation/`, set `overall_verdict`, update README + DECISIONS — **then** implement production promotion as a separate change. Never skip straight from KPI/video review to `reward.py` / `simulation/` edits (see learnings.md `pipeline-closeout-before-promote`).

## Discussing run results (chat + review)

When reporting pipeline run outcomes (overnight recap, arm comparison, Phase 2/3 prep), pair KPIs with **clickable video paths** — see learnings.md `pipeline-discuss-runs-include-video-paths` and [experiment-visual-evidence](../../rules/experiment-visual-evidence.mdc).

Per arm (from `run_dir/artifacts_manifest.json` or `config.json` → `artifact_paths`):

1. **Eval first:** `videos/eval_best.mp4`, then each `eval_ep_*_rank*.mp4` (verdict-relevant).
2. **Train highlights:** top-ranked `train_ep_*_rank*.mp4` from the manifest.
3. **Manifest:** full path to `artifacts_manifest.json` for closeout / frame inspect.

Agent may run [`video-frame-inspect`](../video-frame-inspect/SKILL.md) as pre-check; user watches MP4 for behavioral sign-off.

## Related skills

| Skill | Role in pipeline |
|-------|------------------|
| [`skill-chain.md`](skill-chain.md) | Full per-phase / per-subsection skill map |
| [`hypothesis-experiment-cycle`](../hypothesis-experiment-cycle/SKILL.md) | Phases 1–3 fork + run |
| [`isolated-notebook-hypotheses`](../isolated-notebook-hypotheses/SKILL.md) | JSON contract + analysis card template (legacy name; still authoritative) |
| [`visual-output-verification`](../visual-output-verification/SKILL.md) | Phases 2–4 visual gate |
| [`video-frame-inspect`](../video-frame-inspect/SKILL.md) | MP4 → PNG for agent + report citations |

## Related docs

- [STATUS board](../../../docs/ml/experiments/STATUS_2026-06.md)
- [DECISIONS](../../../docs/research/DECISIONS.md)
- [`python-runtime-environment`](../python-runtime-environment/SKILL.md) — `conda activate auto-sat`
