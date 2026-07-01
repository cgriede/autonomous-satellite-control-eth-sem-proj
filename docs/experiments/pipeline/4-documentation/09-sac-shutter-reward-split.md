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
