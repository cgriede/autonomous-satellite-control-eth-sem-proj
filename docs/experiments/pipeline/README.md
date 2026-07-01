# ML experiment pipeline — documentation

**Live status:** [STATUS_2026-06.md](../../ml/experiments/STATUS_2026-06.md)  
**Decisions:** [DECISIONS.md](../../research/DECISIONS.md) · **Reasoning depth:** [PROJECT_KNOWLEDGE.md](../../research/PROJECT_KNOWLEDGE.md)  
**Orchestrator skill:** [experiment-knowledge-pipeline](../../../.cursor/skills/experiment-knowledge-pipeline/SKILL.md) · [skill chain](../../../.cursor/skills/experiment-knowledge-pipeline/skill-chain.md) (`/start-experiment-step`, `/document-experiment-step`, `/close-experiment-step`)  
**Master plan:** [sac_vs_mpo_compare plan](../../../.cursor/plans/sac_vs_mpo_compare_821ab4d5.plan.md)

This folder is the **canonical experiment record** for each pipeline step: charter through closeout in one markdown file per experiment. Deep reasoning lives in `docs/research/*-investigation.md`.

## Pipeline bins

Move each experiment doc into the folder that matches its **current** lifecycle stage:

| Bin | Phase | When to use |
|-----|-------|-------------|
| [`0-initialized/`](0-initialized/) | **0** | Scope, rationale, literature — append `## Phase 0` only |
| [`1-built/`](1-built/) | **1** | Fork built — append `## Phase 1` only |
| [`2-run/`](2-run/) | **2** | Arms executed — append `## Phase 2` only |
| [`3-evaluation/`](3-evaluation/) | **3** | Verdict table — append `## Phase 3` only |
| [`4-documentation/`](4-documentation/) | **4** | Promotion + persistence — append `## Phase 4` only |
| [`99-archive/`](99-archive/) | — | Deferred or superseded charters (not active pipeline) |

Each phase block uses **What / Why / How** subsections (see skill `reference.md`). **Append only** — never rewrite closed phases.

## Compute policy

**One training run at a time** on this host ([D-012](../../research/DECISIONS.md)). Lock: `backend/scripts/experiments/.pipeline_run.lock` · mirror: [`.active_run.json`](.active_run.json) (gitignored).

**Overnight batch (Exp 10→13):** `backend/scripts/experiments/run_pipeline_overnight_batch.py --show-progress --git-sync-runs --skip-not-ready --continue-on-error`  
**Watch:** `.cursor/tools/watch_pipeline_overnight_batch.ps1` · profile [`ml-pipeline-overnight-batch-10-13`](../../.cursor/skills/long-run-watch/profiles/ml-pipeline-overnight-batch-10-13.md)

## Run order

| # | Slug | Doc | Code | Phase | Verdict | Blocked by |
|---|------|-----|------|-------|---------|------------|
| 1 | `ml_shutter_threshold` | [01-shutter-threshold.md](4-documentation/01-shutter-threshold.md) | `backend/scripts/experiments/ml_shutter_threshold/` | closeout | not_supported | — |
| 2 | `ml_modular_encoder` | [02-modular-encoder.md](4-documentation/02-modular-encoder.md) | `backend/scripts/experiments/ml_modular_encoder/` | closeout | **not_supported** | — |
| 3 | `ml_sac_mpo_compare` | [03-sac-mpo-compare.md](4-documentation/03-sac-mpo-compare.md) | `backend/scripts/experiments/ml_sac_mpo_compare/` | 4 | **supported** | — |
| 4 | `ml_agent_reference_pointing` | [04-agent-reference-pointing.md](4-documentation/04-agent-reference-pointing.md) | `backend/scripts/experiments/ml_agent_reference_pointing/` | 4 | **partial** | — |
| 5 | `ml_mpo_model_size` | [05-mpo-model-size.md](4-documentation/05-mpo-model-size.md) | `backend/scripts/experiments/ml_mpo_model_size/` | 4 | **not_supported** | — |
| 6 | `ml_modular_encoder_r2` | [0-06-modular-encoder-r2.md](99-archive/0-06-modular-encoder-r2.md) | `backend/scripts/experiments/ml_modular_encoder_r2/` | — | **deferred** | — |
| 7 | `ml_sac_vector_budget_penalty` | [07-sac-vector-budget-penalty.md](4-documentation/07-sac-vector-budget-penalty.md) | `backend/scripts/experiments/ml_sac_vector_budget_penalty/` | 4 | **supported** | — |
| 8 | `ml_mpo_decoupled_dual_torque` | [08-mpo-decoupled-dual-fix.md](4-documentation/08-mpo-decoupled-dual-fix.md) | `backend/scripts/experiments/ml_mpo_decoupled_dual_torque/` | closeout | **partial** | — |
| 9 | `ml_sac_shutter_reward_split` | [09-sac-shutter-reward-split.md](4-documentation/09-sac-shutter-reward-split.md) | `backend/scripts/experiments/ml_sac_shutter_reward_split/` | closeout | **supported** | — |
| 10 | `ml_mpo_safe_mode_penalty` | [10-mpo-safe-mode-penalty.md](3-evaluation/10-mpo-safe-mode-penalty.md) | `backend/scripts/experiments/ml_mpo_safe_mode_penalty/` | **3** | pending | — |
| 11 | `ml_mpo_decoupled_dual_vector` | [11-mpo-decoupled-dual-vector.md](3-evaluation/11-mpo-decoupled-dual-vector.md) | `backend/scripts/experiments/ml_mpo_decoupled_dual_vector/` | **3** | pending | — |
| 12 | `ml_mpo_vector_torque_effort` | [12-mpo-vector-torque-effort.md](3-evaluation/12-mpo-vector-torque-effort.md) | `backend/scripts/experiments/ml_mpo_vector_torque_effort/` | **3** | pending | — |
| 13 | `ml_mpo_learn_cadence_hparams` | [13-mpo-learn-cadence-hparams.md](2-run/13-mpo-learn-cadence-hparams.md) | `backend/scripts/experiments/ml_mpo_learn_cadence_hparams/` | 2 | pending | — |

## Shared knobs (all pipeline experiments)

| Knob | Value |
|------|-------|
| `sim_dt_s` | **1.5 s** |
| `controller_interval_s` | **1.5 s** |
| Warmup cache | **rebuild** each arm |
| Production `autonomous_control/` / `simulation/` / `render/` | **read-only** (experiment forks only) |
| Concurrent training | **forbidden** — global `pipeline_run_guard` |

## Platform issues (all experimenters)

| Issue | Severity | Pick up | Notes |
|-------|----------|---------|-------|
| **Training-run video export** | **Pressing (perf)** | Frontend / render agent | MP4 encode is slow and may lag KPIs — fix encode path, not science. **Videos are hard behavioral evidence** (pointing, shutters, learning over time); KPI JSON is for quick reward estimates only. Rule: [experiment-visual-evidence](../../.cursor/rules/experiment-visual-evidence.mdc). Keep `TrainingWorkflowConfig` video defaults unless user opts into `--trim-artifacts`. Phase 2.3: full `run_dir/videos/` paths + `video-frame-inspect` manifest. |

**Code touchpoints:** `backend/notebooks/s01/s01_utils/training_workflow.py`, `backend/utils/ml_training/training_run_artifacts.py`, `backend/render/`.  
**Decision:** [D-013](../../research/DECISIONS.md). Phase 4 report archive lists curated MP4/plot paths; user confirms before closeout.

## Run directories — how to find “which run is which experiment”

All training outputs live under **`backend/autonomous_control/runs/`**. Folder names look cryptic but follow one pattern:

```text
{16-digit-sort-prefix}_ml_{experiment-slug}_{arm-or-variant}_{HH-MM-SS}
```

| Part | Meaning |
|------|---------|
| **16-digit prefix** | Reverse timestamp so **newer runs sort higher** in the file explorer |
| **`ml_…` slug** | Script-specific label set by the experiment runner (see table below) |
| **`HH-MM-SS` suffix** | UTC launch time on that day |

**Authoritative mapping** (always check this first):

1. Open **`config.json`** inside the run folder → block **`experiment.experiment_id`** (pipeline slug) and **`experiment.arm_id`** (if present).
2. Pipeline doc **Phase 2** table → lists the **canonical** run dir for each arm (when documented).
3. Experiment **`results/*.json`** → e.g. `ml_agent_reference_pointing/results/agent_reference.json` points at the latest summary KPIs (not always full paths).

### Slug → pipeline experiment (quick reference)

| Folder slug contains | Pipeline # | Experiment slug | Script folder |
|----------------------|------------|-----------------|---------------|
| `ml_ref_` | **Exp 4** | `ml_agent_reference_pointing` | `scripts/experiments/ml_agent_reference_pointing/` |
| `ml_compare_` | **Exp 3** | `ml_sac_mpo_compare` | `scripts/experiments/ml_sac_mpo_compare/` |
| `ml_encoder_` (not `r2`) | **Exp 2** | `ml_modular_encoder` | `scripts/experiments/ml_modular_encoder/` |
| `ml_encoder_r2_` | **Exp 6** | `ml_modular_encoder_r2` | `scripts/experiments/ml_modular_encoder_r2/` |
| `ml_mpo_model_size_` | **Exp 5** | `ml_mpo_model_size` | `scripts/experiments/ml_mpo_model_size/` |
| `ml_mpo_decoupled_dual_torque_` | **Exp 8** | `ml_mpo_decoupled_dual_torque` | `scripts/experiments/ml_mpo_decoupled_dual_torque/` |
| `ml_mpo_decoupled_dual_vector_` | **Exp 11** | `ml_mpo_decoupled_dual_vector` | `scripts/experiments/ml_mpo_decoupled_dual_vector/` |
| `ml_sac_vector_budget_` | **Exp 7** | `ml_sac_vector_budget_penalty` | `scripts/experiments/ml_sac_vector_budget_penalty/` |
| `ml_mpo_safe_mode_penalty_` | **Exp 10** | `ml_mpo_safe_mode_penalty` | `scripts/experiments/ml_mpo_safe_mode_penalty/` |
| `ml_mpo_learn_cadence_` | **Exp 13** | `ml_mpo_learn_cadence_hparams` | `scripts/experiments/ml_mpo_learn_cadence_hparams/` |
| `ml_mpo_vector_torque_effort_` | **Exp 12** | `ml_mpo_vector_torque_effort` | `scripts/experiments/ml_mpo_vector_torque_effort/` |
| `ml_shutter_` | **Exp 1** | `ml_shutter_threshold` | `scripts/experiments/ml_shutter_threshold/` |
| `ml_overnight_` | *(legacy)* | H0–H6 overnight campaign | `scripts/experiments/ml_algo_overnight/` |
| `train_timing_` | *(not pipeline)* | Timing profiler only | `scripts/experiments/train_timing/` |

### Exp 4 arms (current valid re-run)

| Arm | Folder slug core | Canonical run (2026-06-30) |
|-----|------------------|----------------------------|
| **ref0** torque | `ml_ref_ref0_torque_*` | `9998217183842846_ml_ref_ref0_torque_10-42-36` |
| **ref1** vector | `ml_ref_ref1_vector_*` | `9998217182442815_ml_ref_ref1_vector_11-05-57` |

Older `ml_ref_ref1_vector_*` folders from before the vector-OBC fix are **invalid** for H4 verdict (warmup semantics wrong). Prefer runs after Phase 2 doc date in [04-agent-reference-pointing.md](1-built/04-agent-reference-pointing.md).

Smokes: `ml_ref_smoke_*` (ref0), or ref1 with `--train-episodes 1 --trim-artifacts` (e.g. `…_10-40-50`).
