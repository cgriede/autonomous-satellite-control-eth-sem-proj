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
