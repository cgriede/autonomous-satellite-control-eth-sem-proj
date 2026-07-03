# Experiment pipeline — reference

## Frontmatter schema

```yaml
---
experiment_id: 2
slug: ml_modular_encoder
title: "Exp 2 — Modular encoder"
current_phase: 1                    # 0 | 1 | 2 | 3 | 4
overall_verdict: pending            # pending | supported | not_supported | partial | inconclusive | blocked
blocked_by: null
code_path: backend/scripts/experiments/ml_modular_encoder/
phases:
  "0": { status: done, documented_utc: "2026-06-29T10:00:00Z", completed_utc: "2026-06-29T11:00:00Z" }
  "1": { status: in_progress, documented_utc: null, completed_utc: null }
  "2": { status: pending, documented_utc: null, completed_utc: null }
  "3": { status: pending, documented_utc: null, completed_utc: null }
  "4": { status: pending, documented_utc: null, completed_utc: null }
run_lock_holder: null
decision_ids: []
---
```

**Init file body** (after `/init-experiment`) — title line only; no `## Phase` blocks yet:

```markdown
# Exp N — Title (`slug`)

*(Phase blocks appended by `/document-experiment-step`.)*
```

## Bin resolver

| `current_phase` | Bin |
|-----------------|-----|
| 0 | `0-initialized/` |
| 1 | `1-built/` |
| 2 | `2-run/` |
| 3 | `3-evaluation/` |
| 4 | `4-documentation/` |

On `/close-experiment-step`: move `{old-bin}/{NN}-{slug}.md` → `{new-bin}/` when phase advances across a bin boundary.

## Mandatory subsections per phase

Use **numbered headings** exactly as below. Tag (What)/(Why)/(How) in the heading text.

---

### Phase 0 — Initialized

```markdown
## Phase 0 — Initialized

### 0.1 Experiment scope (What)

- Hypothesis statement + numbered claims (H1a, H1b, …)
- Arms, frozen knobs, success metrics
- Gates / `blocked_by`
- **Atomic scope:** one primary hypothesis per slug — if two independent tracks (e.g. cadence + hyperparams), split into two experiments via AskQuestion unless user explicitly accepts one sequential slug with a runner that covers **every** track (see learnings.md `atomic-one-hypothesis-per-pipeline-slug`)

### 0.2 Thought process (Why)

- Why this experiment now; what prior runs or decisions motivate it
- What we reject or defer (link DECISIONS rows)

#### 0.2.1 Shoulders of giants

- Citations + `LITERATURE_HIGHLIGHTS` pointers
- What prior work supports (or constrains) the fork — not a full lit review (that lives in `docs/research/`)

### 0.3 Preliminary implementation remarks (How)

- Feasibility: hook point, sibling scaffold to copy, smoke strategy
- Risks, open questions before building
- *(Skills)* [`hypothesis-experiment-cycle`](../../.cursor/skills/hypothesis-experiment-cycle/SKILL.md) § ponytail rule; [`isolated-notebook-hypotheses`](../../.cursor/skills/isolated-notebook-hypotheses/SKILL.md) § Before launching branches
- *(Optional)* **Follow-up experiment** if we already suspect inconclusive scope
```

**Exit criteria (close Phase 0):** README row exists; DECISIONS/STATUS checked; 0.1–0.3 non-empty.

---

### Phase 1 — Built

```markdown
## Phase 1 — Built

### 1.1 Build plan (What)

- Single logical delta (ponytail rule)
- File / hook map; JSON result contract; analysis card path
- SUBAGENT_CHARTER + `<hypothesis>.md` paths
- *(Skills)* `isolated-notebook-hypotheses` § Contract-first + Before launching branches

### 1.2 Build implementation (How we forked)

- What was actually built (paths, agent swap, encoder delta)
- Smoke result (`results/smoke.json` or equivalent)
- Deviations from 1.1
- *(Skills)* [`hypothesis-experiment-cycle`](../../.cursor/skills/hypothesis-experiment-cycle/SKILL.md) minimal fork checklist

### 1.3 Run instructions (How to execute)

- **Numbered step table:** command → stage name (e.g. Stage A hparam sweep vs Stage B full) → what it does → output artifact — not a flat command list
- Entrypoint command(s), CLI flags, arms list; which step runs **after** which (e.g. `--full` after `screen_summary.json`)
- Mutex: auto on training commands; optional `run.py --check-mutex` — no fragile `python -c` from experiment cwd
- Expected artifacts per step: JSON summary paths
```

**Exit criteria:** Runner + `_run_guard` → global mutex; smoke passes; **pipeline MD includes `### 1.3 Run instructions`** with copy-paste commands (not README-only).

**Start gate (before coding):** Run § Implement mode (Nike vs plan) in [`SKILL.md`](SKILL.md). Nike mode → notify user + justify in chat; plan mode or upstream-bug suspicion → **ask user** before first fork edit (see learnings.md `pipeline-implement-nike-vs-plan-gate`).

---

### Phase 2 — Run

```markdown
## Phase 2 — Run

### 2.1 Run scope (What)

- Arms executed, dt/reward/agent frozen knobs
- Train/eval episode counts

### 2.2 Run monitoring (Why)

- Run order rationale; mutex / no parallel slugs
- Watch notes (long-run-watch) if applicable

### 2.3 Run log & artifacts (How)

- Per-arm run dirs, KPI JSON paths, wall time
- Errors / reruns; link `results/*_summary.json`
- **Video table (mandatory when exported):** per arm — full paths to `eval_best.mp4`, eval episodes, train rank MP4s; cite `artifacts_manifest.json` (see SKILL.md § Discussing run results; learnings.md `pipeline-discuss-runs-include-video-paths`)
- Plot paths (`plots/`, `episodes/*_reward.png`) when exported
- *(Skills)* [`long-run-watch`](../../.cursor/skills/long-run-watch/SKILL.md) if multi-hour; optional [`video-frame-inspect`](../../.cursor/skills/video-frame-inspect/SKILL.md) spot-check — record manifest path in 2.3
```

**Exit criteria:** All arms complete; `run_lock_holder` cleared; KPIs recorded. When behavior is in scope and `profile.json` enables export: at least one reward plot or MP4 path under `results/artifacts/` per stage, **or** Phase 2.3 documents explicit `--trim-artifacts` opt-in and **artifact gap** (see learnings.md `phase2-export-artifacts-not-trim-default`).

---

### Phase 3 — Evaluation

```markdown
## Phase 3 — Evaluation

### 3.1 Claims & success criteria (What)

- Restate numbered claims + explicit success bars (table-friendly)

### 3.2 Evidence summary (Why)

- Literature vs **our runs**; mechanism diagnosis
- Partial signals vs hard failures
- Link `results/<hypothesis_id>_analysis.md` (8-section card per `isolated-notebook-hypotheses`)
- Video/frame findings if [`video-frame-inspect`](../../.cursor/skills/video-frame-inspect/SKILL.md) was used

### 3.3 Verdict table (How we decided)

| # | Claim | Success criterion | … arms … | **Verdict** |
|---|-------|-------------------|----------|-------------|

- **Overall verdict:** supported | not_supported | partial | inconclusive
- *(Optional)* **Follow-up experiment** if inconclusive — what would unblock
```

**Exit criteria:** `overall_verdict` set; table complete; analysis card on disk.

*(Skills)* [`document-research`](../../.cursor/skills/document-research/SKILL.md) after Phase 3 block appended.

---

### Phase 4 — Documentation

```markdown
## Phase 4 — Documentation

### 4.1 Promotion & integration (What)

- What code (if any) merges to production / shared kernels — methods reusable across experiments
- Explicit **no promote** list
- DECISIONS row IDs

### 4.2 Closeout rationale (Why)

- Why the verdict stands; what we learned
- *(Optional)* **Follow-up experiment** — next slug or gate if inconclusive

### 4.3 Knowledge persistence (How)

- Investigation note path (`docs/research/*-investigation.md`)
- STATUS closeout line; PROJECT_KNOWLEDGE / README index updates
- Fork artifacts: `results/*.json`, `*_analysis.md`
- **Report archive** — curated paths for semester report (videos, plots, key frames)
- `video-frame-inspect` manifest paths for any report-facing MP4
- *(Skills)* [`document-research`](../../.cursor/skills/document-research/SKILL.md), [`visual-output-verification`](../../.cursor/skills/visual-output-verification/SKILL.md), [`minimal-feature-review`](../../.cursor/skills/minimal-feature-review/SKILL.md) — **user confirms** visuals before Phase 4 close
```

**Exit criteria:** [`document-research`](../document-research/SKILL.md) complete; doc in `4-documentation/`.

---

## Move + link update (every close)

1. Run `python .cursor/tools/pipeline/pipeline_doc.py close-phase --slug <slug>` (or `sync-bin` if only the folder is wrong).
2. Tool updates [`README.md`](../../../docs/experiments/pipeline/README.md) **Doc** column and fixes links under `backend/scripts/experiments/<slug>/`.
3. Agent updates README **Phase** / **Verdict** columns; grep for any remaining stale paths in STATUS / investigation notes.

## README index columns

| # | Slug | Doc | Code | Phase | Verdict | Blocked by |

`Phase` column = `current_phase` (0–4) or human label (initialized / built / run / evaluation / documentation).

## Init new experiment

1. Next `NN` from README.
2. Create `0-initialized/{NN}-{kebab-slug}.md` — frontmatter + title only.
3. Add README row; `current_phase: 0`, all `phases.*.status: pending`.

## Mutex (D-012)

One active training process per host. Phase 2 only.

## Implement mode gate (Phase 1 start)

Run before first fork edit ([`SKILL.md`](SKILL.md) § Implement mode; learnings.md `pipeline-implement-nike-vs-plan-gate`).

| Mode | When | Agent action |
|------|------|--------------|
| **Nike** | Phase 0.3 complete (hook + sibling + smoke); single delta; user approved build; fork-only; no semantic-contract risk | Notify user + 2–4 bullet justification; then build |
| **Plan** | Any TBD on hook; no sibling; multi-hook; prod edit; cross-cutting | Short sketch in chat; **wait for user** |
| **Upstream bug** | Workaround would mask prod/sim defect | **Ask user** — fix upstream, defer, or DECISIONS workaround |

Do not ask "do we need a build plan?" when Nike criteria already pass. Phase 1.1 is documented at `/document-experiment-step`, not a separate plan artifact.
