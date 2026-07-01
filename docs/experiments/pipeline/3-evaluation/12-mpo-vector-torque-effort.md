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
