---
experiment_id: 9
slug: ml_sac_shutter_reward_split
title: "Exp 9 — SAC shutter reward split (waste off, budget on)"
current_phase: 1
overall_verdict: pending
blocked_by: null
code_path: backend/scripts/experiments/ml_sac_shutter_reward_split/
predecessor: ml_sac_vector_budget_penalty
phases:
  "0": { status: done, documented_utc: "2026-06-30T18:00:00Z", completed_utc: "2026-06-30T18:00:00Z" }
  "1": { status: done, documented_utc: "2026-06-30T18:00:00Z", completed_utc: "2026-06-30T18:00:00Z" }
  "2": { status: pending, documented_utc: null, completed_utc: null }
  "3": { status: pending, documented_utc: null, completed_utc: null }
  "4": { status: pending, documented_utc: null, completed_utc: null }
run_lock_holder: null
decision_ids: []
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

*(Phases 2–4 appended after run.)*
