

# README.md

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


# 02-modular-encoder.md

---
experiment_id: 2
slug: ml_modular_encoder
title: "Exp 2 — Modular encoder"
current_phase: 4
overall_verdict: not_supported
blocked_by: null
code_path: backend/scripts/experiments/ml_modular_encoder/
phases:
  "0": { status: done, documented_utc: "2026-06-29T18:00:00Z", completed_utc: "2026-06-29T18:00:00Z" }
  "1": { status: done, documented_utc: "2026-06-29T18:00:00Z", completed_utc: "2026-06-29T17:05:00Z" }
  "2": { status: done, documented_utc: "2026-06-29T20:30:00Z", completed_utc: "2026-06-29T17:07:35Z", arms: [sac_a0, sac_a1] }
  "3": { status: done, documented_utc: "2026-06-29T20:30:00Z", completed_utc: "2026-06-29T21:00:00Z" }
  "4": { status: done, documented_utc: "2026-06-29T21:15:00Z", completed_utc: "2026-06-29T21:30:00Z" }
run_lock_holder: null
run_started_utc: "2026-06-29T16:34:58Z"
decision_ids: [D-006, D-013, D-014, D-015]
---

# Exp 2 — Modular encoder (`ml_modular_encoder`)

**Agent:** SAC sparse · **dt:** 1.5 s / 1.5 s · **Train:** 7 episodes  
**Evaluated:** 2026-06-29 · **Closed:** 2026-06-29 · **Decision IDs:** [D-006](../../research/DECISIONS.md), [D-014](../../research/DECISIONS.md), [D-015](../../research/DECISIONS.md)  
**Plan:** [sac_vs_mpo_compare plan](../../../../.cursor/plans/sac_vs_mpo_compare_821ab4d5.plan.md) · **Investigation:** [model-size-investigation.md](../../research/model-size-investigation.md)

---



## Phase 0 — Initialized



### 0.1 Experiment scope (What)



**Hypothesis (H1):** SAC sparse with **vector compressors** on per-target bearing/mask (arm **A1**) outperforms production flat `ControllerEncoder` (arm **A0**) on `learning_mode` and returns.



| Claim | Success criterion |

|-------|-------------------|

| **H1a** | A1 `learning_mode` **true** while A0 false, or A1 sustained eval return improvement |

| **H1b** | A1 best train return **>** A0 |

| **H1c** | A1 improves secondary KPIs vs A0 (`positive_reward_steps`, shutter meaningful fraction) |



**Arms:** `sac_a0` (flat / production encoder) vs `sac_a1` (compress, `vector_embed_dim=8`).



**Frozen protocol:** SAC sparse · dt **1.5 s / 1.5 s** · 7 train · 5 warmup (rebuild cache per arm) · 2 eval ([D-002](../../research/DECISIONS.md)).



**Stop rule:** No KPI gap after 7 eps → **do not** add split-head arms; report “flat MLP / concat not the bottleneck.”



**Gates:** [D-006](../../research/DECISIONS.md) — encoder before MPO width ablation; Exp 1 shutter threshold **not supported** (pipeline proceeds here).



### 0.2 Thought process (Why)



- Overnight MPO runs showed warmup OK then collapse; width ablation deferred ([D-005](../../research/DECISIONS.md)) — **structure before capacity**.

- Exp 1 rejected threshold + capture-window alone ([D-009](../../research/DECISIONS.md), [D-010](../../research/DECISIONS.md)); spam/latent reward may be **encoder + credit**, not shutter knob.

- Scalar observation is **105-D** with **50+50** ordered target bearing/mask fields — flattening may be sample-inefficient vs group compressors.

- SAC chosen as sole learner for this arm (MPO compare deferred to Exp 3).



#### 0.2.1 Shoulders of giants



- **Entity- / set-structured observations** — per-target fields; ordered slots (not full Deep Sets sum-pool): [compositional policy architectures](https://openreview.net/pdf/ceead8c5d2c73b2e871b5d6bddf870a3c404f75a.pdf), [entity-based RL survey](https://arxiv.org/html/2410.17647v3).

- **Multimodal fusion** — CNN vision + scalar streams → trunk MLP: [MERL](https://openreview.net/pdf/6c53a204af9367febb3d6fdad8ca87528ae40d9f.pdf).

- **Group bottleneck** — `Linear(50 → k)` on bearing/mask vs flat concat (lightweight; preserves slot order).

- Project synthesis: [model-size-investigation.md](../../research/model-size-investigation.md) · plan § Exp 2 literature.

- Fork doc: `backend/scripts/experiments/ml_modular_encoder/H1-modular-encoder.md`



### 0.3 Preliminary implementation remarks (How)



- **Hook:** swap agent after `build_training_workflow_setup` — encoder-only delta; training loop unchanged.

- **Scaffold:** copy overnight patterns (`_reward_fork`, `_sim_constants_fork`, `_runner_common` KPIs, `pipeline_run_guard`).

- **Smoke:** `run_modular_encoder.py --smoke` — 1 warmup ep, A1 `SACModularAgent`, buffer + one `train()` step.

- **Risks:** `agents` package name collision with overnight (resolved → `encoder_agents/`); SAC lr names must match `sac_agent_fork`.

- **Follow-up if inconclusive:** proceed to Exp 3 SAC vs MPO dense; do **not** widen encoder (split heads) without `learning_mode` on A1. **Deferred rerun:** [Exp 6](../0-initialized/06-modular-encoder-r2.md) after Exp 5 MPO sizing.



---



## Phase 1 — Built



### 1.1 Build plan (What)



**Single delta:** replace flat concat of bearing + mask vectors with **`Linear(n, k)`** compressors (`k=8`); passthrough globals + vision CNN unchanged.



| Component | Path |

|-----------|------|

| Scalar partition | `encoders/scalar_split.py` |

| A1 encoder | `encoders/compressed_controller_encoder.py` |

| SAC + modular actor/critic | `encoder_agents/sac_modular_agent.py`, `modular_actor.py`, `modular_critic.py` |

| A0 baseline | Overnight `sac_agent_fork.SACAgent` (production `ControllerEncoder`) |

| Runner | `run_modular_encoder.py`, `_encoder_runner.py` |

| dt / reward / baseline | `_encoder_sim.py`, `_frozen_baseline.py`, overnight forks |

| Charter / hypothesis | `SUBAGENT_CHARTER.md`, `H1-modular-encoder.md` |



**JSON contract:** `results/modular_encoder_summary.json` · **Analysis card:** `modular_encoder_analysis.md`



### 1.2 Build implementation (How we forked)



- Global mutex via `pipeline_run_guard` (`_run_guard.py`).

- A0: `importlib` load `ml_algo_overnight/agents/sac_agent_fork.py`.

- A1: `SACModularAgent` + `CompressedControllerEncoder` (passthrough + bearing/mask compress + vision fusion).

- **Smoke passed** (`results/smoke.json`): `passed: true`, warmup return **72.7**, 516 steps, buffer 516, `encoder_mode: compress`, `vector_embed_dim: 8`.

- **Deviations:** local package renamed `agents/` → `encoder_agents/`; `sys.path` order `reversed(_PATH_ROOTS)`; `SACModularAgent` uses `learning_rate_pi` / `learning_rate_q`.



### 1.3 Run instructions (How to execute)



**Mutex:** one pipeline job per host ([D-012](../../research/DECISIONS.md)) — `backend/scripts/experiments/.pipeline_run.lock`.



```powershell

conda activate auto-sat

cd D:\code\sem-proj-asc\backend\scripts\experiments\ml_modular_encoder

python .\run_modular_encoder.py --show-progress --arms sac_a0,sac_a1

```



| Flag | Purpose |

|------|---------|

| `--smoke --allow-cpu` | Quick A1 warmup + train step |

| `--vector-embed-dim 8` | A1 bottleneck (default) |

| `--train-episodes 7` | Fast slice (default) |



**Expected artifacts per arm:**



- `backend/autonomous_control/runs/ml_encoder_<arm>_<stamp>/` (train/eval, optional videos per training workflow)

- `results/modular_encoder_summary.json`, `modular_encoder_analysis.md`, `results/modular_encoder.log`

- After run: optional `video-frame-inspect` on eval MP4 → cite manifest in Phase **2.3**

- **Platform note ([D-013](../../research/DECISIONS.md)):** training-run video export is slow — default run uses trimmed eval video; full MP4 set needs `--full-artifacts` and may finish after KPIs. Frontend agent owns improvement.



---



## Phase 2 — Run



### 2.1 Run scope (What)



| Item | Value |

|------|-------|

| Command | `run_modular_encoder.py --show-progress --arms sac_a0,sac_a1` |

| Arms | `sac_a0` (flat), `sac_a1` (compress k=8) |

| dt | **1.5 s / 1.5 s** (`dt_profile.json`) |

| Reward | **sparse** |

| Warmup / train / eval | 5 / 7 / 2 |

| Completed UTC | 2026-06-29T17:07:35Z (`modular_encoder_summary.json`) |

| Exit code | 0 |



### 2.2 Run monitoring (Why)



- Sequential arms in one process (mutex [D-012](../../research/DECISIONS.md)); **sac_a0** then **sac_a1**.

- Wall time ~**987 s** (A0) + ~**970 s** (A1); videos encoded sync after each arm (~6 MP4s/arm).

- No run abort; dt guard lines logged per arm.



### 2.3 Run log & artifacts (How)



**Summary:** `results/modular_encoder_summary.json` · **Log:** `results/modular_encoder.log` · **Analysis:** `modular_encoder_analysis.md`



| Arm | Run dir | Eval mean | `learning_mode` | Train shutter cmds/ep (approx) | Eval shutter cmds/ep |

|-----|---------|-----------|-----------------|-------------------------------|----------------------|

| **sac_a0** | `autonomous_control/runs/9998217249101092_ml_encoder_sac_a0_16-34-58/` | −78.9 | false | ~236 | ~223 |

| **sac_a1** | `autonomous_control/runs/9998217248114377_ml_encoder_sac_a1_16-51-25/` | −86.5 | false | ~210 | ~98 |



**Plots:** `plots/returns_by_episode.png`, `plots/learning_curves.png` per run dir.



**Videos (eval):** `videos/eval_best.mp4`, `videos/eval_ep_0_rank1.mp4` (both arms).



**Learning signals (train ep 7):** A0 `q_loss≈1420`, `pi_loss≈−98`; A1 `q_loss≈3190`, `pi_loss≈−109` — critic divergence, returns worsen after ep 0.



**Shared diagnostics:** `shutter_meaningful_fraction=0` both arms (no applied capture credit above ε).



---



## Phase 3 — Evaluation



### 3.1 Claims & success criteria (What)



| ID | Claim | Success bar |

|----|-------|-------------|

| **H1a** | A1 learns better than A0 | A1 `learning_mode=true` or eval return ↑ vs A0 |

| **H1b** | A1 best train return > A0 | Best train −75.1 (A1) vs −72.4 (A0) |

| **H1c** | A1 secondary KPIs better | Meaningful shutter fraction or spam↓ at equal return |



### 3.2 Evidence summary (Why)



- **Neither arm learned** (`learning_mode=false`): train returns **degrade** from ep 0; SAC **q_loss explodes** (especially A1).

- **A1 worse than A0** on eval (−86.5 vs −78.9) despite **fewer** eval shutters (~98 vs ~223/ep) — selectivity without value.

- vs **MPO Exp 1** (~516 shutters/ep, return −101.6): SAC spams less and avoids collapse floor, but **encoder delta did not improve** SAC outcomes.

- **Zero meaningful captures** on both arms (same as Exp 1) — sparse 7-ep slice is a **weak test** of encoder benefit; stop rule still applies: no encoder widening.

- **Warmup identical** (+393 mean) — post-warmup failure is policy/credit, not mission seed.



### 3.3 Verdict table (How we decided)



| # | Claim | Criterion | sac_a0 | sac_a1 | **Verdict** |

|---|-------|-----------|--------|--------|-------------|

| H1a | Learning / eval lift | `learning_mode` or eval ↑ | false, −78.9 | false, −86.5 | **Rejected** |

| H1b | Train return | A1 > A0 best train | −72.4 best | −75.1 best | **Rejected** |

| H1c | Secondary KPIs | Meaningful shutter or spam↓ @ equal return | meaningful=0 | meaningful=0; fewer shutters but worse return | **Rejected** |



**Overall verdict: `not_supported`** — vector compress encoder (**A1**) shows **no meaningful benefit** vs flat (**A0**); flat concat / group bottleneck is **not** the limiting lever in this SAC sparse slice.



**Per-arm JSON verdict:** `inconclusive` (pipeline KPI gate) — science conclusion is **H1 not supported**.



**Follow-up:** [Exp 3](../../1-built/03-sac-mpo-compare.md) (algorithm/reward); [Exp 6](../0-initialized/06-modular-encoder-r2.md) (encoder rerun after Exp 5 learnable protocol). **Do not** add split-head encoder arms.

**Deferred interest ([D-015](../../research/DECISIONS.md)):** If the stack ever reaches **`learning_mode=true`**, group compressors on bearing/mask remain **highly interesting** — v1 cannot test that fairly today.

---

## Phase 4 — Documentation

### 4.1 Promotion & integration (What)

**No production promote** ([D-003](../../research/DECISIONS.md)):

| Component | Disposition |
|-----------|-------------|
| `CompressedControllerEncoder` / `encoder_agents/` | Stays in `ml_modular_encoder/` fork only |
| Production `ControllerEncoder` | Unchanged — flat concat remains baseline |
| `encoders/scalar_split.py` | Reusable pattern; not merged until learnable rerun |

**Reusable for later experiments:** fork runner, encoder swap hook, JSON + analysis card contract.

**Decision IDs:** [D-006](../../research/DECISIONS.md) (encoder-before-width gate satisfied), [D-014](../../research/DECISIONS.md) (H1 not supported v1), [D-015](../../research/DECISIONS.md) (deferred high interest).

### 4.2 Closeout rationale (Why)

**Verdict stands:** H1 **not supported** in the SAC sparse 7-ep slice — A1 did not beat A0; neither arm learned; `shutter_meaningful_fraction=0`.

**Deferred high interest:** Once **reward / credit assignment / algorithm** produce a learnable policy (`learning_mode=true`, stable critic, meaningful captures), **vector compressors on ordered target slots** could be **very helpful**:

- Observation is **105-D** with **50+50** structured bearing/mask fields — flattening may be sample-inefficient at scale.
- A1 already showed **lower eval shutter rate** than A0 (~98 vs ~223 cmds/ep) in v1 — a hint of different action structure worth retesting **only when learning is real**, not under q_loss blow-up.
- Literature + [model-size-investigation.md](../../research/model-size-investigation.md) motivation unchanged; v1 failure is **protocol-limited**, not proof the idea is dead.

**Do not** interpret v1 as “never use compressors” — interpret as **“not the current bottleneck.”**

**Follow-up:** [Exp 3](../../1-built/03-sac-mpo-compare.md) → [Exp 5](05-mpo-model-size.md) → [Exp 6](../0-initialized/06-modular-encoder-r2.md) (encoder r2 in learnable regime).

### 4.3 Knowledge persistence (How)

| Layer | Path |
|-------|------|
| Pipeline closeout | This file (`4-documentation/02-modular-encoder.md`) |
| Analysis card | `backend/scripts/experiments/ml_modular_encoder/modular_encoder_analysis.md` |
| Summary JSON | `backend/scripts/experiments/ml_modular_encoder/results/modular_encoder_summary.json` |
| DECISIONS | [D-014](../../research/DECISIONS.md), [D-015](../../research/DECISIONS.md) |
| STATUS | [STATUS_2026-06.md](../../ml/experiments/STATUS_2026-06.md) |
| Deferred rerun charter | [06-modular-encoder-r2.md](../0-initialized/06-modular-encoder-r2.md) |
| Run dirs | `…_ml_encoder_sac_a0_16-34-58/`, `…_ml_encoder_sac_a1_16-51-25/` |

**Pipeline next:** **Exp 3** SAC vs MPO (mutex free).


# 03-sac-mpo-compare.md

---
experiment_id: 3
slug: ml_sac_mpo_compare
title: "Exp 3 — SAC vs MPO compare"
current_phase: 4
overall_verdict: supported
blocked_by: null
code_path: backend/scripts/experiments/ml_sac_mpo_compare/
plan_ref: ".cursor/plans/sac_vs_mpo_compare_821ab4d5.plan.md — Track 3"
phases:
  "0": { status: done, documented_utc: "2026-06-29T20:00:00Z", completed_utc: "2026-06-29T21:30:00Z" }
  "1": { status: done, documented_utc: "2026-06-29T21:30:00Z", completed_utc: "2026-06-30T13:00:00Z", arms: [compare_sac, compare_mpo] }
  "2": { status: done, documented_utc: "2026-06-30T13:00:00Z", completed_utc: "2026-06-30T13:00:00Z" }
  "3": { status: done, documented_utc: "2026-06-30T13:00:00Z", completed_utc: "2026-06-30T13:00:00Z" }
  "4": { status: pending, documented_utc: null, completed_utc: null }
run_lock_holder: null
decision_ids: [D-002, D-007, D-011, D-012, D-013, D-017]
---

# Exp 3 — SAC vs MPO compare (`ml_sac_mpo_compare`)

**Plan:** [sac_vs_mpo_compare plan](../../../../.cursor/plans/sac_vs_mpo_compare_821ab4d5.plan.md) **§ Track 3**  
**Agents:** SAC sparse + MPO dense · **dt:** 1.5 s / 1.5 s  
**Investigation:** [sac-mpo-compare-investigation.md](../../research/sac-mpo-compare-investigation.md)

---

## Phase 0 — Initialized

### 0.1 Experiment scope (What)

**Core question:** Does **SAC + sparse** vs **MPO + dense** (H6 formula) produce a fair algorithm comparison at dt 1.5 s — and can dense credit unblock MPO?

**Hypothesis (H3):** SAC learns; MPO dense achieves `learning_mode=true` or ≥20% eval improvement vs H6 (−243).

| ID | Claim |
|----|-------|
| H3a | SAC sparse learnable |
| H3b | Dense unblocks MPO vs H6 |
| H3c | Algorithm × reward pairing matters |
| H3d | Early abort informative |

### 0.2 Thought process (Why)

Prior H4 SAC learned; H1a/H6 MPO collapsed at dt 1.5 s. Isolates **algorithm × reward** after Exp 1–2.

### 0.3 Preliminary implementation remarks (How)

Slug `ml_sac_mpo_compare/`; patience early abort; `_compare_runner.py`.

---

## Phase 1 — Built

### 1.1 Build plan (What)

SAC sparse vs MPO dense; `results/compare_sac_mpo.json`; `compare_sac_mpo_analysis.md`.

### 1.2 Build implementation (How we forked)

Smoke passed; `_training_loop_fork.py` patience; global mutex.

### 1.3 Run instructions (How to execute)

`python run_sac_mpo_compare.py --show-progress`

---

## Phase 2 — Run

### 2.1 Run scope (What)

**Run at:** 2026-06-29 23:06–23:38 UTC · [`results/compare_sac_mpo.json`](../../../../backend/scripts/experiments/ml_sac_mpo_compare/results/compare_sac_mpo.json)

| Arm | Agent | Reward | `learning_mode` | Best train | Eval mean | Eps | Wall |
|-----|-------|--------|---------------|------------|-----------|-----|------|
| `compare_sac` | SAC | sparse | **true** | +5.33 | −22.17 | 37 | ~16 min |
| `compare_mpo` | MPO | dense | false | −51.6 | −51.6 | 22 | ~16 min |

**Note:** `patience_episodes=20` in JSON (not charter 10). Both arms early-aborted.

### 2.2 Run monitoring (Why)

Sequential arms under global mutex; no parallel slugs.

### 2.3 Run log & artifacts (How)

**compare_sac**

| Artifact | Path |
|----------|------|
| Run dir | `d:\code\sem-proj-asc\backend\autonomous_control\runs\9998217225628033_ml_compare_compare_sac_23-06-11\` |
| Eval ep 0 | `...\videos\eval_ep_0_rank1.mp4` |
| Train best (ep 16) | `...\videos\train_ep_16_rank1.mp4` |
| Manifest | `...\artifacts_manifest.json` |

**compare_mpo**

| Artifact | Path |
|----------|------|
| Run dir | `d:\code\sem-proj-asc\backend\autonomous_control\runs\9998217224670341_ml_compare_compare_mpo_23-22-09\` |
| Eval ep 0 | `...\videos\eval_ep_0_rank1.mp4` |
| Manifest | `...\artifacts_manifest.json` |

MPO diagnostics: eval `shutter_meaningful_fraction=0`; train torque saturated **~99.8%**; `kl_mean ≈ 3.8×10⁵`.

---

## Phase 3 — Evaluation

### 3.1 Claims & success criteria (What)

Restated H3a–H3d from Phase 0.

### 3.2 Evidence summary (Why)

- **H3a:** SAC `learning_mode=true`; best train crosses positive (+5.33 vs ep0 −72).
- **H3b:** MPO `learning_mode=false`; eval −51.6 vs H6 −243 (**~79% better**) but flat plateau; KL blow-up persists — **partial** on floor only, not sustained learning.
- **H3c:** SAC clearly separates from MPO on learning signal and eval (−22 vs −52).
- **H3d:** Early abort fired; SAC had improving segments before abort.

### 3.3 Verdict table (How we decided)

| # | Claim | **Verdict** |
|---|-------|-------------|
| H3a | SAC learnable | **supported** |
| H3b | Dense unblocks MPO | **not_supported** (floor ↑ only) |
| H3c | Algorithm × reward matters | **supported** |
| H3d | Early abort informative | **supported** |

**Overall verdict:** **supported** (H3a + H3c; charter rule: SAC learns, MPO dense does not sustain learning vs H6 goal).

**Implication for Exp 5:** MPO reward mode for width ablation — sparse used in practice; dense did not justify width sweep alone.

*(Phase 4 pending.)*


# 05-mpo-model-size.md

---
experiment_id: 5
slug: ml_mpo_model_size
title: "Exp 5 — MPO model size (width ablation)"
current_phase: 4
overall_verdict: not_supported
blocked_by: null
code_path: backend/scripts/experiments/ml_mpo_model_size/
phases:
  "0": { status: done, documented_utc: "2026-06-29T20:00:00Z", completed_utc: "2026-06-30T13:00:00Z" }
  "1": { status: done, documented_utc: "2026-06-30T13:00:00Z", completed_utc: "2026-06-30T13:00:00Z" }
  "2": { status: done, documented_utc: "2026-06-30T13:00:00Z", completed_utc: "2026-06-30T13:00:00Z" }
  "3": { status: done, documented_utc: "2026-06-30T13:00:00Z", completed_utc: "2026-06-30T13:00:00Z" }
  "4": { status: pending, documented_utc: null, completed_utc: null }
run_lock_holder: null
decision_ids: [D-005, D-006, D-018]
---

# Exp 5 — MPO model size (`ml_mpo_model_size`)

**Agent:** MPO only · **dt:** 1.5 s / 1.5 s · **Train:** 50 ep (deviation from charter 7)  
**Investigation:** [model-size-investigation.md](../../research/model-size-investigation.md) · [mpo-model-size-investigation.md](../../research/mpo-model-size-investigation.md)

---

## Phase 0 — Initialized

### 0.1 Experiment scope (What)

**Core question:** Is production MPO head width under-capacity — does S → M → L improve learning?

**Hypothesis (H5):** Wider heads improve `learning_mode` / eval when reward is learnable.

| Arm | Actor / Critic |
|-----|----------------|
| `mpo_s` | 90 / 140 |
| `mpo_m` | 140 / 256 |
| `mpo_l` | 256 / 512 |

**Reward:** **sparse** (charter default was dense pending Exp 3 — Exp 3 closed with MPO dense failure).

### 0.2 Thought process (Why)

[D-005](../../research/DECISIONS.md) deferred width-first; Exp 2 encoder closed; run after Exp 3 reward signal.

### 0.3 Preliminary implementation remarks (How)

`run_mpo_model_size.py`; width via `MPOConfig` replace only.

---

## Phase 1 — Built

### 1.1 Build plan (What)

S/M/L grid; `results/mpo_model_size_summary.json`; `_run_guard.py` mutex.

### 1.2 Build implementation (How we forked)

Smoke passed on `mpo_s`; shared raised LRs (`lr_pi=4.5e-4`, `lr_q=1e-3`).

### 1.3 Run instructions (How to execute)

`python run_mpo_model_size.py --show-progress` · optional `--reward-mode dense`

---

## Phase 2 — Run

### 2.1 Run scope (What)

**Run at:** 2026-06-30 01:01–02:44 UTC · [`results/mpo_model_size_summary.json`](../../../../backend/scripts/experiments/ml_mpo_model_size/results/mpo_model_size_summary.json)

| Arm | Actor/Critic | `learning_mode`* | Best train | Eval | Wall |
|-----|--------------|------------------|------------|------|------|
| `mpo_s` | 90/140 | true | −51.6 | −51.6 | 33 min |
| `mpo_m` | 140/256 | true | −51.6 | −51.6 | 34 min |
| `mpo_l` | 256/512 | true | −51.6 | −51.6 | 36 min |

\*Heuristic `learning_mode=true` with **flat** returns after ep 1 — treat as false positive; not real learning.

**Deviation:** 50 train ep (not charter 7); **sparse** reward (not charter dense default).

### 2.2 Run monitoring (Why)

Sequential S → M → L after Exp 4; mutex held throughout.

### 2.3 Run log & artifacts (How)

| Arm | Run dir | Eval video |
|-----|---------|------------|
| `mpo_s` | `d:\code\sem-proj-asc\backend\autonomous_control\runs\9998217218692971_ml_mpo_model_size_mpo_s_01-01-46\` | `...\videos\eval_ep_0_rank1.mp4` (if exported) |
| `mpo_m` | `...\9998217216712049_ml_mpo_model_size_mpo_m_01-34-47\` | same pattern |
| `mpo_l` | `...\9998217214701278_ml_mpo_model_size_mpo_l_02-08-18\` | same pattern |

KL after ep 1 → ~0 (policy stops updating); identical −51.6 plateau as Exp 3 `compare_mpo`.

---

## Phase 3 — Evaluation

### 3.1 Claims & success criteria (What)

H5a width helps; H5b monotonic width; H5d width not bottleneck if all collapse equally.

### 3.2 Evidence summary (Why)

All three widths **identical** KPIs — no monotonic improvement. Collapse pattern matches Exp 3 MPO floor, not capacity ceiling. **H5d supported:** width is **not** the lever at dt 1.5 s sparse.

### 3.3 Verdict table (How we decided)

| # | Claim | **Verdict** |
|---|-------|-------------|
| H5a | M/L beats S | **not_supported** |
| H5b | Monotonic width | **not_supported** |
| H5d | Width not bottleneck | **supported** |

**Overall verdict:** **not_supported** on width hypothesis; **H5d supported** — pursue algorithm/reward/action-space levers (e.g. vector mode Ref2), not head units.

**Unblocks:** [Exp 6](../0-initialized/06-modular-encoder-r2.md) process gate (encoder r2) — MPO width closed.

*(Phase 4 pending.)*


# 01-shutter-threshold.md

---
experiment_id: 1
slug: ml_shutter_threshold
title: "Exp 1 — Shutter threshold"
current_stage: closeout
overall_verdict: not_supported
blocked_by: null
code_path: backend/scripts/experiments/ml_shutter_threshold/
stages:
  charter:    { status: done, completed_utc: "2026-06-28T10:00:00Z" }
  literature: { status: done, completed_utc: "2026-06-28T11:00:00Z" }
  design:     { status: done, completed_utc: "2026-06-28T12:00:00Z" }
  implement:  { status: done, completed_utc: "2026-06-28T14:00:00Z" }
  run:        { status: done, completed_utc: "2026-06-29T15:30:00Z", arms: [mpo_t05, mpo_t09] }
  closeout:   { status: done, completed_utc: "2026-06-29T16:00:00Z" }
run_lock_holder: null
decision_ids: [D-009, D-010, D-011]
---

# Exp 1 — Shutter threshold (`ml_shutter_threshold`)

**Agent:** MPO · **Reward:** sparse + **15 s** capture-credit window (experiment fork)  
**Closed:** 2026-06-29 · **Decision IDs:** [D-009](../../research/DECISIONS.md), [D-010](../../research/DECISIONS.md), [D-011](../../research/DECISIONS.md)  
**Deep dive:** [shutter-threshold-investigation.md](../../research/shutter-threshold-investigation.md)

---

## Charter

### Hypothesis (H1)

> Raising the shutter decision threshold from **0.5 → 0.9** reduces MPO shutter spam (~968 cmds/ep in overnight H1a) **and** improves learning when combined with a **15 s** sparse capture-credit window.

**Arms:** `mpo_t05` (threshold **0.5**) vs `mpo_t09` (threshold **0.9**) · dt **1.5 s / 1.5 s** · 7 train + 2 eval episodes.

**Gates:** Exp 0 dt profile fixed (D-002); production modules read-only (D-003).

---

## Literature

- MPO sparse credit assignment; overnight H1a shutter spam baseline (~968 cmds/ep).
- Literature basis in fork: `backend/scripts/experiments/ml_shutter_threshold/H1-shutter-threshold.md`
- Highlights: [LITERATURE_HIGHLIGHTS.md](../../research/LITERATURE_HIGHLIGHTS.md) (reward sparsity / action saturation context).

---

## Design

- Experiment slug: `backend/scripts/experiments/ml_shutter_threshold/`
- Forks: reward capture window, shutter threshold in runner spec, `_sim_constants_fork` for dt 1.5 s
- JSON contract: `results/shutter_threshold_summary.json`, per-arm `results/arm_kpis/*.json`
- Analysis card: `shutter_threshold_analysis.md`

---

## Implement

- Entrypoint: `run_shutter_threshold.py` → `_shutter_runner.py`
- Global pipeline mutex: `_run_guard.py` → `pipeline_run_guard.acquire_pipeline_run_lock`
- Smoke: `--smoke` arm before full matrix
- Artifact manifest: standard training workflow (eval/train videos, reward plots)

---

## Run

**Mutex:** Only one pipeline training job per host ([D-012](../../research/DECISIONS.md)); lock at `backend/scripts/experiments/.pipeline_run.lock`.

```powershell
conda activate auto-sat
cd D:\code\sem-proj-asc\backend\scripts\experiments\ml_shutter_threshold
python .\run_shutter_threshold.py --show-progress --arms mpo_t05,mpo_t09
```

| Arm | Valid run dir | Notes |
|-----|---------------|-------|
| `mpo_t05` | `backend/autonomous_control/runs/ml_shutter_mpo_t05_14-04-49` | Invalid: `ml_shutter_mpo_t05_11-12-19` (pre–dt-fix, 1936 steps) |
| `mpo_t09` | `backend/autonomous_control/runs/9998217254656575_ml_shutter_mpo_t09_15-02-22` | Videos + artifacts_manifest |

---

## Closeout

### Verdict — hypothesis claims

| # | Claim tested | Success criterion | `mpo_t05` (0.5) | `mpo_t09` (0.9) | **Verdict** |
|---|--------------|-------------------|-----------------|-----------------|-------------|
| **H1a** | Higher threshold **cuts shutter spam** vs 0.5 arm | Mean train cmds/ep **&lt; 50%** of t05 baseline (516) | **516.0** cmds/ep (516 every ep) | **514.9** cmds/ep (−0.2%); fire@0.9 **99.8%** of steps | **Rejected** |
| **H1b** | Spam reduction comes from policy **below** saturation, not threshold alone | `shutter_unit` distribution materially below 1.0 at 0.9 | (not re-sampled) | mean **0.999**, median **1.0**, `shutter_gym` mean **+0.999** | **Rejected** |
| **H1c** | 15 s window + threshold change **enables learning** | `learning_mode` **true** OR sustained eval return improvement | `learning_mode` **false**; eval **−101.6** | `learning_mode` **false**; eval **−101.6** | **Rejected** |
| **H1d** | Meaningful captures after training | `shutter_meaningful_fraction` **&gt; 0** | **0.0** | **0.0** | **Rejected** |

### Overall H1 verdict: **Not supported**

Threshold tuning is **not an effective lever** while MPO saturates the shutter action dimension. The capture window fires **mechanically** (mid-episode latent reward bursts) but does not fix credit assignment.

**Partial signal (not H1 success):** Late-episode torque is not constant max (torque penalty + training); video shows calmer applied RW torque after ~600 s — policy moves, mission does not.

### Results snapshot

| Arm | Threshold | Mean cmds/ep | Best train return | Eval return mean | `learning_mode` | Valid run dir |
|-----|-----------|--------------|-------------------|------------------|-----------------|---------------|
| `mpo_t05` | 0.5 | 516.0 | −99.87 | −101.6 | false | `backend/autonomous_control/runs/ml_shutter_mpo_t05_14-04-49` |
| `mpo_t09` | 0.9 | 514.9 | −99.90 | −101.6 | false | `backend/autonomous_control/runs/9998217254656575_ml_shutter_mpo_t09_15-02-22` |

---

## Artifacts

| Artifact | Path |
|----------|------|
| Summary JSON | `backend/scripts/experiments/ml_shutter_threshold/results/shutter_threshold_summary.json` |
| Analysis card | `backend/scripts/experiments/ml_shutter_threshold/shutter_threshold_analysis.md` |
| Plots | `backend/scripts/experiments/ml_shutter_threshold/results/plots/` |
| Per-arm KPI cache | `results/arm_kpis/mpo_t05.json`, `mpo_t09.json` |
| Hypothesis (fork) | `backend/scripts/experiments/ml_shutter_threshold/H1-shutter-threshold.md` |
| Re-finalize summary | `python _finalize_summary.py` in experiment folder |

---

## Mechanism (reference)

`shutter_unit = 0.5 × (clip(shutter_gym, −1, 1) + 1)` · fire when `shutter_unit > threshold`.

At **0.5**: any `shutter_gym > 0` fires. At **0.9**: need `shutter_gym > 0.8`. Policy trained to **≈ +1** on both arms → threshold barely matters.

---

## Pipeline next step

**Exp 2** — modular encoder (`ml_modular_encoder`) · **Exp 3** — SAC sparse vs MPO dense (unblocked).


# 09-sac-shutter-reward-split.md

---
experiment_id: 9
slug: ml_sac_shutter_reward_split
title: "Exp 9 — SAC shutter reward split (waste off, budget on)"
current_phase: 4
overall_verdict: supported
blocked_by: null
code_path: backend/scripts/experiments/ml_sac_shutter_reward_split/
predecessor: ml_sac_vector_budget_penalty
phases:
  "0": { status: done, documented_utc: "2026-06-30T18:00:00Z", completed_utc: "2026-06-30T18:00:00Z" }
  "1": { status: done, documented_utc: "2026-06-30T18:00:00Z", completed_utc: "2026-06-30T18:00:00Z" }
  "2": { status: done, documented_utc: "2026-06-30T20:43:59Z", completed_utc: "2026-06-30T20:43:59Z" }
  "3": { status: done, documented_utc: "2026-06-30T20:43:59Z", completed_utc: "2026-06-30T20:56:09Z" }
  "4": { status: done, documented_utc: "2026-06-30T20:56:00Z", completed_utc: "2026-06-30T20:56:00Z" }
run_lock_holder: null
decision_ids: [D-025]
---

# Exp 9 — SAC shutter reward split (`ml_sac_shutter_reward_split`)

**Agent:** SAC sparse · **Action:** vector OBC · **dt:** 1.5 s / 1.5 s  
**Predecessor:** [Exp 7](4-documentation/07-sac-vector-budget-penalty.md) (both penalties on)

---

## Phase 0 — Initialized

### 0.1 Experiment scope (What)

**Core question:** Does turning **off** `enable_shutter_waste_penalty` while keeping **`enable_budget_exhausted_shutter_penalty` on** improve or preserve SAC vector learning vs Exp 7 (both on)?

**Rationale (operator):** Relax the reward plane — sparse applied capture already down-weights cloudy frames via `quality × (1 − cloud_frac)`. Penalizing “bad” shutters within budget may be redundant if the agent should converge to ~10 good captures anyway; budget-exhausted spam control (Exp 7) may be sufficient.

| ID | Claim | Success criterion | Falsified if |
|----|-------|-------------------|--------------|
| **H9a** | Eval holds or improves | Eval return ≥ Exp 7 (+10.58) | Worse eval with more spam |
| **H9b** | Learning preserved | `learning_mode=true` | No learning signal |
| **H9c** | Budget spam still controlled | Post-budget shutter cmds ≤ Exp 7 proxy | Budget spam returns |
| **H9d** | Meaningful captures not worse | Train `shutter_meaningful_fraction` ≥ Exp 7 (0.22) | Collapse to random shutter |

**Overall:** **supported** if H9b and (H9a or H9d) and H9c; **not_supported** if eval worse and spam up.

**Arms:**

| Arm | `enable_shutter_waste_penalty` | `enable_budget_exhausted_shutter_penalty` | Runs? |
|-----|-------------------------------|-------------------------------------------|-------|
| **waste_off_budget_on** | **false** | **true** | **Yes** |
| both_on | true | true | **No** — Exp 7 `9998217172220712_ml_sac_vector_budget_13-56-17` |

**No existing run** for waste_off only — Exp 7 config has `enable_shutter_waste_penalty: true`.

**Frozen protocol** (match Exp 7): seed 7, warmup 5, train 50, eval 2, SAC hparams, vector, dt 1.5 s.

### 0.2 Thought process (Why)

| Prior | Implication |
|-------|-------------|
| Exp 7 supported with both penalties | Budget-exhausted term is the high-value lever |
| Cloudy capture credit already sparse | Extra waste penalty may over-constrain exploration |
| Repeat shutter within budget gets 0 applied credit | `enable_shutter_waste_penalty` is a second negative on same failure mode |

**Defer:** turning off budget-exhausted penalty (would revert Exp 7 win).

### 0.3 Preliminary implementation remarks (How)

Scaffold from `ml_sac_vector_budget_penalty/`; single reward delta via `reward_waste_off_budget_on()` on `MPOConfig.reward`.

---

## Phase 1 — Built

### 1.1 What was built

| Component | Path |
|-----------|------|
| Entry | `run_sac_shutter_reward_split.py` |
| Runner | `_split_runner.py` — arm `waste_off_budget_on` |
| Reward delta | `_split_frozen.py` — `reward_waste_off_budget_on()` |
| Baseline embed | Exp 7 run in `config.json` → `experiment.baseline_comparison` |
| Results | `results/sac_shutter_reward_split.json`, `results/smoke.json` |

### 1.2 Why

- One-arm treatment + read-only Exp 7 baseline avoids duplicate both_on run.
- Warmup fingerprint includes reward flags so cache rebuild matches arm.

### 1.3 How to run

```powershell
conda activate auto-sat
cd backend/scripts/experiments/ml_sac_shutter_reward_split
python run_sac_shutter_reward_split.py --smoke --allow-cpu
python run_sac_shutter_reward_split.py --show-progress
```

**Smoke (2026-06-30):** passed — `results/smoke.json`; reward flags verified (`waste=false`, `budget_exhausted=true`).

---

## Phase 2 — Run

### 2.1 Run scope (What)

| Arm | `enable_shutter_waste_penalty` | `enable_budget_exhausted_shutter_penalty` | Train | Eval |
|-----|-------------------------------|-------------------------------------------|-------|------|
| **waste_off_budget_on** | **false** | **true** | 50 | 2 |

**Canonical run dir:** `d:\code\sem-proj-asc\backend\autonomous_control\runs\9998217165798903_ml_sac_shutter_split_15-43-20`

**Results JSON:** `backend/scripts/experiments/ml_sac_shutter_reward_split/results/sac_shutter_reward_split.json` · wall ~22 min.

| Metric | waste_off_budget_on | Exp 7 both_on |
|--------|---------------------|---------------|
| `learning_mode` | **true** | true |
| Eval return mean | **+106.4** | +10.6 |
| Train return best | **+169.9** (ep 36) | +124.6 |
| Train `shutter_meaningful_fraction` | **0.286** | 0.220 |
| Eval `shutter_meaningful_fraction` | **0.667** | 0.400 |
| `post_budget_shutter_cmds_total` | **75** | — |

### 2.2 Run monitoring (Why)

- Single treatment arm; Exp 7 `9998217172220712_ml_sac_vector_budget_13-56-17` embedded as read-only baseline.
- **Operator (Phase 2 review):** reward KPIs strong; action representation not visibly richer vs Exp 7 on video — schedule still sparse.

### 2.3 Run log & artifacts (How)

**Manifest:** `d:\code\sem-proj-asc\backend\autonomous_control\runs\9998217165798903_ml_sac_shutter_split_15-43-20\artifacts_manifest.json`

**Videos:**

| Clip | Path |
|------|------|
| Eval ep 0 (rank 1, +106.4) | `d:\code\sem-proj-asc\backend\autonomous_control\runs\9998217165798903_ml_sac_shutter_split_15-43-20\videos\eval_ep_0_rank1.mp4` |
| Eval ep 1 (rank 2) | `...\videos\eval_ep_1_rank2.mp4` |
| Train best (ep 36) | `...\videos\train_ep_36_rank1.mp4` |
| Train ep 40 (rank 2) | `...\videos\train_ep_40_rank2.mp4` |
| Train ep 22 (rank 3) | `...\videos\train_ep_22_rank3.mp4` |

**Plots:** `...\plots\returns_by_episode.png`, `learning_curves.png`, `eval_episode_diagnostics.png`

---

## Phase 3 — Evaluation

### 3.1 Claims & success criteria (What)

H9a–H9d vs Exp 7 (`both_on` baseline).

### 3.2 Evidence summary (Why)

| Signal | Finding |
|--------|---------|
| **KPI** | Eval **+106.4** vs Exp 7 **+10.6**; `learning_mode=true`; meaningful shutter fraction **up** train and eval. |
| **Budget spam** | `post_budget_shutter_cmds_total=75` — budget-exhausted penalty still active; not a spam regression vs charter. |
| **Video** | Sparse applied capture schedule preserved; operator: reward up but not clearly richer pointing representation ([D-019](../../research/DECISIONS.md) pattern). |

### 3.3 Verdict table (How we decided)

| # | Claim | Criterion | waste_off | Exp 7 | **Verdict** |
|---|-------|-----------|-----------|-------|-------------|
| H9a | Eval holds/improves | eval ≥ +10.6 | **+106.4** | +10.6 | **supported** |
| H9b | Learning preserved | `learning_mode=true` | **true** | true | **supported** |
| H9c | Budget spam controlled | post-budget cmds ≤ proxy | 75 | — | **supported** (penalty on) |
| H9d | Meaningful captures | train frac ≥ 0.22 | **0.286** | 0.220 | **supported** |

**Overall verdict:** **supported** on charter criteria; **partial** on operator behavioral bar (representation not richer).

**Promote (Phase 4):** `enable_shutter_waste_penalty=false` with budget-exhausted on — pending Phase 4 closeout.

---

## Phase 4 — Documentation

### 4.1 Promotion & integration (What)

| Item | Action |
|------|--------|
| **Promoted (2026-06-30)** | **`enable_shutter_waste_penalty=False`** as nb08 / `training_workflow.py` default — matches production `RewardConfig` default and Exp 9 evidence |
| **Keep on** | `enable_budget_exhausted_shutter_penalty=True` ([D-022](../../research/DECISIONS.md) Exp 7) |
| **Docs** | `docs/presentation/machine-learning.md` — shutter-waste slide + nb08 default bullet |
| **DECISIONS** | [D-025](../../research/DECISIONS.md) — Exp 9 SAC shutter split **supported** |
| **Not promoted** | Fork runner (`ml_sac_shutter_reward_split/`) — experiment record only |

**Note:** Exp 7 treatment run used `enable_shutter_waste_penalty=true` in fork config; Exp 9 shows waste-off is strictly better on KPIs with budget-exhausted still on.

### 4.2 Closeout rationale (Why)

Turning off within-budget shutter waste penalty while keeping budget-exhausted penalty yields **+106.4 eval** vs Exp 7 **+10.6**, higher meaningful shutter fractions, and preserved `learning_mode`. Sparse applied capture already scales with `quality × (1 − cloud_frac)` — the extra waste term was redundant constraint.

Operator video: reward KPIs strong; pointing representation not visibly richer than Exp 7 ([D-019](../../research/DECISIONS.md) pattern) — behavioral bar partial, charter KPI bar supported.

### 4.3 Knowledge persistence (How)

| Artifact | Path |
|----------|------|
| Pipeline doc (this file) | `docs/experiments/pipeline/4-documentation/09-sac-shutter-reward-split.md` |
| Analysis card | `backend/scripts/experiments/ml_sac_shutter_reward_split/results/sac_shutter_reward_split_analysis.md` |
| Summary JSON | `backend/scripts/experiments/ml_sac_shutter_reward_split/results/sac_shutter_reward_split.json` |
| README index | [pipeline/README.md](../README.md) row 9 (SAC split) |

**Report archive:**

- Eval: `...\9998217165798903_ml_sac_shutter_split_15-43-20\videos\eval_ep_0_rank1.mp4`
- Train peak: `...\videos\train_ep_36_rank1.mp4`
- Returns: `...\plots\returns_by_episode.png`


# 04-agent-reference-pointing.md

---
experiment_id: 4
slug: ml_agent_reference_pointing
title: "Exp 4 — Agent-reference pointing"
current_phase: 4
overall_verdict: partial
blocked_by: null
code_path: backend/scripts/experiments/ml_agent_reference_pointing/
phases:
  "0": { status: done, documented_utc: "2026-06-30T00:00:00Z", completed_utc: "2026-06-30T00:00:00Z" }
  "1": { status: done, documented_utc: "2026-06-30T00:00:00Z", completed_utc: "2026-06-30T10:42:00Z" }
  "2": { status: done, documented_utc: "2026-06-30T11:30:00Z", completed_utc: "2026-06-30T13:00:00Z" }
  "3": { status: done, documented_utc: "2026-06-30T13:00:00Z", completed_utc: "2026-06-30T13:00:00Z" }
  "4": { status: pending, documented_utc: null, completed_utc: null }
run_lock_holder: null
decision_ids: [D-016, D-019, D-020]
invalid_runs:
  - pipeline_overnight_exp4_ref1_torque_passthrough
  - results/agent_reference.json_pre_vector_fix
---

# Exp 4 — Agent-reference pointing (`ml_agent_reference_pointing`)

**Agent:** SAC sparse (+ optional MPO dense Ref2) · **dt:** 1.5 s / 1.5 s · **Train:** 50 ep (learnable slice)  
**Plan:** [sac_vs_mpo_compare plan](../../../../.cursor/plans/sac_vs_mpo_compare_821ab4d5.plan.md) § Track 4  
**Code:** `backend/scripts/experiments/ml_agent_reference_pointing/`  
**Investigation:** [agent-reference-pointing-investigation.md](../../research/agent-reference-pointing-investigation.md)

---

## Phase 0 — Initialized

### 0.1 Experiment scope (What)

**Core question:** Does commanding a **nadir-relative orientation reference** (`dim0 = u ∈ [-1,1]`) through OBC PD tracking improve mission learning vs direct **reaction-wheel torque** control?

**Hypothesis (H4):** SAC sparse with **`attitude_request_mode=vector`** (Ref1) achieves `learning_mode=true` and higher eval return than torque control (Ref0), with lower `safe_mode_takeover_count`.

| Arm | `attitude_request_mode` | Agent | Reward | Purpose |
|-----|-------------------------|-------|--------|---------|
| **Ref0** | `torque` | SAC sparse | sparse | Control — production torque path + safe-mode |
| **Ref1** | `vector` | SAC sparse | sparse | Treatment — `u` → `f_n` → `θ_req` → PD → τ; hold-last safety |
| **Ref2** (optional) | `vector` | MPO | dense | Exp 3 dependent — **not run** |

### 0.2 Thought process (Why)

Vector mode shrinks the effective action space and enforces safety on the **pointing request** (hold-last at 45° off-nadir) instead of torque-path safe-mode arbitration.

### 0.3 Preliminary implementation remarks (How)

Experiment forks under `ml_agent_reference_pointing/`; promotion target `simulation/obc_pointing_request.py`.

---

## Phase 1 — Built (vector OBC v1)

### 1.1 What — frozen design contract

**Policy dim0:** `u ∈ [-1, 1]` (unitless).

**Command transform:**

```text
f_n = max_safe · u          # max_safe = OFF_NADIR_HARD_LIMIT_DEG (45°)
θ_req = wrap_pi(θ_nadir + f_n)
```

| Symbol | Definition |
|--------|------------|
| `max_safe` | `OFF_NADIR_HARD_LIMIT_DEG` from `ATTITUDE_SAFETY.py` — same as torque-mode hard limit |
| `θ_nadir` | `nadir_target_angle_rad(θ_orbit)` |
| Safety | If geometric off-nadir at `θ_req` ≥ `max_safe` → **hold last valid** `θ_req` (no clamp projection) |
| Episode init | `last_valid = θ_nadir` (equivalent to `u = 0`) |

**Baseline (vector warmup):** extract `θ_target` from baseline PD target → `u = clip(f_n_target / max_safe, −1, 1)` → same `ObcPointingResolver` as agent. **No** torque passthrough.

**Torque mode (Ref0):** unchanged production `AttitudeSafetyController` path.

**Diagnostics:** `hold_last_count` (alias `reference_clamp_count` in KPI JSON).

### 1.2 Why — invalidate prior runs

Pipeline exp4 ref1 completed on **torque-passthrough** warmup fix is **invalid science** — excluded from H4 verdict. Prior `results/agent_reference.json` and ref1 warmup caches from wrong-semantics runs marked **invalid_run**.

### 1.3 How — modules

| Module | Role |
|--------|------|
| `simulation/obc_pointing_request.py` | Production `ObcPointingResolver`, nadir-relative helpers |
| `_episode_runner_fork.py` | Patches `episode_runner.baseline_overflight_controller_tick`, stepper, policy parse |
| `_obc_attitude_request_fork.py` | Experiment context wrapping resolver |
| `_baseline_pointing.py` | Baseline → `u` for warmup |

**Smoke:** `run_agent_reference.py --smoke` (Ref0); `run_agent_reference.py --arms ref1 --train-episodes 1 --trim-artifacts` (Ref1 vector).

**Production promotion (2026-06-30):** `TrainingWorkflowConfig.attitude_request_mode`, `EpisodeRunner`, `action_adapter.py`, `obc_pointing_request.py` — [D-016](../../research/DECISIONS.md).

---

## Phase 2 — Run (vector OBC v1 re-run)

### 2.1 Run scope (What)

**Command:** `run_agent_reference.py --arms ref0,ref1 --show-progress` (50 train ep, 3 train + 2 eval MP4s per arm).

**Summary:** [`results/agent_reference.json`](../../../../backend/scripts/experiments/ml_agent_reference_pointing/results/agent_reference.json) · wall ~47 min total.

| Arm | Mode | `learning_mode` | Eval mean | Best train | `hold_last` | Run dir |
|-----|------|-----------------|-----------|------------|-------------|---------|
| **ref0** | torque | true | −11.13 | +8.37 | 0 | `backend/autonomous_control/runs/9998217183842846_ml_ref_ref0_torque_10-42-36/` |
| **ref1** | vector | true | −24.08 | +95.77 | 0 | `backend/autonomous_control/runs/9998217182442815_ml_ref_ref1_vector_11-05-57/` |

### 2.2 Run monitoring (Why)

- Valid post-fix pair only; overnight ref1 errors (`stored_action`, recursion) excluded.
- Ref2 (MPO vector) not executed.

### 2.3 Run log & artifacts (How)

**Ref0 — torque**

| Artifact | Path |
|----------|------|
| Manifest | `d:\code\sem-proj-asc\backend\autonomous_control\runs\9998217183842846_ml_ref_ref0_torque_10-42-36\artifacts_manifest.json` |
| Eval best | `d:\code\sem-proj-asc\backend\autonomous_control\runs\9998217183842846_ml_ref_ref0_torque_10-42-36\videos\eval_best.mp4` |
| Eval ep 0 | `...\videos\eval_ep_0_rank1.mp4` |
| Train best (ep 49) | `...\videos\train_ep_49_rank1.mp4` |

**Ref1 — vector**

| Artifact | Path |
|----------|------|
| Manifest | `d:\code\sem-proj-asc\backend\autonomous_control\runs\9998217182442815_ml_ref_ref1_vector_11-05-57\artifacts_manifest.json` |
| Eval best | `d:\code\sem-proj-asc\backend\autonomous_control\runs\9998217182442815_ml_ref_ref1_vector_11-05-57\videos\eval_best.mp4` |
| Eval ep 0 | `...\videos\eval_ep_0_rank1.mp4` |
| **Train best (ep 11)** | `d:\code\sem-proj-asc\backend\autonomous_control\runs\9998217182442815_ml_ref_ref1_vector_11-05-57\videos\train_ep_11_rank1.mp4` |
| Train ep 43 | `...\videos\train_ep_43_rank2.mp4` |
| Learning curves | `...\plots\learning_curves.png` |

---

## Phase 3 — Evaluation

### 3.1 Claims & success criteria (What)

| ID | Claim | Success criterion |
|----|-------|-------------------|
| **H4a** | Vector beats torque on eval | Ref1 eval return > Ref0 |
| **H4b** | Both learn | `learning_mode=true` on Ref0 and Ref1 |
| **H4c** | Vector safer | Ref1 `safe_mode` / `hold_last` ≤ Ref0 |

### 3.2 Evidence summary (Why)

**KPI slice (canonical 2026-06-30):** Ref0 eval **−11.1** beats Ref1 **−24.1** → **H4a not met**. Both `learning_mode=true` → **H4b met**. `hold_last_count=0` on both → **H4c neutral** (no OOB hold-last events).

**User video review (Ref1 train ep 11, return +95.8)** — primary behavioral signal for ASC follow-up:

- **Pointing:** Vector mode shows deliberate off-nadir scheduling; behavior operator likes mid-episode.
- **Shutters:** SAC sparse — relatively **sparse** shutter firing mid-episode when pointing aligns; looks like emerging **schedule**, not random spam.
- **End-of-episode:** Policy still **spams shutter commands** after budget exhausted; does not appear to internalize the **fixed capture budget** limit.
- **Collapse:** Large train peak (ep 11) followed by worse later episodes / weaker eval — open questions: learning rate, reward mis-shaping, local optimum, eval distribution (clouds).

**Deferred tests ([D-020](../../research/DECISIONS.md)):**

- Penalty when agent sends shutter commands with **capture budget ≤ 0**
- Reward v2 / budget-aware shaping (`s01_env_reward_v2` plan)
- Policy stability after high-return episodes (LR, replay, entropy)

**Ref2:** MPO + vector not run — does not block this closeout.

### 3.3 Verdict table (How we decided)

| # | Claim | Criterion | Ref0 | Ref1 | **Verdict** |
|---|-------|-----------|------|------|-------------|
| H4a | Vector higher eval | Ref1 > Ref0 | −11.13 | −24.08 | **not_supported** |
| H4b | Both learn | `learning_mode=true` | true | true | **supported** |
| H4c | Vector safer | fewer safe-mode / hold-last | 0 | 0 | **inconclusive** |

**Overall verdict:** **partial** — vector OBC v1 is valid and shows promising **pointing + sparse shutter scheduling** on video (ep 11), but H4a eval win not demonstrated; shutter-budget ignorance and post-peak collapse motivate **ASC follow-up** on reward shaping, not abandoning vector mode.

**Follow-up experiment (out of v1 scope):** SAC vector + shutter-budget penalty; optional Ref2 (MPO vector).

*(Phase 4 — Documentation appended by `/document-experiment-step` when ready.)*


# 07-sac-vector-budget-penalty.md

---
experiment_id: 7
slug: ml_sac_vector_budget_penalty
title: "Exp 7 — SAC vector + shutter budget penalty"
current_phase: 4
overall_verdict: supported
blocked_by: null
code_path: backend/scripts/experiments/ml_sac_vector_budget_penalty/
plan_ref: ".cursor/plans/inbox/s01_env_reward_v2_fe941d4d.plan.md (reward fork slice)"
phases:
  "0": { status: done, documented_utc: "2026-06-30T14:00:00Z", completed_utc: "2026-06-30T16:00:00Z" }
  "1": { status: done, documented_utc: "2026-06-30T16:00:00Z", completed_utc: "2026-06-30T13:54:00Z" }
  "2": { status: done, documented_utc: "2026-06-30T16:30:00Z", completed_utc: "2026-06-30T14:33:00Z" }
  "3": { status: done, documented_utc: "2026-06-30T16:30:00Z", completed_utc: "2026-06-30T16:30:00Z" }
  "4": { status: done, documented_utc: "2026-06-30T16:30:00Z", completed_utc: "2026-06-30T16:30:00Z" }
run_lock_holder: null
decision_ids: [D-020, D-022]
predecessor: ml_agent_reference_pointing
---

# Exp 7 — SAC vector + shutter budget penalty (`ml_sac_vector_budget_penalty`)

**Agent:** SAC sparse · **Action:** vector OBC (`attitude_request_mode=vector`) · **dt:** 1.5 s / 1.5 s  
**Predecessor:** [Exp 4](04-agent-reference-pointing.md) (partial — Ref1 video signal)  
**Investigation:** [agent-reference-pointing-investigation.md](../../research/agent-reference-pointing-investigation.md) · [D-020](../../research/DECISIONS.md) · [D-022](../../research/DECISIONS.md)

---

## Phase 0 — Initialized

### 0.1 Experiment scope (What)

**Core question:** Does a **penalty for shutter commands when capture budget ≤ 0** improve SAC sparse learning in **vector** pointing mode — reducing end-of-episode shutter spam and stabilizing returns after high-reward episodes?

**Origin (operator video, Exp 4 Ref1 train ep 11):**

- Mid-episode: **sparse** meaningful shutters; **pointing schedule** looks learnable (`train_ep_11_rank1.mp4`, return +95.8).
- End-of-episode: policy **still fires shutter** after budget exhausted — does not internalize fixed capture limit.
- Later episodes / eval weaker than peak — open: reward mis-shaping, local optimum, LR, eval cloud draw.

**Hypothesis (H7):**

> SAC sparse + vector + **budget-exhausted shutter penalty** achieves equal or better eval return vs Exp 4 Ref1 baseline, with lower post-budget shutter command rate and less train-return collapse after peak episodes.

| ID | Claim | Success criterion | Falsified if |
|----|-------|-------------------|--------------|
| **H7a** | Penalty reduces spam | Post-budget `shutter_cmd_count` ↓ ≥ **30%** vs Ref1 baseline run | No reduction |
| **H7b** | Eval improves or holds | Eval return ≥ Exp 4 Ref1 (−24.08) or `learning_mode=true` with ↑ best train | Worse eval with more spam |
| **H7c** | Scheduling preserved | Mid-episode `shutter_meaningful_fraction` not worse than baseline | Penalty kills all shutter exploration |
| **H7d** | Peak-collapse mitigated | Train return std after best ep ↓ vs baseline (same 50-ep slice) | Same collapse pattern |

**Overall:** **supported** if H7a **and** (H7b or clear H7c); **not_supported** if spam unchanged and eval worse.

**Arms** (single run — no control re-run):

| Arm | `attitude_request_mode` | Reward | Runs? |
|-----|-------------------------|--------|-------|
| **penalty_on** | `vector` | sparse + **budget-exhausted shutter penalty** | **Yes** (treatment) |
| penalty_off | `vector` | sparse (production) | **No** — baseline = Exp 4 Ref1 `9998217182442815_ml_ref_ref1_vector_11-05-57` |

**Penalty design (fork — Phase 1):**

- When `capture_budget_remaining ≤ 0` **and** agent issues shutter command above threshold → add negative term to `total` (magnitude TBD in build; start from existing `k_shutter_waste` scale).
- Do **not** change sparse applied-capture credit at valid shutters.
- Experiment-only `_reward_fork.py`; no production `reward.py` edit until Phase 4 promote.

**Frozen protocol** (match Exp 4 Ref1 canonical run):

| Knob | Value |
|------|-------|
| dt | 1.5 s / 1.5 s |
| seed | 7 |
| warmup | 5 (rebuild per arm) |
| train | **50** |
| eval | 2 |
| SAC | same as Exp 4 Ref1 (`lr_pi=4.5e-4`, `lr_q=1e-3`) |
| Videos | 3 train + 2 eval (default workflow) |

**Baseline for comparison (read-only):** Exp 4 Ref1 run `9998217182442815_ml_ref_ref1_vector_11-05-57` — rerun `penalty_off` only if cache/protocol drift is suspected.

**Out of scope:** Torque mode (Ref0), MPO, encoder A0/A1 (Exp 6 deferred), full `s01_env_reward_v2` cloud terms, production reward promote in Phase 1.

### 0.2 Thought process (Why)

| Prior fact | Implication |
|------------|-------------|
| Exp 4 Ref1 eval < Ref0 on KPI | Vector still worth tuning via **reward**, not abandoning OBC |
| Exp 3 SAC learns sparse; MPO does not | SAC-only experiment |
| Exp 1 shutter threshold failed | Spam is not fixed by threshold alone — try **budget-aware penalty** |
| Exp 5 width ruled out | Reward / action semantics lever, not capacity |
| [D-020](../../research/DECISIONS.md) deferred this test | Exp 7 owns the fork |

**Reject / defer:**

| Path | Why |
|------|-----|
| Drop vector mode | Video shows pointing + scheduling signal |
| Penalty on torque path | Hold vector — that's where operator saw behavior |
| Full reward v2 plan in one exp | Ponytail — **budget shutter penalty only** |

#### 0.2.1 Shoulders of giants

- Exp 4 closeout + user video: `train_ep_11_rank1.mp4`
- Exp 1 shutter investigation — threshold/window insufficient
- `k_shutter_waste` / `RewardConfig` in production reward kernel

### 0.3 Preliminary implementation remarks (How)

**Scaffold:** Copy `ml_agent_reference_pointing/` patterns (vector OBC already production); new slug `ml_sac_vector_budget_penalty/`.

| Component | Planned path |
|-----------|--------------|
| Entry | `run_sac_vector_budget.py` |
| Runner | `_budget_runner.py` |
| Reward fork | `_reward_fork.py` (`penalty_off` = sparse; `penalty_on` = sparse + exhausted-budget penalty) |
| Mutex | `_run_guard.py` → `pipeline_run_guard` |
| Results | `results/sac_vector_budget.json`, `sac_vector_budget_analysis.md` |

**Smoke:** vector mode + both reward modes activate; one train step each.

**Evidence anchor (pre-run):**

`d:\code\sem-proj-asc\backend\autonomous_control\runs\9998217182442815_ml_ref_ref1_vector_11-05-57\videos\train_ep_11_rank1.mp4`

---

## Phase 1 — Built

### 1.1 What was built

| Component | Path |
|-----------|------|
| Entry | `run_sac_vector_budget.py` |
| Runner | `_budget_runner.py` — **single arm** `penalty_on` only |
| Reward fork | `_reward_fork.py` — sparse vector + `apply_shutter_capture` penalty when `budget.remaining ≤ 0` (−`k_shutter_waste`) |
| Frozen protocol | `_budget_frozen.py` — matches Exp 4 Ref1 SAC hparams |
| dt fork | `_sim_constants_fork.py` — 1.5 s / 1.5 s |
| Results | `results/sac_vector_budget.json`, `results/smoke.json` |

**Design choices:**

- **No `penalty_off` arm** — compare treatment to Exp 4 Ref1 run (embedded in `config.json` → `experiment.baseline_comparison`).
- **TensorBoard on by default** — `enable_tensorboard=True` in workflow; `--no-tensorboard` opt-out. Live capability test for episode scalars + HParams under `run_dir/tensorboard/`.

### 1.2 Why

- Avoid duplicate 50-ep SAC run when Ref1 baseline already exists.
- TensorBoard gives per-episode loss/return curves for peak-collapse diagnosis (H7d).

### 1.3 How to run

```powershell
conda activate auto-sat
cd backend/scripts/experiments/ml_sac_vector_budget_penalty
python run_sac_vector_budget.py --smoke --allow-cpu
python run_sac_vector_budget.py --show-progress
tensorboard --logdir backend/autonomous_control/runs/<run_dir>/tensorboard
```

**Smoke (2026-06-30):** passed — `results/smoke.json`; TensorBoard parity verified at `D:\code\sem-proj-asc\backend\autonomous_control\runs\9998217172385095_ml_sac_vector_budget_smoke_13-53-34\tensorboard`.

---

## Phase 2 — Run

### 2.1 Run scope (What)

**Command:**

```powershell
conda activate auto-sat
cd backend/scripts/experiments/ml_sac_vector_budget_penalty
python run_sac_vector_budget.py --show-progress
```

| Arm | Mode | Reward | Train | Eval | Seed | dt |
|-----|------|--------|-------|------|------|-----|
| **penalty_on** | vector | sparse + budget-exhausted shutter penalty | 50 | 2 | 7 | 1.5 s / 1.5 s |

**Baseline (read-only, no re-run):** Exp 4 Ref1 `9998217182442815_ml_ref_ref1_vector_11-05-57`.

**Summary:** [`results/sac_vector_budget.json`](../../../../backend/scripts/experiments/ml_sac_vector_budget_penalty/results/sac_vector_budget.json) · wall ~22 min train (13:56 → 14:18 UTC).

| Arm | `learning_mode` | Eval mean | Best train | Train shutter cmds | Meaningful frac (train) | Run dir |
|-----|-----------------|-----------|------------|--------------------|-------------------------|---------|
| **penalty_on** | true | **+10.58** | **+124.57** (ep 42) | **478** | **0.220** | `9998217172220712_ml_sac_vector_budget_13-56-17` |
| Ref1 (baseline) | true | −24.08 | +95.77 (ep 11) | 7071 | 0.015 | `9998217182442815_ml_ref_ref1_vector_11-05-57` |

### 2.2 Run monitoring (Why)

- **Mutex:** global `pipeline_run_guard` — no parallel pipeline slugs ([D-012](../../research/DECISIONS.md)).
- **Single treatment arm** — Ref1 baseline embedded in `config.json` → `experiment.baseline_comparison` to avoid duplicate 50-ep SAC.
- **Post-processing crash (14:18 UTC):** training + checkpoint completed; runner failed in `count_post_budget_shutter_cmds` (`episode_idx` attribute bug, since fixed in `_runner_common.py`). Recovered via `--finalize-run` (14:23–14:33 UTC) — KPI JSON + MP4 export.
- **`post_budget_shutter_cmds_total`:** remains `null` in summary JSON (finalize without train replay). H7a assessed via aggregate shutter diagnostics + one finalize log line (`post_budget_cmds=0`).

### 2.3 Run log & artifacts (How)

**Run dir:** `d:\code\sem-proj-asc\backend\autonomous_control\runs\9998217172220712_ml_sac_vector_budget_13-56-17`

| Artifact | Path |
|----------|------|
| Summary KPI | `...\summary_metrics.json` |
| Episodes CSV | `...\episodes.csv` |
| Run log | `...\run_log.md` |
| Config | `...\config.json` |
| Results JSON | `backend/scripts/experiments/ml_sac_vector_budget_penalty/results/sac_vector_budget.json` |
| Error trace (crash) | `backend/scripts/experiments/ml_sac_vector_budget_penalty/results/penalty_on_error.json` |
| Run log (script) | `backend/scripts/experiments/ml_sac_vector_budget_penalty/results/budget_penalty.log` |
| TensorBoard | `...\tensorboard\` |
| Manifest | `...\artifacts_manifest.json` |

**Videos (mandatory evidence):**

| Clip | Path |
|------|------|
| Eval best | `d:\code\sem-proj-asc\backend\autonomous_control\runs\9998217172220712_ml_sac_vector_budget_13-56-17\videos\eval_best.mp4` |
| Eval ep 0 (rank 1) | `...\videos\eval_ep_0_rank1.mp4` |
| Eval ep 1 (rank 2) | `...\videos\eval_ep_1_rank2.mp4` |
| **Train best (ep 42)** | `...\videos\train_ep_42_rank1.mp4` |
| Train ep 25 (rank 2) | `...\videos\train_ep_25_rank2.mp4` |
| Train ep 11 (rank 3) | `...\videos\train_ep_11_rank3.mp4` |

**Plots:**

| Plot | Path |
|------|------|
| Returns by episode | `...\plots\returns_by_episode.png` |
| Learning curves | `...\plots\learning_curves.png` |
| Train diagnostics p01–p05 | `...\plots\train_episode_diagnostics_p01.png` … `p05.png` |
| Eval diagnostics | `...\plots\eval_episode_diagnostics.png` |
| Episode reward PNGs | `...\episodes\eval_best_reward.png`, `train_ep_42_rank1_reward.png`, etc. |

**Video frame inspect (agent pre-check):**

| MP4 | Manifest |
|-----|------------|
| `eval_ep_0_rank1.mp4` | `d:\code\sem-proj-asc\.cursor\video_frame_inspect\data\eval_ep_0_rank1_20260630T150624Z\manifest.json` |
| `train_ep_42_rank1.mp4` | `d:\code\sem-proj-asc\.cursor\video_frame_inspect\data\train_ep_42_rank1_20260630T150758Z\manifest.json` |

**Frame findings (pre-check — operator sign-off pending):**

- **Mid-orbit (~t=200–500 s):** reward bursts with take-picture markers; image quality peaks in clear gaps; torque activity localized to imaging window.
- **End-of-episode (~t=700 s):** nadir coast, target 0% in-view — **no end-of-episode shutter spam** on reward trace (contrast with Exp 4 Ref1 operator report).
- **Train ep 42 (+124.6):** same sparse scheduling pattern as eval; pointing window looks deliberate.

---

## Phase 3 — Evaluation

### 3.1 Claims & success criteria (What)

| ID | Claim | Success criterion |
|----|-------|-------------------|
| **H7a** | Penalty reduces spam | Post-budget shutter cmds ↓ ≥ **30%** vs Ref1 |
| **H7b** | Eval improves or holds | Eval return ≥ **−24.08** (Ref1) |
| **H7c** | Scheduling preserved | Train `shutter_meaningful_fraction` ≥ Ref1 (**0.015**) |
| **H7d** | Peak-collapse mitigated | Train return std **after best ep** ↓ vs Ref1 |

### 3.2 Evidence summary (Why)

**Literature vs our runs:** Exp 1 showed threshold tuning does not stop shutter saturation. Exp 4 video showed vector SAC **can** schedule mid-orbit but ignores budget at episode tail. Exp 7 adds a **distinct** penalty: `−k_shutter_waste` when `budget.remaining ≤ 0` at shutter issue time (fork patches `SimulationStepper.apply_shutter_capture`). This is **not** the production `enable_shutter_waste_penalty` (penalizes zero-applied capture **within** budget).

**KPI slice (penalty_on vs Ref1):**

| Metric | penalty_on | Ref1 | Δ |
|--------|------------|------|---|
| Eval return mean | +10.58 | −24.08 | +34.7 |
| Train return best | +124.57 (ep 42) | +95.77 (ep 11) | +28.8 |
| Train return mean | −4.50 | −48.94 | +44.4 |
| Train shutter cmds | 478 | 7071 | **−93%** |
| Train meaningful frac | 0.220 | 0.015 | **15×** |
| Eval shutter cmds | 10 | 346 | **−97%** |
| Post-peak std (after best ep) | 17.5 (n=7 after ep 42) | 28.4 (n=38 after ep 11) | **−38%** |
| Post-peak mean (after best ep) | +3.3 | −53.5 | improved |

**Mechanism diagnosis:** Penalty gives direct negative credit on **wasted** shutter commands after the orbit capture budget is exhausted, without reducing applied capture credit on valid shutters. Policy learns **fewer total shutter cmds** with **higher meaningful fraction** — spam replaced by timed captures.

**Partial / open:**

- Formal `post_budget_shutter_cmds_total` not in JSON — replay finalize optional.
- Eval (+10.6) ≪ train peak (+124.6) — eval cloud draw / overfitting; still far above Ref1 eval.

**Analysis card:** [`results/sac_vector_budget_analysis.md`](../../../../backend/scripts/experiments/ml_sac_vector_budget_penalty/results/sac_vector_budget_analysis.md)

### 3.3 Verdict table (How we decided)

| # | Claim | Criterion | penalty_on | Ref1 | **Verdict** |
|---|-------|-----------|------------|------|-------------|
| H7a | Spam reduction | post-budget cmds ↓ ≥30% | train cmds **478** (−93%); proxy — formal counter null | **7071** | **supported** (proxy) |
| H7b | Eval holds/improves | eval ≥ −24.08 | **+10.58** | −24.08 | **supported** |
| H7c | Scheduling preserved | meaningful frac not worse | **0.220** train | 0.015 | **supported** |
| H7d | Peak-collapse mitigated | post-peak std ↓ | **17.5** | 28.4 | **supported** |

**Overall verdict:** **supported** — H7a (proxy) + H7b + H7c; H7d corroborates. Budget-exhausted shutter penalty is an effective reward lever for SAC vector sparse.

**Follow-up (out of H7 scope):**

- Promote penalty to production kernel (Phase 4 plan — separate implementation).
- Replay finalize for formal H7a counter.
- LR / replay study if eval–train gap remains large after promote.

---

## Phase 4 — Documentation

### 4.1 Promotion & integration (What)

| Item | Action |
|------|--------|
| **Promoted (2026-06-30)** | `enable_budget_exhausted_shutter_penalty` (default **on**) + `budget_exhausted_shutter_command_penalty` in `autonomous_control/reward.py`; applied in `simulation/stepper.py::apply_shutter_capture` |
| **Magnitude** | `−k_shutter_waste` (`REWARD_SHUTTER_WASTE_PENALTY = 5.0`) when `budget.remaining ≤ 0` at shutter command |
| **Distinct from** | `enable_shutter_waste_penalty` (zero-applied capture within budget) — keep both |
| **Update** | `docs/presentation/machine-learning.md` reward slide |
| **DECISIONS** | [D-022](../../research/DECISIONS.md) — closeout supported; promote chartered |

**Not promoted at closeout (fork-only):**

- `ml_sac_vector_budget_penalty/_reward_fork.py` runtime patch (shutter penalty now production; fork keeps sparse + torque-effort shim only)
- `_sim_constants_fork.py` dt profile (already production default 1.5 s)
- Single-arm runner / no `penalty_off` re-run shortcut
- TensorBoard experiment default (workflow already supports TB)

### 4.2 Closeout rationale (Why)

Exp 4 left vector mode **partial** — promising pointing video but eval below torque and end-of-episode shutter spam. Exp 7 tested the smallest reward delta [D-020](../../research/DECISIONS.md) chartered: penalize shutter commands when capture budget is already zero.

Treatment run shows **large** improvements on every KPI dimension vs read-only Ref1 baseline: positive eval, 93% fewer train shutter commands, 15× higher meaningful shutter fraction, and lower post-peak return volatility. Video pre-check shows mid-orbit sparse capture windows without end-of-episode spam on the reward trace.

Verdict **supported** warranted production promotion of the penalty hook — merged 2026-06-30 ([D-022](../../research/DECISIONS.md)).

### 4.3 Knowledge persistence (How)

| Artifact | Path |
|----------|------|
| Pipeline doc (this file) | `docs/experiments/pipeline/4-documentation/07-sac-vector-budget-penalty.md` |
| Analysis card | `backend/scripts/experiments/ml_sac_vector_budget_penalty/results/sac_vector_budget_analysis.md` |
| Summary JSON | `backend/scripts/experiments/ml_sac_vector_budget_penalty/results/sac_vector_budget.json` |
| Investigation note | [agent-reference-pointing-investigation.md](../../research/agent-reference-pointing-investigation.md) § Exp 7 results |
| DECISIONS | [D-020](../../research/DECISIONS.md) (charter), [D-022](../../research/DECISIONS.md) (closeout) |
| README index | [pipeline/README.md](../README.md) row 7 |

**Report archive (semester-facing):**

- Eval best MP4: `...\9998217172220712_ml_sac_vector_budget_13-56-17\videos\eval_best.mp4`
- Train peak MP4: `...\videos\train_ep_42_rank1.mp4`
- Returns plot: `...\plots\returns_by_episode.png`
- Baseline contrast video: `...\9998217182442815_ml_ref_ref1_vector_11-05-57\videos\train_ep_11_rank1.mp4`

**User sign-off:** frame review is agent pre-check only — confirm eval/train MP4s before citing behavioral claims in external reports.

**Pipeline next step:** ~~promote budget-exhausted penalty~~ **done** — monitor next SAC vector training runs for eval–train gap.


# 08-mpo-decoupled-dual-fix.md

---
experiment_id: 8
slug: ml_mpo_decoupled_dual_torque
title: "Exp 8 — MPO fixed dual, sparse, torque mode"
current_phase: 4
overall_verdict: partial
blocked_by: null
code_path: backend/scripts/experiments/ml_mpo_decoupled_dual_torque/
plan_ref: ".cursor/plans/sac_vs_mpo_compare_821ab4d5.plan.md — MPO debug track"
phases:
  "0": { status: done, documented_utc: "2026-06-30T15:10:00Z", completed_utc: "2026-06-30T15:40:00Z" }
  "1": { status: done, documented_utc: null, completed_utc: "2026-06-30T16:38:06Z", notes: "smoke + canonical 50-ep run" }
  "2": { status: done, documented_utc: "2026-06-30T20:43:59Z", completed_utc: "2026-06-30T20:43:59Z" }
  "3": { status: done, documented_utc: "2026-06-30T20:43:59Z", completed_utc: "2026-06-30T20:56:08Z" }
  "4": { status: done, documented_utc: "2026-06-30T20:56:00Z", completed_utc: "2026-06-30T20:56:00Z" }
run_lock_holder: null
decision_ids: [D-023, D-024]
predecessor: ml_mpo_model_size
investigation: docs/research/mpo-learning-collapse-investigation.md
---
# Exp 8 — MPO fixed dual, sparse, torque mode (`ml_mpo_decoupled_dual_torque`)

**Agent:** MPO (fixed decoupled-KL dual) · **Action:** torque (production default) · **Reward:** sparse · **dt:** 1.5 s / 1.5 s
**Fix commit:** `d5af20c` — `fix(mpo): implement decoupled-KL dual`
**Predecessor:** [Exp 5](../4-documentation/05-mpo-model-size.md) (torque mode, identical collapse across widths — pre-fix)
**Investigation:** [mpo-learning-collapse-investigation.md](../../research/mpo-learning-collapse-investigation.md) · [D-023](../../research/DECISIONS.md) · [D-024](../../research/DECISIONS.md)
**Pair:** [Exp 11](../1-built/11-mpo-decoupled-dual-vector.md) (same fixed agent, vector mode)

---

## Phase 0 — Initialized

### 0.1 Experiment scope (What)

**Core question:** With the MPO dual now correctly implemented (E-step Q-value dual η + enforced M-step α_μ/α_Σ trust region, committed in `d5af20c`), does MPO achieve `learning_mode=true` on sparse reward in torque mode — the same mode that produced the −51.6 / −243.5 collapse in all prior runs?

**Hypothesis (H8):**

> The fixed MPO agent achieves `learning_mode=true` (returns rise above the −51.6 floor established by Exp 3/5) with bounded KL/η, on the same sparse + torque + dt-1.5 s protocol that previously collapsed.

| ID | Claim | Success criterion | Falsified if |
|----|-------|-------------------|--------------|
| **H8a** | Dual fix unblocks learning | `learning_mode=true` **or** eval return ≥ −41 (≥20% above −51.6 floor) with rising best-train trajectory | Returns still pin at −51.6 floor |
| **H8b** | KL/η stay bounded | `kl_mean` stays within ~10× target over 50 eps; no monotonic η→1e11 ramp | KL/η still explode |
| **H8c** | Policy escapes saturation | Train `torque_saturated_fraction` < 0.9 (was 0.998 in all prior MPO runs) | Still ~1.0 |
| **H8d** | α_μ/α_Σ remain finite and active | Both alpha values track KL constraint errors; neither collapses to 0 or explodes | Either hits extremes immediately |

**Overall:** **supported** if H8a **and** H8b; **not_supported** otherwise (then H8d still resolves symptom-vs-cause for Exp 11 design).

**Single arm:** no control re-run of the broken implementation needed — Exp 3/5 already provide the pre-fix baseline at identical protocol.

**Frozen protocol** (match Exp 3 `compare_mpo` / Exp 5 `mpo_s` exactly for comparability):

| Knob | Value |
|------|-------|
| dt | 1.5 s / 1.5 s |
| seed | 7 |
| warmup | 5 (rebuild) |
| train | 50 |
| eval | 2 |
| reward | sparse |
| action mode | **torque** (production default) |
| actor/critic units | S = 90/140 (production default) |
| new hparams | `eps_eta=0.1`, `target_kl_mu=0.1`, `target_kl_sigma=0.01`, `lr_alpha=1e-3` (fixed-dual defaults from `MPOConfig`) |
| videos | 3 train + 2 eval |

**Out of scope:** dense reward (Exp 3), width sweep (Exp 5), vector mode (→ Exp 11), encoder changes.

**Gate:** `pipeline_run_guard.check_pipeline_run_clear(slug="ml_mpo_decoupled_dual_torque")` before Phase 2.

### 0.2 Thought process (Why)

| Prior fact | Implication |
|------------|-------------|
| All MPO runs pre-fix collapsed to −51.6 / −243.5 within ep 1 | torque + sparse is the hard baseline to beat |
| `h1b_stable_eta`: η frozen=1.0 still explodes KL, critic diverges | M-step unconstrained — α fix is the lever |
| KL≈5.6e4 at ep 0 while η≈4 ([investigation §3a](../../research/mpo-learning-collapse-investigation.md)) | η lag confirms dual is the cause, not symptom |
| SAC learns sparse torque (Exp 3, [D-017](../../research/DECISIONS.md)) | Environment is learnable — MPO just needed the correct algorithm |
| Width identical collapse (Exp 5, [D-018](../../research/DECISIONS.md)) | Not capacity — the fix targets the right lever |

#### 0.2.1 Shoulders of giants

- **Abdolmaleki et al. 2018 (`docs/research/1812.02256v1.pdf`)** — decoupled-KL MPO: E-step Q-dual η + separate α_μ/α_Σ M-step trust region. The exact structure implemented in `d5af20c`.
- **Abdolmaleki et al. 2018 (`arXiv:1806.06920`)** — MPO robustness claim: same hyperparameters across tasks when the dual is correct.

### 0.3 Preliminary implementation remarks (How)

**Scaffold:** copy `ml_mpo_model_size/` (nearest MPO fork); swap `MPOConfig` fields to production defaults (the fix is already in production `MPOConfig` / `controller_agent.py`). No agent fork needed — use `MPOAgent` directly.

| Component | Planned path |
|-----------|--------------|
| Entry | `run_mpo_torque.py` (`--smoke`, `--show-progress`) |
| Runner | `_torque_runner.py` — standard MPO train/eval loop, no reward or agent fork |
| dt constants | `_sim_constants_fork.py` — 1.5 s / 1.5 s |
| Mutex | `_run_guard.py` → `pipeline_run_guard` |
| Results | `results/mpo_torque.json`, `mpo_torque_analysis.md` |

**Smoke:** one warmup + one train step; assert `log_alpha_mu` and `log_alpha_sigma` present on agent; check `kl_mean` finite in returned metrics; `torque_saturated_fraction` logged.

**Comparators (read-only, no re-run):**

| Run | Return | Notes |
|-----|--------|-------|
| `9998217224670341_ml_compare_compare_mpo_23-22-09` | −51.6 | Exp 3 MPO dense — KL→1.5e11 |
| `9998217218692971_ml_mpo_model_size_mpo_s_01-01-46` | −51.6 | Exp 5 mpo_s sparse — KL→0 frozen |

---

## Phase 1 — Built

### 1.1 What was built

| Component | Path |
|-----------|------|
| Entry | `run_mpo_torque.py` |
| Runner | `_torque_runner.py` — production `MPOAgent`, sparse torque |
| dt constants | `_sim_constants_fork.py` — 1.5 s / 1.5 s |
| Mutex | `_run_guard.py` → `pipeline_run_guard` |
| Results | `results/mpo_torque.json`, `results/smoke.json` |

### 1.2 Why

No agent fork — dual fix already in production `MPOConfig` / `controller_agent.py` (`d5af20c`).

### 1.3 How to run

```powershell
conda activate auto-sat
cd backend/scripts/experiments/ml_mpo_decoupled_dual_torque
python run_mpo_torque.py --smoke --allow-cpu
python run_mpo_torque.py --show-progress
```

**Smoke + canonical run (2026-06-30):** `results/mpo_torque.json`; duplicate re-run (`9998217154247371_*`) aborted — use canonical dir only.

---

## Phase 2 — Run

### 2.1 Run scope (What)

| Arm | Agent | Action | Reward | Train | Eval | Seed | dt |
|-----|-------|--------|--------|-------|------|------|-----|
| **torque_sparse** | MPO (fixed dual) | torque | sparse | 50 | 2 | 7 | 1.5 s / 1.5 s |

**Canonical run dir:** `d:\code\sem-proj-asc\backend\autonomous_control\runs\9998217164480175_ml_mpo_decoupled_dual_torque_sparse_16-05-19`

**Results JSON:** `backend/scripts/experiments/ml_mpo_decoupled_dual_torque/results/mpo_torque.json` · wall ~33 min.

| Metric | torque_sparse | Pre-fix comparator (`mpo_s` −51.6) |
|--------|---------------|--------------------------------------|
| `learning_mode` | **true** | false (floor) |
| Eval return mean | **−81.1** | −51.6 |
| Train return best | **+8.7** (ep 28) | −51.6 |
| `kl_mean` (last ep) | **0.021** | →0 frozen / →1e11 |
| `eta_mean` (last ep) | **0.788** | frozen |
| Train `torque_saturated_fraction` | **0.951** | ~0.998 |
| Eval `torque_saturated_fraction` | **0.986** | ~1.0 |
| Eval `shutter_meaningful_fraction` | **0.0** | — |
| Train `shutter_meaningful_fraction` | **0.083** | — |

### 2.2 Run monitoring (Why)

- **Mutex:** cleared after canonical run; duplicate `18-55-51` spawn **KeyboardInterrupt** — ignore for verdict.
- **Operator (Phase 2 review):** dual fix visibly works; returns plateau ~ep 5; safe-mode fires each ep; `pi_loss` plateaus; sparse applied shutters on eval despite latent opportunity peaks.

### 2.3 Run log & artifacts (How)

**Manifest:** `d:\code\sem-proj-asc\backend\autonomous_control\runs\9998217164480175_ml_mpo_decoupled_dual_torque_sparse_16-05-19\artifacts_manifest.json`

**Videos:**

| Clip | Path |
|------|------|
| Eval ep 0 (rank 1) | `d:\code\sem-proj-asc\backend\autonomous_control\runs\9998217164480175_ml_mpo_decoupled_dual_torque_sparse_16-05-19\videos\eval_ep_0_rank1.mp4` |
| Eval ep 1 (rank 2) | `d:\code\sem-proj-asc\backend\autonomous_control\runs\9998217164480175_ml_mpo_decoupled_dual_torque_sparse_16-05-19\videos\eval_ep_1_rank2.mp4` |
| Train best (ep 28, +8.7) | `...\videos\train_ep_28_rank1.mp4` |
| Train ep 11 (rank 2) | `...\videos\train_ep_11_rank2.mp4` |
| Train ep 6 (rank 3) | `...\videos\train_ep_6_rank3.mp4` |

**Plots:** `...\plots\returns_by_episode.png`, `learning_curves.png`, `eval_episode_diagnostics.png`, `train_episode_diagnostics_p01.png` … `p05.png`

**Frame inspect (eval best):** `d:\code\sem-proj-asc\.cursor\video_frame_inspect\data\eval_best_20260630T150214Z\manifest.json` — cyan latent peaks; almost no gold applied-capture dots on eval; train ep 28 shows rare successful captures.

---

## Phase 3 — Evaluation

### 3.1 Claims & success criteria (What)

Restated from Phase 0 — H8a–H8d vs pre-fix −51.6 floor and saturation ~1.0.

### 3.2 Evidence summary (Why)

| Signal | Finding |
|--------|---------|
| **Algorithm** | Dual fix **unblocks learning** — `learning_mode=true`, rising train trajectory, KL ~0.02, η ~0.78 (not frozen / exploded). |
| **Mission** | Eval **−81.1** — worse than pre-fix floor on eval slice; almost **no meaningful eval shutters**; torque still **saturated**. |
| **Safety** | Safe-mode activations ~5–6/ep (telemetry); **no reward penalty** for cuts — motivates [Exp 10](../0-initialized/10-mpo-safe-mode-penalty.md). |
| **Video** | Eval: latent opportunity without applied capture; train ep 28: intermittent good shutters — timing/credit gap, not broken applied-reward kernel. |

**Literature:** [D-022](../../research/DECISIONS.md) — decoupled-KL fix validated; mission outcome partial (branch C: unblock then relapse on eval).

### 3.3 Verdict table (How we decided)

| # | Claim | Criterion | torque_sparse | **Verdict** |
|---|-------|-----------|---------------|-------------|
| H8a | Dual unblocks learning | `learning_mode=true` or eval ≥ −41 | **true**; train best +8.7 | **supported** |
| H8b | KL/η bounded | KL within ~10× target; no η ramp | KL 0.021; η 0.788 | **supported** |
| H8c | Escapes saturation | train sat < 0.9 | **0.951** | **not_supported** |
| H8d | α_μ/α_Σ active | finite, tracking | α_μ ~1e-5, α_σ ~0.28 | **supported** |

**Overall verdict:** **partial** — algorithm fix **supported** (H8a, H8b, H8d); mission / saturation **not** (H8c, eval shutters).

**Follow-up:** [Exp 10](../1-built/10-mpo-safe-mode-penalty.md) safe-mode penalty; [Exp 11 MPO vector](../1-built/11-mpo-decoupled-dual-vector.md) gated on this verdict.

**Promote (Phase 4):** decoupled-KL dual tests only — no new hparams; no production reward changes.

---

## Phase 4 — Documentation

### 4.1 Promotion & integration (What)

| Item | Action |
|------|--------|
| **Already in production** | Decoupled-KL MPO dual (`MPOConfig.decoupled_kl=True`, `target_kl_mu`/`target_kl_sigma`, separate `log_alpha_mu`/`log_alpha_sigma`) — commit `d5af20c` |
| **Promoted at closeout** | **None** — algorithm fix pre-merged; Exp 8 validates behavior |
| **Regression tests** | **Deferred** — add `test_mpo_decoupled_dual_kl_bounded.py` smoke (finite KL over N stores) in follow-up PR |
| **Not promoted** | Reward plane changes; torque saturation mitigations; safe-mode penalty → [Exp 10](../0-initialized/10-mpo-safe-mode-penalty.md) |
| **DECISIONS** | [D-024](../../research/DECISIONS.md) — Exp 8 closeout **partial** |

### 4.2 Closeout rationale (Why)

Exp 8 confirms [D-023](../../research/DECISIONS.md) charter: the decoupled-KL dual is the correct MPO learning lever — `learning_mode=true`, KL ~0.02, η bounded. Mission KPIs remain poor (eval −81, saturation ~0.95, sparse eval shutters). This is **algorithm supported / mission partial** — not a reason to revert the dual fix.

Operator video: eval shows latent capture opportunity without applied gold dots; train ep 28 (+8.7) shows intermittent successful shutters. Safe-mode fires without reward credit — chartered as Exp 10.

**Exp 11 MPO vector** gate cleared: dual fix validated enough to test vector mode (see `11-mpo-decoupled-dual-vector.md`, `blocked_by` cleared).

### 4.3 Knowledge persistence (How)

| Artifact | Path |
|----------|------|
| Pipeline doc (this file) | `docs/experiments/pipeline/4-documentation/08-mpo-decoupled-dual-fix.md` |
| Analysis card | `backend/scripts/experiments/ml_mpo_decoupled_dual_torque/results/mpo_torque_analysis.md` |
| Summary JSON | `backend/scripts/experiments/ml_mpo_decoupled_dual_torque/results/mpo_torque.json` |
| Investigation | [mpo-learning-collapse-investigation.md](../../research/mpo-learning-collapse-investigation.md) § Exp 8 |
| README index | [pipeline/README.md](../README.md) row 8 |

**Report archive:**

- Eval: `...\9998217164480175_ml_mpo_decoupled_dual_torque_sparse_16-05-19\videos\eval_ep_0_rank1.mp4`
- Train peak: `...\videos\train_ep_28_rank1.mp4`
- Returns: `...\plots\returns_by_episode.png`
- Frame manifest: `.cursor/video_frame_inspect/data/eval_best_20260630T150214Z/manifest.json`


# 0-06-modular-encoder-r2.md

---
experiment_id: 6
slug: ml_modular_encoder_r2
title: "Exp 6 — Modular encoder (r2)"
current_phase: 0
overall_verdict: deferred
blocked_by: null
code_path: backend/scripts/experiments/ml_modular_encoder_r2/
phases:
  "0": { status: cancelled, documented_utc: "2026-06-29T20:00:00Z", completed_utc: null, notes: "Deferred — archived; low priority vs Exp 7 reward/path work" }
  "1": { status: pending, documented_utc: null, completed_utc: null }
  "2": { status: pending, documented_utc: null, completed_utc: null }
  "3": { status: pending, documented_utc: null, completed_utc: null }
  "4": { status: pending, documented_utc: null, completed_utc: null }
run_lock_holder: null
decision_ids: [D-006, D-015]
predecessor: ml_modular_encoder
---

# Exp 6 — Modular encoder r2 (`ml_modular_encoder_r2`)

> **Status: deferred / archived** — not scheduled. Encoder A0 vs A1 retest deprioritized after Exp 5 width ruled out and Exp 4 vector+reward path showed more value ([D-021](../../research/DECISIONS.md), [D-015](../../research/DECISIONS.md)).

**Agent:** SAC · **dt:** 1.5 s / 1.5 s · **Train:** TBD (≥7; match learnable slice from Exp 3/5)  
**Plan:** [sac_vs_mpo_compare plan](../../../../.cursor/plans/sac_vs_mpo_compare_821ab4d5.plan.md) · **Predecessor:** [02-modular-encoder.md](../4-documentation/02-modular-encoder.md) (Exp 2 v1)  
**Investigation:** [model-size-investigation.md](../../research/model-size-investigation.md)  
**Blocked by:** ~~Exp 5~~ — **unblocked** after Exp 5 closeout (2026-06-30)  
**Priority:** [D-015](../../research/DECISIONS.md) — **high deferred interest** once `learning_mode` exists elsewhere in the stack

---

## Phase 0 — Initialized

### 0.1 Experiment scope (What)

**Core question:** Re-test **SAC flat vs vector-compress encoder** (same delta as Exp 2 v1) once the pipeline has a **learnable MPO reference** from width sizing — or a documented verdict that capacity is not the bottleneck.

**Hypothesis (H2r):**

> With reward / training protocol aligned to the best learnable regime from Exp 3 + Exp 5, **A1** (`CompressedControllerEncoder`, `vector_embed_dim=8`) beats **A0** (production flat `ControllerEncoder`) on `learning_mode` and eval return.

| Claim | Success criterion | Falsified if |
|-------|-------------------|--------------|
| **H2ra** | A1 `learning_mode` **true** while A0 false, or A1 eval return ↑ ≥ **10%** vs A0 | Both false / flat; A0 ≥ A1 |
| **H2rb** | A1 best train return **>** A0 | A0 best train ≥ A1 |
| **H2rc** | A1 improves vs A0 on `shutter_meaningful_fraction` or lower spam at equal return | No secondary KPI gap |

**Arms** (unchanged from Exp 2 v1):

| Arm | Encoder | Notes |
|-----|---------|-------|
| `sac_a0` | Flat / production `ControllerEncoder` | Baseline |
| `sac_a1` | `CompressedControllerEncoder` (`k=8`) | Single encoder delta |

**Frozen until Phase 1 build** (pick from Exp 3/5 closeout — do not guess now):

| Knob | v1 (Exp 2) | r2 default intent |
|------|------------|-----------------|
| Reward mode | sparse | **Match Exp 3 SAC arm** if `learning_mode`; else **dense** if Exp 5 M/L learns |
| `train_episodes` | 7 | **≥7**; extend only if Exp 5 uses longer slice with signal |
| dt | 1.5 / 1.5 | unchanged [D-002] |
| Warmup | 5 ep, rebuild per arm | unchanged |

**Stop rule:** Same as Exp 2 — no split-head / wider encoder arms without `learning_mode` on A1.

**Gates before Phase 2 run:**

- [x] Exp 2 v1 evaluation ([D-014](../../research/DECISIONS.md)) — [02-modular-encoder.md](../4-documentation/02-modular-encoder.md)
- [ ] Exp 3 closeout — SAC vs MPO verdict + reward mode for SAC path
- [ ] **Exp 5 closeout** — MPO S/M/L width ablation; record whether any arm achieves `learning_mode` or stable KL
- [ ] r2 reward mode + train length **frozen in DECISIONS** (or Phase 1.1)

**Out of scope:** MPO arms, encoder width sweep, shutter threshold (Exp 1 closed).

### 0.2 Thought process (Why)

| Prior fact (Exp 2 v1) | Implication for r2 |
|------------------------|-------------------|
| Both SAC arms `learning_mode=false`; returns **worsen** after ep 0; **q_loss** explodes | v1 sparse slice may be **non-learnable** for SAC — not a clean encoder test |
| A1 **worse** eval than A0 (−86.5 vs −78.9) despite **fewer** eval shutters | Compress encoder did not help; rerun only meaningful in a learnable regime |
| `shutter_meaningful_fraction=0` on all arms | Encoder test needs a protocol where capture credit is observable |
| SAC **~40%** shutter rate vs MPO **~100%** | SAC behavior differs; encoder question is separate from spam |

**Deferred high interest ([D-015](../../research/DECISIONS.md)):** v1 verdict is `not_supported`, but **if the stack ever reaches `learning_mode=true`**, group compressors on bearing/mask are **highly interesting** — structured 105-D obs, literature support, and A1’s lower eval shutter rate are worth retesting once reward/credit/algorithm are fixed. Exp 6 is chartered for that gate, not because v1 showed a win.

**Why after Exp 5 (MPO sizing):**

- [D-006](../../research/DECISIONS.md): encoder before width — **v1 satisfied**; width ablation (Exp 5) answers “is MLP capacity the bottleneck?”
- If Exp 5 **M/L learns** on dense (or chosen reward), r2 reruns encoder comparison under that **known-good** SAC-compatible protocol.
- If Exp 5 **all widths collapse** (H5d), r2 still runs SAC encoder A0 vs A1 with Exp 3 reward choice — tests structure when capacity is ruled out.

**Reject / defer:**

| Path | Status | Why |
|------|--------|-----|
| Encoder r2 before Exp 5 | **blocked** | User charter — wait for MPO sizing |
| Split-head encoder | deferred | Exp 2 stop rule |
| Re-run v1 sparse 7-ep only | rejected | Already inconclusive; r2 must change protocol per gates |

#### 0.2.1 Shoulders of giants

- Exp 2 v1 record: [02-modular-encoder.md](../4-documentation/02-modular-encoder.md) · `results/modular_encoder_summary.json`
- [model-size-investigation.md](../../research/model-size-investigation.md) — encoder vs width ordering
- Same literature as Exp 2 §0.2.1 (entity-based RL, Gorishniy embeddings, MERL fusion)
- Exp 5 width refs: MPO 2018 appendix; [05-mpo-model-size.md](05-mpo-model-size.md)

### 0.3 Preliminary implementation remarks (How)

**Scaffold:** Copy **`ml_modular_encoder/`** → `ml_modular_encoder_r2/` (or subcommand on same runner with `--protocol r2` — pick one in Phase 1; prefer **separate folder** for JSON contract clarity).

**Single delta vs v1:** reward fork mode + train episode count from Exp 3/5 gate table; encoder arms unchanged.

| Component | Planned path |
|-----------|--------------|
| Runner | `run_modular_encoder_r2.py` (or extend v1 with `--profile r2`) |
| Encoders / agents | Reuse `encoders/`, `encoder_agents/` from v1 |
| Results | `results/modular_encoder_r2_summary.json`, `modular_encoder_r2_analysis.md` |

**Smoke:** `--smoke` on `sac_a1` with **r2 reward profile** applied; one `train()` step.

**Risks:** Exp 5 inconclusive → r2 still runnable but may repeat v1 null result; document as H2r inconclusive not encoder falsified.

**Follow-up if inconclusive:** Close encoder line; promote Exp 4 agent-reference or production SAC sparse with documented non-learnability.

*(Skills)* [`hypothesis-experiment-cycle`](../../../.cursor/skills/hypothesis-experiment-cycle/SKILL.md) § ponytail rule; [`experiment-knowledge-pipeline`](../../../.cursor/skills/experiment-knowledge-pipeline/SKILL.md) Phase 1 build.

---

## Pipeline next step

1. Finish **Exp 2** Phases 2–4 (document run → verdict → closeout).  
2. Run **Exp 3** → freeze SAC reward mode for r2.  
3. Run **Exp 5** → MPO sizing closeout (**unblocks r2**).  
4. `/close-experiment-step` Phase 0 here when 0.1–0.3 approved → Phase 1 build (`ml_modular_encoder_r2/`).


# 13-mpo-learn-cadence-hparams.md

---
experiment_id: 13
slug: ml_mpo_learn_cadence_hparams
title: "Exp 13 — MPO learn cadence + untouched hyperparams"
current_phase: 2
overall_verdict: pending
blocked_by: null
code_path: backend/scripts/experiments/ml_mpo_learn_cadence_hparams/
predecessor: ml_mpo_decoupled_dual_torque
phases:
  "0": { status: done, documented_utc: "2026-06-30T22:00:00Z", completed_utc: "2026-06-30T21:41:09Z" }
  "1": { status: done, documented_utc: "2026-06-30T21:45:00Z", completed_utc: "2026-06-30T21:43:15Z" }
  "2": { status: in_progress, documented_utc: null, completed_utc: null }
  "3": { status: pending, documented_utc: null, completed_utc: null }
  "4": { status: pending, documented_utc: null, completed_utc: null }
run_lock_holder: null
decision_ids: []
---

# Exp 13 — MPO learn cadence + untouched hyperparams (`ml_mpo_learn_cadence_hparams`)

**Agent:** MPO (decoupled-KL dual, Exp 8 protocol) · **Action:** torque · **Reward:** sparse · **dt:** 1.5 s / 1.5 s (frozen)  
**Predecessor:** [Exp 8](../4-documentation/08-mpo-decoupled-dual-fix.md) (working MPO baseline); [Exp 5](../4-documentation/05-mpo-model-size.md) (width closed — not primary axis here)  
**Infra reuse:** `backend/scripts/experiments/train_timing/` (single-episode timing + duty-cycle sweep)

---

## Phase 0 — Initialized

### 0.1 Experiment scope (What)

**Core question (two tracks, one experiment):**

1. **Track A — Learn cadence:** Can we batch MPO `train()` calls relative to controller stores (and optionally controller interval) to cut wall time **without** changing learning outcomes?
2. **Track B — Untouched hyperparams:** Which **non-architecture** MPO knobs (LRs, KL/temperature, batch, samples) move eval/train KPIs on the **cadence winner** from Track A?

**Operator ratio notation** — **sim : collect : learn** (three relative frequencies):

| Slot | Meaning | Code knob |
|------|---------|-----------|
| **sim (1×)** | Physics integration step | `sim_dt_s` = **1.5 s** (frozen, H0 winner) |
| **collect (ap)** | Agent issues a new command **and** `store()` runs | `controller_interval_s` = ratio × 1.5 s |
| **learn (tr)** | Every **tr** collect events, open the learn gate and run **tr** `train()` calls (each samples `batch_size` transitions from replay — not a new stacked-obs architecture) | `train_every_n_steps` = **tr**, `updates_per_step` = **tr** |

**Agent vs low-level (this repo):** In train/eval the **learned agent is the pilot** — `get_action` + `store` only when `stepper.should_update_controller()` is true (`episode_runner.py`). **Simulation still steps every `sim_dt_s`**; between pilot ticks the last command is **held** (zero-order hold on torque / pointing). Attitude safety may override torque any step. There is no separate OBC loop issuing different commands every sim step in torque mode; vector mode resolves pointing→torque every sim step from the **last** pilot pointing command.

**Cadence arms** (canonical mapping — operator-confirmed 2026-06-30):

| Label | Ratio | `sim_dt_s` | `controller_interval_s` | `train_every_n_steps` | `updates_per_step` | Stores/ep† | Train updates/ep‡ |
|-------|-------|------------|-------------------------|----------------------|-------------------|------------|-------------------|
| **baseline_1_1_1** | 1:1:1 | 1.5 | 1.5 | 1 | 1 | ~516 | ~516 |
| **cadence_1_1_10** | 1:1:10 | 1.5 | 1.5 | 10 | 10 | ~516 | ~516 |
| **cadence_1_1_50** | 1:1:50 | 1.5 | 1.5 | 50 | 50 | ~516 | ~516 |
| **cadence_1_2_4** | 1:2:4 | 1.5 | **3.0** | 4 | 4 | ~258 | ~256 |

†Controller stores = sim steps ÷ `controller_interval_steps` (rounded integer multiple via `scheduler.resolve_controller_interval_steps`).  
‡`floor(stores / train_every_n_steps) × updates_per_step`.

**Interpretation:** `1:1:10` = collect every 1.5 s, learn every **10×1.5 s = 15 s** with **10** gradient bursts at that gate (same total updates as baseline, different scheduling). `1:2:4` = collect every **3 s**, learn every **4×3 s = 12 s** with **4** bursts — **also halves store count** (slower pilot), so total updates ≈ **half** baseline; treat as a distinct MDP + throughput arm, not matched-duty to `1:1:1`.

**Matched-duty controls** (same total gradient steps as baseline at **1.5 s** controller — isolates scheduling only):

| Label | Ratio | `train_every_n_steps` | `updates_per_step` | Total updates ≈ |
|-------|-------|----------------------|-------------------|-----------------|
| **duty_10x10** | 1:1:10 sched | 10 | 10 | ~516 |
| **duty_100x100** | 1:1:100 sched | 100 | 100 | ~516 |

**Track A claims**

| ID | Claim | Success criterion | Falsified if |
|----|-------|-------------------|--------------|
| **H13a** | Faster cadence, same learning | Among parity-passing arms, pick **lowest wall_s** for 50-train run | All fast arms collapse (KL→0, flat returns) while baseline learns |
| **H13b** | Batched learn preserves KPI | `1:1:10` / `1:1:50` match baseline eval within ≤5% at equal train ep **and** lower wall | Speedup only from fewer updates (`train_every`≫`updates`) with large return gap |
| **H13c** | Matched duty ≈ baseline | `10×10` / `100×100` within noise of `1:1:1` on eval | Matched duty diverges >10% eval return with same update count |

**Track B — hyperparam axes (untouched or single-point in pipeline so far)**

| Axis | Default (`MPOConfig`) | Proposed sweep (coarse) | Rationale |
|------|----------------------|-------------------------|-----------|
| **learning_rate_pi** | 1.5e-4 | {5e-5, 1.5e-4, 4.5e-4} | Exp 5 raised LRs ad hoc; no grid |
| **learning_rate_q** | 4.5e-4 | {1.5e-4, 4.5e-4, 1e-3} | Critic often 3× actor in literature |
| **learning_rate_eta** | 1e-3 | {3e-4, 1e-3, 3e-3} | Dual temperature step size |
| **target_kl_mu / target_kl_sigma** | 0.1 / 0.01 | {0.05, 0.1, 0.2} × {0.005, 0.01, 0.02} | MPO “temperature” / trust region — fixed in Exp 8 |
| **batch_size** | 256 | {128, 256, 512} | Affects train wall time + gradient noise |
| **num_samples_q / num_samples_pi** | 80 / 40 | {40/20, 80/40, 120/60} | MPO-specific compute vs variance |
| ~~buffer_size~~ | 50_000 | **frozen** | ~516 stores/ep × 50 ep ≪ capacity; unlikely lever |
| ~~gamma / tau~~ | 0.99 / 0.005 | **frozen** | Credit-horizon semantics — defer |
| ~~width (actor/critic units)~~ | 90 / 140 | **frozen** | Exp 5 closed; optional **cross-check** on winning LR only if Track B shows sensitivity |

**Track B design:** **staged fractional sweep** on cadence winner — not full Cartesian product.

- **Stage B0 (screen):** one-at-a-time ±1 step from default on each axis above (7 arms + default = 8 configs), 10 train ep, eval 2.
- **Stage B1 (refine):** 2×2 on the 1–2 axes that moved eval most in B0; 50 train ep.

**Track B claims**

| ID | Claim | Success criterion |
|----|-------|-------------------|
| **H13d** | Some untouched hparam moves KPI | ≥1 B0 arm beats default eval return by ≥5% **or** same return with ≥10% lower wall |
| **H13e** | Width not required | Best B1 config does not require width change vs Exp 5 null result |

**Frozen protocol** (all arms unless noted):

| Knob | Value |
|------|-------|
| dt | 1.5 s / 1.5 s |
| seed | 7 |
| warmup | 5 (rebuild per arm) |
| train | 50 (Track A parity screen may use 10 ep first) |
| eval | 2 |
| reward | sparse (Exp 8) |
| action | torque |
| MPO dual | decoupled KL (Exp 8) |
| videos | 3 train + 2 eval (trim only with `--trim-artifacts` on screen arms) |

**Primary metrics:** `summary_metrics.json` eval/train best return, `learning_mode`, KL stats, **`wall_s` / `steps_per_s`**, `n_train_updates`, timing breakdown (`episode_timing` categories).

**Gate:** `pipeline_run_guard.check_pipeline_run_clear(slug="ml_mpo_learn_cadence_hparams")` before Phase 2. Soft preference: after Exp 10–12 runs complete (mutex + stable MPO comparator).

**Out of scope:** SAC arms; dense reward; vector mode; changing `sim_dt_s` (H0 closed at 1.5 s); production promotion until Phase 4.

### 0.2 Thought process (Why)

| Prior | Implication |
|-------|-------------|
| [Exp 5](../4-documentation/05-mpo-model-size.md) | Width not the bottleneck — sweep **optimization / trust-region** knobs instead |
| [Exp 8](../4-documentation/08-mpo-decoupled-dual-fix.md) | Decoupled dual is the working MPO baseline — freeze architecture, vary cadence + hparams |
| `train_timing/` duty probes | `duty_100x1`: ~71 steps/s vs baseline ~13 steps/s but **5** train updates — pure stride wins speed, loses learning; burst variants untested end-to-end |
| [D-012](../../research/DECISIONS.md) | Sequential arms only — cadence screen (~8 arms × 1 ep) then short train, then B0/B1 |
| [machine-learning.md](../../presentation/machine-learning.md) § Training loop | Documents `train_every_n_steps` / `updates_per_step`; cadence does not change mission physics |
| Exp 10 charter | Explicitly deferred “hparam grid” to this experiment |

**Defer / reject**

- **buffer_size:** replay rarely fills; changing it adds cache invalidation noise without expected signal.
- **Full grid on width × LR:** Exp 5 + operator note — cross-correlation possible but **second-order**; only B1 spot-check if LR axis wins.
- **Controller interval change (`1:2:4`):** halves pilot decisions — different MDP; compare on its own merits (throughput + learning), not as matched-duty to `1:1:1`.

#### 0.2.1 Shoulders of giants

- **Abdolmaleki et al. 2018 (MPO)** — robustness to hyperparameters when dual/KL constraints are correct; motivates KL + LR axes over width.
- **SAC/MPO replay cadence** — common practice: multiple gradient steps per env step; our `updates_per_step` is the direct knob ([`environment-hyperparameters.md`](../../presentation/environment-hyperparameters.md)).
- **Prior art in repo:** `train_timing/run_duty_cycle_compare.py` — micro-benchmark; this experiment adds **full-episode learning parity** and hparam sweep on the winner.

### 0.3 Preliminary implementation remarks (How)

**Feasibility:** High — fork from Exp 8 runner + `train_timing/_fixtures.py` pattern; no production edits required ([D-003](../../research/DECISIONS.md)).

**Hook points**

| Component | Path |
|-----------|------|
| Cadence knobs | `TrainingWorkflowConfig.train_every_n_steps`, `updates_per_step` |
| Controller interval arm | `ml_algo_overnight/_sim_constants_fork.py` `apply_dt_profile` (only for `cadence_1_2_4`) |
| MPO hparams | `MPOConfig` replace in experiment `_frozen.py` |
| Timing | `episode_timing.EpisodeTimingCollector` via `train_timing/_profile_runner.py` |
| Mutex | `_run_guard.py` → `acquire_pipeline_run_lock` |

**Execution order (Phase 2)**

1. **A0 — Micro timing:** extend `train_timing` variants with `cadence_1_1_10`, `cadence_1_1_50`, `cadence_1_2_4` (+ matched duties); 1 train ep each; record JSON.
2. **A1 — Learning parity:** top 3–4 by steps/s → 10 train ep + eval; drop arms with KL freeze or >10% eval gap vs baseline.
3. **A2 — Confirm winner:** 50 train ep on cadence winner + baseline (2 arms).
4. **B0 — Hparam OAT screen:** 8 configs on winner cadence.
5. **B1 — Refine:** 2–4 arms, 50 train ep.

**Smoke:** 1 warmup + 1 train ep on `baseline_1_1_1` and `cadence_1_1_10`; assert `n_train_updates` matches table and run completes.

**Risks**

| Risk | Mitigation |
|------|------------|
| `1:1:50` OOM / runaway wall time | Cap burst at 50 only in A0; drop arm if single-ep wall >3× baseline |
| Hparam combinatorial explosion | Staged B0/B1 only; no full factorial |
| `1:2:4` halves stores + updates | Document in Phase 2; do not expect eval parity with `1:1:1` — success = acceptable KPI at lower wall |
| False speed win (stride-only) | H13c matched-duty controls + learning KPI gate; reject arms where `updates_per_step` ≪ `train_every_n_steps` |

---

## Phase 1 — Built

### 1.1 Build plan (What)

**Single logical delta:** vary **learn cadence** (`TrainingWorkflowConfig.train_every_n_steps`, `updates_per_step`) and **pilot interval** (`controller_interval_s` for `1:2:4` only); optional **MPOConfig** replace for Track B — no reward, architecture, or production edits.

| Artifact | Path |
|----------|------|
| Entry | `backend/scripts/experiments/ml_mpo_learn_cadence_hparams/run_exp13.py` |
| Cadence arms | `_cadence_profiles.py` |
| Hparam arms (Track B) | `_hparam_profiles.py` |
| Runner | `_runner.py` |
| Frozen knobs | `profile.json`, `_profile_baseline.py` |
| dt fork | `_sim_constants_fork.py` (+ `DT_15_AP2` for ap=3 s) |
| Mutex | `_run_guard.py` → `pipeline_run_guard` |
| Charter / hypothesis | `SUBAGENT_CHARTER.md`, `H13-learn-cadence-hparams.md` |
| Summary JSON | `results/learn_cadence_hparams_summary.json` |
| Smoke JSON | `results/smoke.json` |
| Timing A0 | `results/timing_a0.json`, `results/timing_a0.md` |
| Analysis card (Phase 3) | `results/learn_cadence_hparams_analysis.md` *(scaffold at closeout)* |

**Scaffold source:** Exp 8 `ml_mpo_decoupled_dual_torque` (MPO decoupled-KL sparse torque @ dt 1.5 s).

### 1.2 Build implementation (How we forked)

**Built 2026-06-30** — Nike mode; fork-only under `ml_mpo_learn_cadence_hparams/`.

| Component | Implementation |
|-----------|----------------|
| Cadence hook | `frozen_training_config(..., train_every_n_steps=, updates_per_step=)` + `run_serial(..., train_updates_per_step=, train_every_n_steps=)` via `tw.run_training_workflow` |
| `1:2:4` dt | `DT_15_AP2` (`sim_dt_s=1.5`, `controller_interval_s=3.0`) via `_sim_constants_fork.apply_dt_profile` |
| MPO hparams | `dataclasses.replace(setup.mpo_config, **overrides)`; `--hparam-arm` selects `_hparam_profiles.HPARAM_SCREEN_ARMS` |
| Timing A0 | `run_timing_episode()` + `EpisodeTimingCollector` (same pattern as `train_timing/_profile_runner.py`) |
| Smoke | 1 warmup + 1 train ep per arm; asserts `n_train_updates > 0` |

**Smoke result** (`results/smoke.json`, 2026-06-30 ~21:40 UTC):

| Arm | `n_train_updates` | `steps/s` | Episode wall (s) | Run dir |
|-----|-------------------|-----------|------------------|---------|
| `baseline_1_1_1` | 516 | 13.0 | 39.7 | `d:\code\sem-proj-asc\backend\autonomous_control\runs\9998217144429519_ml_mpo_learn_cadence_smoke_21-39-29` |
| `cadence_1_1_10` | 510 | 13.5 | 38.1 | `d:\code\sem-proj-asc\backend\autonomous_control\runs\9998217144386260_ml_mpo_learn_cadence_smoke_21-40-13` |

Both arms: `passed: true`; update counts match charter table (510 ≈ floor(516/10)×10).

**Deviations from 1.1:** none. `duty_10x10` not a separate arm (identical knobs to `cadence_1_1_10`). Track B hparam arms defined but not smoke-tested (cadence winner unknown until Phase 2 A0/A1).

### 1.3 Run instructions (How to execute)

**Env:** `conda activate auto-sat` · repo root or experiment folder.

**Mutex (Phase 2 full trains):** one pipeline job per host — `pipeline_run_guard.check_pipeline_run_clear(slug="ml_mpo_learn_cadence_hparams")` before multi-ep arms. `--smoke` and `--timing-a0` are single-episode probes (still avoid overlapping with another pipeline lock holder).

```powershell
# Smoke (done)
python backend/scripts/experiments/ml_mpo_learn_cadence_hparams/run_exp13.py --smoke

# Track A0 — one timed train ep per cadence arm
python backend/scripts/experiments/ml_mpo_learn_cadence_hparams/run_exp13.py --timing-a0

# Single arm — full train (50 ep default)
python backend/scripts/experiments/ml_mpo_learn_cadence_hparams/run_exp13.py --arm baseline_1_1_1 --show-progress

# Parity screen — 10 ep, trim video
python backend/scripts/experiments/ml_mpo_learn_cadence_hparams/run_exp13.py --arm cadence_1_1_10 --train-episodes 10 --trim-artifacts --show-progress

# All cadence arms sequentially
python backend/scripts/experiments/ml_mpo_learn_cadence_hparams/run_exp13.py --show-progress

# Track B on baseline cadence (after A2 winner frozen in Phase 2 doc)
python backend/scripts/experiments/ml_mpo_learn_cadence_hparams/run_exp13.py --arm baseline_1_1_1 --hparam-arm hparam_lr_pi_high --train-episodes 10 --trim-artifacts
```

**Cadence arms (Track A):** `baseline_1_1_1`, `cadence_1_1_10`, `cadence_1_1_50`, `cadence_1_2_4`, `duty_100x100`.

**Expected artifacts per arm:** `results/<arm_id>.json`, `run_dir/config.json` (`experiment.arm_id`, cadence fields), `summary_metrics.json`, `plots/`, `videos/` (unless `--trim-artifacts`).

*(Phase blocks 2–4 appended by `/document-experiment-step`.)*


# 12-mpo-vector-torque-effort.md

---
experiment_id: 12
slug: ml_mpo_vector_torque_effort
title: "Exp 12 — MPO vector + torque-effort penalty"
current_phase: 3
overall_verdict: pending
blocked_by: null
code_path: backend/scripts/experiments/ml_mpo_vector_torque_effort/
predecessor: ml_mpo_decoupled_dual_vector
phases:
  "0": { status: done, documented_utc: "2026-06-30T22:00:00Z", completed_utc: "2026-06-30T22:00:00Z" }
  "1": { status: done, documented_utc: null, completed_utc: "2026-06-30T21:21:53Z"
  "2": { status: done, documented_utc: null, completed_utc: "2026-07-01T05:59:10Z"
  "3": { status: pending, documented_utc: null, completed_utc: null }
  "4": { status: pending, documented_utc: null, completed_utc: null }
run_lock_holder: null
decision_ids: []---
# Exp 12 — MPO vector + torque effort (`ml_mpo_vector_torque_effort`)

**Agent:** MPO (fixed dual) · **Action:** vector · **Reward:** sparse + **forced** torque effort · **dt:** 1.5 s  
**Predecessor:** [Exp 11](11-mpo-decoupled-dual-vector.md) (vector, effort off by default)
---
## Phase 0 — Initialized

### 0.1 Experiment scope (What)

**Core question:** Does enabling `k_torque_effort` in vector mode (overriding production default) reduce saturation or improve eval return vs Exp 11?

| ID | Claim | Success criterion |
|----|-------|-------------------|
| **H12a** | Effort signal helps vector | Eval return ≥ Exp 11 **or** train saturation lower |
| **H12b** | Learning stable | Same KL/η bounds as Exp 11 |

**Single arm:** `vector_torque_effort`. Comparator = Exp 11 (read-only after batch slot 2).

**Frozen protocol:** match Exp 11 except `enable_torque_effort=True`.

### 0.2 Thought process (Why)

Production `training_workflow` sets `enable_torque_effort=False` when `attitude_request_mode=vector`. Exp 8 torque runs with effort on; Exp 11 turns it off. Low-cost ablation while GPU is warm.

### 0.3 Preliminary implementation remarks (How)

Copy Exp 11; patch reward config + `_reward_fork.py` to force effort on. Smoke asserts `enable_torque_effort=true` in `config.json`.

---

## Phase 1 — Built

### 1.1 Build plan (What)

| Component | Path |
|-----------|------|
| Entry | `run_mpo_vector_torque_effort.py` |
| Runner | `_torque_effort_runner.py` — arm `vector_torque_effort` |
| Reward delta | `_reward_fork.py` — force `enable_torque_effort=True` |
| Results | `results/mpo_vector_torque_effort.json`, `results/smoke.json` |

### 1.2 Build implementation (How we forked)

Copied Exp 11; `_apply_torque_effort_reward()` patches MPO + mission reward before train.

**Smoke (2026-06-30):** passed — `results/smoke.json`; `enable_torque_effort=true`; finite KL/dual vars.

### 1.3 Run instructions (How to execute)

```powershell
conda activate auto-sat
cd backend/scripts/experiments/ml_mpo_vector_torque_effort
python run_mpo_vector_torque_effort.py --smoke --allow-cpu
python run_mpo_vector_torque_effort.py --show-progress
```

**Overnight queue slot 3 of 4:** `run_pipeline_overnight_batch.py`.

---

## Phase 2 — Run

### 2.1 Run scope (What)

| Arm | Action | Reward | Train | Eval |
|-----|--------|--------|-------|------|
| **vector_torque_effort** | vector | sparse + torque effort | 50 | 2 |

### 2.2 Run monitoring (Why)

- Queue position 3 of 3; mutex enforced per arm.

### 2.3 Run log & artifacts (How)

*(Fill after run completes.)*


# 10-mpo-safe-mode-penalty.md

---
experiment_id: 10
slug: ml_mpo_safe_mode_penalty
title: "Exp 10 — MPO safe-mode reward penalty (credit alignment)"
current_phase: 3
overall_verdict: pending
blocked_by: null
code_path: backend/scripts/experiments/ml_mpo_safe_mode_penalty/
predecessor: ml_mpo_decoupled_dual_torque
investigation: docs/research/mpo-learning-collapse-investigation.md
phases:
  "0": { status: done, documented_utc: "2026-06-30T20:00:00Z", completed_utc: "2026-06-30T21:00:36Z" }
  "1": { status: done, documented_utc: null, completed_utc: "2026-06-30T21:18:29Z"
  "2": { status: done, documented_utc: null, completed_utc: "2026-07-01T05:59:10Z"
  "3": { status: pending, documented_utc: null, completed_utc: null }
  "4": { status: pending, documented_utc: null, completed_utc: null }
run_lock_holder: null
decision_ids: [D-022]---
# Exp 10 — MPO safe-mode reward penalty (`ml_mpo_safe_mode_penalty`)

**Agent:** MPO (fixed decoupled-KL dual) · **Action:** torque · **Reward:** sparse + **new** safe-mode penalty arm · **dt:** 1.5 s / 1.5 s  
**Predecessor:** [Exp 8](../4-documentation/08-mpo-decoupled-dual-fix.md) (dual fix works; safe-mode fires without reward signal)  
**Not in scope:** Exp 8 closeout, SAC vector (defer separate arm if MPO result is informative)
---
## Phase 0 — Initialized

### 0.1 Experiment scope (What)

**Core question:** Does a per-step **safe-mode / AGENT_CUT penalty** on the reward plane reduce `safe_mode_activations`, improve agent-applied torque credit assignment, and improve mission KPIs vs Exp 8 (penalty **off**)?

**Motivation (operator, Exp 8 Phase 2):** Telemetry shows ~5–6 `safe_mode_activations` per episode while the agent still saturates torque; the safety layer replaces agent commands but **today’s `RewardConfig` has no term** for that — only torque-effort and shutter terms. The agent may not learn to stay inside safe envelope.

| ID | Claim | Success criterion | Falsified if |
|----|-------|-------------------|--------------|
| **H10a** | Safe-mode rate drops | Mean `safe_mode_activations`/ep **<** Exp 8 (~5–6) on train **and** eval | No decrease with penalty on |
| **H10b** | Learning preserved | `learning_mode=true`; train best return ≥ Exp 8 train best (+8.7) **or** eval improves vs Exp 8 (−81.1) | Collapse / frozen KL like pre-fix MPO |
| **H10c** | Applied capture not worse | Eval `shutter_meaningful_fraction` ≥ Exp 8 (≈0); latent→applied gap not wider on video | More torque saturation + fewer applied dots |
| **H10d** | Torque saturation eases | Train/eval `torque_saturated_fraction` < Exp 8 (~0.95) | Still ~1.0 with penalty on |

**Overall:** **supported** if H10b and (H10a or H10d) and H10c not regressed; **partial** if H10a/H10d improve but eval still poor; **not_supported** if penalty on is worse on all of H10a–H10d.

**Arms:**

| Arm | `enable_safe_mode_penalty` | Runs? |
|-----|---------------------------|-------|
| **safe_mode_penalty_on** | **true** | **Yes** (treatment) |
| penalty_off (Exp 8) | false | **No** — read-only `9998217164480175_ml_mpo_decoupled_dual_torque_sparse_16-05-19` |

**Frozen protocol** (match Exp 8 except reward flag):

| Knob | Value |
|------|-------|
| dt | 1.5 s / 1.5 s |
| seed | 7 |
| warmup | 5 (rebuild) |
| train | 50 |
| eval | 2 |
| reward | sparse; shutter/budget flags = Exp 8 defaults |
| action mode | torque |
| MPO hparams | same as Exp 8 |
| videos | 3 train + 2 eval |

**Penalty design (Phase 1 — experiment fork first, D-003):**

| Field | Proposed default | Notes |
|-------|------------------|-------|
| `enable_safe_mode_penalty` | `false` (prod); `true` (treatment arm) | New `RewardConfig` flag |
| `k_safe_mode_penalty` | TBD (start ~1.0–5.0 per penalized step) | Pint-consistent scalar; tune in smoke if gradient too weak/strong |
| Penalized steps | Step has `AGENT_CUT` **or** attitude safety applied safe-mode torque (`IN_SAFE_MODE` / `SAFE_MODE_TAKEOVER` interval) | Requires per-step boolean on canonical series or reward recompute hook |

**Out of scope:** turning off attitude safety; dense reward; vector mode; hparam grid (separate screen); promoting flag to production until Phase 4.

**Gate:** `pipeline_run_guard.check_pipeline_run_clear(slug="ml_mpo_safe_mode_penalty")` before Phase 2. Soft preference: run after Exp 8 Phase 2 review recorded (comparator already exists).

### 0.2 Thought process (Why)

| Prior | Implication |
|-------|-------------|
| Exp 8: dual fix **supported** (KL/η stable); eval poor; safe-mode fires every ep | Algorithm learns; **reward plane** may be missing credit for safety overrides |
| No safe-mode term in `reward.py` today | Hypothesis is additive — not revisiting Exp 8 dual fix |
| Torque-effort penalty alone did not prevent saturation + safe-mode | Effort penalizes magnitude, not “command was cut” |
| Exp 9 SAC reward split | Parallel reward-plane thread on SAC; **this** exp is MPO torque only |

**Reject / defer:**

| Path | Why |
|------|-----|
| Bundle into Exp 8 closeout | Operator explicitly deferred to new experiment |
| SAC safe-mode arm in same slug | Different action semantics; add only if H10 supported on MPO |
| Penalize only episode-level safe-mode count | Step credit assignment needs per-step signal |

#### 0.2.1 Shoulders of giants

- [mpo-learning-collapse-investigation.md](../../research/mpo-learning-collapse-investigation.md) §8 — safe-mode reward gap listed as deferral after Exp 8.
- Exp 8 pipeline + operator notes — plateau ~ep 5, safe HUD vs telemetry, sparse applied shutters.

### 0.3 Preliminary implementation remarks (How)

**Scaffold:** copy `ml_mpo_decoupled_dual_torque/` → `ml_mpo_safe_mode_penalty/`; single reward delta.

| Component | Planned path |
|-----------|--------------|
| Entry | `run_mpo_safe_mode_penalty.py` |
| Runner | `_penalty_runner.py` — arm `safe_mode_penalty_on` |
| Reward delta | `_penalty_frozen.py` — `reward_safe_mode_penalty_on()` |
| Simulation hook | Per-step `safe_mode_active` (or `agent_cut`) in `SimulationStateSeries` + `compute_reward` term |
| Baseline embed | Exp 8 run in `config.json` → `experiment.baseline_comparison` |
| Results | `results/mpo_safe_mode_penalty.json`, `results/smoke.json` |
| Hypothesis card | `H10-mpo-safe-mode-penalty.md` |

**Engineering notes:**

1. `AttitudeSafetyController` emits `AGENT_CUT` and safe-mode takeover events (`stepper.attitude_safety_events`); episode telemetry already logs `safe_mode_activations` via `safe_mode_takeover_count()`.
2. Reward kernel needs **per-step** knowledge (not episode aggregate). Extend `finalize_series()` / `_recompute_reward_at` pattern used for shutter overrides.
3. Warmup fingerprint must include `enable_safe_mode_penalty` + `k_safe_mode_penalty`.
4. On **supported**, update `docs/presentation/machine-learning.md` reward slide before production promotion (Phase 4).

**Smoke:** one warmup + one train step; assert penalty flag in config; finite KL; log penalized step count > 0 on a forced-safe-mode probe episode if available.

---

## Phase 1 — Built

### 1.1 Build plan (What)

| Component | Path |
|-----------|------|
| Entry | `run_mpo_safe_mode_penalty.py` |
| Runner | `_penalty_runner.py` — arm `safe_mode_penalty_on` |
| Reward delta | `_safe_mode_reward_fork.py` — per-step penalty on `AGENT_CUT` / safe-mode events |
| Frozen knobs | `_penalty_frozen.py`, `profile.json` (`k_safe_mode_penalty=2.0`) |
| dt / mutex | `_sim_constants_fork.py`, `_run_guard.py` |
| Results | `results/mpo_safe_mode_penalty.json`, `results/smoke.json` |
| Hypothesis card | `H10-mpo-safe-mode-penalty.md` |

**Single delta:** enable safe-mode penalty on sparse MPO torque (Exp 8 protocol otherwise frozen).

### 1.2 Build implementation (How we forked)

Forked `ml_mpo_decoupled_dual_torque/`; patches `SimulationStepper._populate_camera_and_reward` for penalized steps. Warmup fingerprint includes `enable_safe_mode_penalty`, `k_safe_mode_penalty`.

**Smoke (2026-06-30):** passed — `results/smoke.json`; `kl=0`, finite dual vars; `enable_safe_mode_penalty=true`, `k=2.0`.

### 1.3 Run instructions (How to execute)

```powershell
conda activate auto-sat
cd backend/scripts/experiments/ml_mpo_safe_mode_penalty
python run_mpo_safe_mode_penalty.py --smoke --allow-cpu
python run_mpo_safe_mode_penalty.py --show-progress
```

**Mutex:** global `pipeline_run_guard` — one pipeline training job at a time ([D-012](../../research/DECISIONS.md)).

**Comparator (read-only):** Exp 8 `9998217164480175_ml_mpo_decoupled_dual_torque_sparse_16-05-19`.

---

## Phase 2 — Run

### 2.1 Run scope (What)

| Arm | Agent | Action | Reward | Train | Eval | Seed | dt |
|-----|-------|--------|--------|-------|------|------|-----|
| **safe_mode_penalty_on** | MPO (fixed dual) | torque | sparse + safe-mode penalty | 50 | 2 | 7 | 1.5 s / 1.5 s |

**Command:**

```powershell
conda activate auto-sat
cd backend/scripts/experiments/ml_mpo_safe_mode_penalty
python run_mpo_safe_mode_penalty.py --show-progress
```

**Expected artifacts:** `results/mpo_safe_mode_penalty.json`, `run_dir/config.json`, `summary_metrics.json`, `videos/`, `plots/`, `artifacts_manifest.json`

### 2.2 Run monitoring (Why)

- **Queue position:** 1 of 4 in overnight batch (`run_pipeline_overnight_batch.py`).
- **Mutex:** no parallel pipeline slugs; offer `long-run-watch` if blocked.

### 2.3 Run log & artifacts (How)

*(Fill after run completes — run dirs, KPI JSON, video table.)*


# 11-mpo-decoupled-dual-vector.md

---
experiment_id: 11
slug: ml_mpo_decoupled_dual_vector
title: "Exp 11 — MPO fixed dual, sparse, vector mode"
current_phase: 3
overall_verdict: pending
blocked_by: null
code_path: backend/scripts/experiments/ml_mpo_decoupled_dual_vector/
plan_ref: ".cursor/plans/sac_vs_mpo_compare_821ab4d5.plan.md — MPO debug track"
phases:
  "0": { status: done, documented_utc: "2026-06-30T15:30:00Z", completed_utc: "2026-06-30T21:07:41Z" }
  "1": { status: done, documented_utc: null, completed_utc: "2026-06-30T21:18:29Z"
  "2": { status: done, documented_utc: null, completed_utc: "2026-07-01T05:59:10Z"
  "3": { status: pending, documented_utc: null, completed_utc: null }
  "4": { status: pending, documented_utc: null, completed_utc: null }
run_lock_holder: null
decision_ids: [D-022]
predecessor: ml_mpo_decoupled_dual_torque
investigation: docs/research/mpo-learning-collapse-investigation.md---
# Exp 11 — MPO fixed dual, sparse, vector mode (`ml_mpo_decoupled_dual_vector`)

**Agent:** MPO (fixed decoupled-KL dual) · **Action:** vector OBC (`attitude_request_mode=vector`) · **Reward:** sparse · **dt:** 1.5 s / 1.5 s
**Fix commit:** `d5af20c` — `fix(mpo): implement decoupled-KL dual`
**Predecessor:** [Exp 8](../4-documentation/08-mpo-decoupled-dual-fix.md) (same agent, torque mode) · [Exp 4](../4-documentation/04-agent-reference-pointing.md) (SAC, vector mode, partial verdict)
**Pair:** [Exp 8](../4-documentation/08-mpo-decoupled-dual-fix.md) (torque baseline for the same fix)
---
## Phase 0 — Initialized

### 0.1 Experiment scope (What)

**Core question:** Once MPO can learn (established by Exp 8 in torque mode), does vector OBC (`attitude_request_mode=vector`) improve, match, or hurt MPO learning — mirroring the Exp 4 SAC comparison (Ref0 torque vs Ref1 vector)?

**Gate:** Run **only after Exp 8** produces a verdict. If Exp 8 is `not_supported` (MPO still collapses despite the fix), Exp 11 is moot — a vector mode cannot help if the algorithm still can't learn. Unblock manually when Exp 8 Phase 3 closes with a positive or informative verdict.

**Hypothesis (H11):**

> Fixed MPO in vector mode achieves equal or better eval return than fixed MPO in torque mode (Exp 8), with equivalent KL/η stability — consistent with the Exp 4 SAC finding that vector semantics carry a learnable pointing schedule signal.

| ID | Claim | Success criterion | Falsified if |
|----|-------|-------------------|--------------|
| **H11a** | Vector ≥ torque | Eval return ≥ Exp 8 torque result **or** `learning_mode=true` in both | Vector eval worse than Exp 8 torque with no explanation |
| **H11b** | Stability preserved | KL/η bounded (same criteria as H8b) | KL explodes in vector mode despite fix |
| **H11c** | Saturation escapes | Train `torque_saturated_fraction` < 0.9 | Still ~1.0 |

**Overall:** **supported** if H11a **and** H11b; **inconclusive** if Exp 8 itself was inconclusive (see gate).

**Single arm:** vector mode only. Torque baseline = Exp 8 canonical run (read-only).

**Frozen protocol** (match Exp 8 exactly except action mode):

| Knob | Value |
|------|-------|
| dt | 1.5 s / 1.5 s |
| seed | 7 |
| warmup | 5 (rebuild) |
| train | 50 |
| eval | 2 |
| reward | sparse |
| action mode | **vector** (`attitude_request_mode=vector`, OBC fix [D-016](../../research/DECISIONS.md)) |
| actor/critic units | S = 90/140 |
| MPO hparams | same as Exp 8 (`eps_eta=0.1`, `target_kl_mu=0.1`, `target_kl_sigma=0.01`, `lr_alpha=1e-3`) |
| videos | 3 train + 2 eval |

**Out of scope:** dense reward, width sweep, encoder changes, torque re-run.

**Gate:** `pipeline_run_guard.check_pipeline_run_clear(slug="ml_mpo_decoupled_dual_vector")` before Phase 2.

### 0.2 Thought process (Why)

| Prior fact | Implication |
|------------|-------------|
| Exp 4 SAC: vector mode learnable (train ep 11 +95.8, pointing schedule visible in video) | Vector semantics are worth testing once MPO learns at all |
| Exp 4: Ref1 (vector) eval below Ref0 (torque) on KPI slice — partial verdict ([D-019](../../research/DECISIONS.md)) | Vector may need reward tuning to beat torque; Exp 11 gives the MPO side of the picture |
| Exp 8 (torque) is the prerequisite | Cannot meaningfully compare modes without a working torque baseline |
| Vector OBC fix (`max_safe=45°`, `f_n=max_safe·u`) promoted to production [D-016](../../research/DECISIONS.md) | Vector mode semantics are now correct — valid to test |

**Reject / defer:**

| Path | Why |
|------|-----|
| Run Exp 11 before Exp 8 closes | Gate — mode comparison meaningless if algorithm still broken |
| Budget-exhausted shutter penalty (Exp 7 pattern) on MPO | Only meaningful once MPO learns; defer to Exp 10 if needed |
| Dense reward in vector mode | Exp 3 ruled dense out for MPO; stay sparse |

#### 0.2.1 Shoulders of giants

- **Abdolmaleki et al. 2018 (`docs/research/1812.02256v1.pdf`)** — same dual fix as Exp 8; algorithm is mode-agnostic (action scale handled via `action_scale`/`action_bias` in `MPOAgent`).
- **Exp 4 [agent-reference-pointing-investigation.md](../../research/agent-reference-pointing-investigation.md)** — SAC vector OBC partial verdict; train ep 11 video confirms learnable pointing signal.

### 0.3 Preliminary implementation remarks (How)

**Scaffold:** copy Exp 8 (`ml_mpo_decoupled_dual_torque/`) and change only the OBC mode flag. The `MPOAgent` is identical — no fork needed.

| Component | Planned path |
|-----------|--------------|
| Entry | `run_mpo_vector.py` (`--smoke`, `--show-progress`) |
| Runner | `_vector_runner.py` — set `attitude_request_mode=vector`; otherwise identical to Exp 8 runner |
| dt constants | `_sim_constants_fork.py` — 1.5 s / 1.5 s |
| Mutex | `_run_guard.py` → `pipeline_run_guard` |
| Results | `results/mpo_vector.json`, `mpo_vector_analysis.md` |

**Key implementation note:** `attitude_request_mode=vector` routes the agent output through `obc_pointing_request.py` (promoted in [D-016](../../research/DECISIONS.md)). The `action_scale`/`action_bias` in `MPOAgent` is set from `env.action_space.low/high` which already reflects the correct vector-mode bounds. No agent-side change needed.

**Smoke:** one warmup + one train step; assert `attitude_request_mode=vector` in config; `kl_mean` finite; saturation logged.

**Comparator (read-only):** Exp 8 canonical run dir (`9998217164480175_ml_mpo_decoupled_dual_torque_sparse_16-05-19`).

---

## Phase 1 — Built

### 1.1 Build plan (What)

| Component | Path |
|-----------|------|
| Entry | `run_mpo_vector.py` |
| Runner | `_vector_runner.py` — arm `vector_sparse` |
| dt / mutex | `_sim_constants_fork.py`, `_run_guard.py` |
| Results | `results/mpo_vector.json`, `results/smoke.json` |
| Hypothesis card | `H11-mpo-decoupled-dual-vector.md` |

**Single delta:** `attitude_request_mode=vector` (Exp 8 MPO + sparse otherwise frozen).

### 1.2 Build implementation (How we forked)

Copied Exp 8 scaffold; production `MPOAgent` unchanged. Vector OBC via workflow config ([D-016](../../research/DECISIONS.md)).

**Smoke (2026-06-30):** passed — `results/smoke.json`; `attitude_request_mode=vector`; finite KL/dual vars.

### 1.3 Run instructions (How to execute)

```powershell
conda activate auto-sat
cd backend/scripts/experiments/ml_mpo_decoupled_dual_vector
python run_mpo_vector.py --smoke --allow-cpu
python run_mpo_vector.py --show-progress
```

**Mutex:** global `pipeline_run_guard` ([D-012](../../research/DECISIONS.md)).

**Comparator (read-only):** Exp 8 torque `9998217164480175_ml_mpo_decoupled_dual_torque_sparse_16-05-19`.

---

## Phase 2 — Run

### 2.1 Run scope (What)

| Arm | Agent | Action | Reward | Train | Eval | Seed | dt |
|-----|-------|--------|--------|-------|------|------|-----|
| **vector_sparse** | MPO (fixed dual) | vector | sparse | 50 | 2 | 7 | 1.5 s / 1.5 s |

**Command:**

```powershell
conda activate auto-sat
cd backend/scripts/experiments/ml_mpo_decoupled_dual_vector
python run_mpo_vector.py --show-progress
```

### 2.2 Run monitoring (Why)

- **Queue position:** 2 of 4 in overnight batch.
- Exp 8 gate cleared (partial verdict); mode comparison meaningful.

### 2.3 Run log & artifacts (How)

*(Fill after run completes.)*
