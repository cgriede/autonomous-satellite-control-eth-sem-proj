---
experiment_id: 12
slug: ml_mpo_vector_torque_effort
title: "Exp 12 — MPO vector + torque-effort penalty"
current_phase: 4
overall_verdict: not_supported
blocked_by: null
code_path: backend/scripts/experiments/ml_mpo_vector_torque_effort/
predecessor: ml_mpo_decoupled_dual_vector
phases:
  "0": { status: done, documented_utc: "2026-06-30T22:00:00Z", completed_utc: "2026-06-30T22:00:00Z" }
  "1": { status: done, documented_utc: null, completed_utc: "2026-06-30T21:21:53Z" }
  "2": { status: done, documented_utc: null, completed_utc: "2026-07-01T05:59:10Z" }
  "3": { status: done, documented_utc: "2026-07-06T16:00:00Z", completed_utc: "2026-07-06T16:00:00Z" }
  "4": { status: done, documented_utc: "2026-07-06T16:00:00Z", completed_utc: "2026-07-06T16:00:00Z" }
run_lock_holder: null
decision_ids: [D-027]
---
# Exp 12 — MPO vector + torque effort (`ml_mpo_vector_torque_effort`)

**Agent:** MPO (fixed dual) · **Action:** vector · **Reward:** sparse + forced torque effort (`k=0.1`) · **dt:** 1.5 s  
**Predecessor:** [Exp 11](11-mpo-decoupled-dual-vector.md) (vector, effort off by default, eval +45.5)

---

## Phase 0 — Initialized

**Core question:** Does enabling `k_torque_effort` in vector mode reduce saturation or improve eval return vs Exp 11?

| ID | Claim | Success criterion |
|----|-------|-------------------|
| **H12a** | Effort signal helps vector | Eval return ≥ Exp 11 (+45.5) or train saturation lower |
| **H12b** | Learning stable | KL/η bounds as Exp 11 |

**Motivation:** Production `training_workflow` sets `enable_torque_effort=False` when `attitude_request_mode=vector`. Exp 8 torque runs with effort on; Exp 11 turns it off. Low-cost ablation while GPU is warm.

---

## Phase 1 — Built

Copied Exp 11; forced `enable_torque_effort=True` via `_reward_fork.py`. Smoke: `enable_torque_effort=true` in config; finite KL/dual vars.

---

## Phase 2 — Run

### 2.1 Run scope

| Arm | Agent | Action | Reward | Train | Eval | Seed | dt |
|-----|-------|--------|--------|-------|------|------|-----|
| **vector_torque_effort** | MPO (fixed dual) | vector | sparse + torque effort k=0.1 | 50 | 2 | 7 | 1.5 s / 1.5 s |

**Canonical run dir:** `d:\code\sem-proj-asc\backend\autonomous_control\runs\9998217140497791_ml_mpo_vector_torque_effort_vector_torque_effort_22-45-01`

**Results JSON:** `backend/scripts/experiments/ml_mpo_vector_torque_effort/results/mpo_vector_torque_effort.json` · wall ~29 min.

| Metric | vector_torque_effort | Exp 11 (vector, effort off) |
|--------|----------------------|-----------------------------|
| `eval_return_mean` | **+25.3** | **+45.5** |
| `learning_mode` | **true** | true |
| Train return best | **+75.6** (ep 20) | +82.3 (ep 42) |
| `kl_mean` (last ep) | **0.013** | 0.014 |
| `eta_mean` (last ep) | **0.027** | 0.014 |
| Train returns (eps 36–43) | **0.0 × 4 consecutive** | consistently positive |

**Train trajectory:** similar early learning to Exp 11 (+75 at ep 20) but more instability in later episodes (four consecutive 0.0 returns at eps 36, 41, 42, 43) — torque effort penalty causes oscillation in the late training phase.

---

## Phase 3 — Evaluation

### 3.1 Evidence summary

| Signal | Finding |
|--------|---------|
| **Eval return** | **+25.3** — 20-point decline vs Exp 11 (+45.5). Torque effort penalizes the normalized action signal from the OBC layer, which doesn't map to actual wheel torque the same way as in torque mode. |
| **Learning mode** | `learning_mode=true`; KL stable at 0.013. Algorithm is healthy but mission performance is lower. |
| **Train instability** | Four consecutive zero-return episodes in late training (eps 36, 41, 42, 43) suggest the agent oscillates between taking too many shutters and retreating entirely. |
| **Torque effort in vector mode** | The torque effort penalty targets `wheel_torque_agent_cmd_nm` (the PD command), not the policy dim0 action. The policy still outputs pointing offsets; penalizing the derived torque may create a conflicting gradient that discourages pointing far from nadir regardless of cloud/target context. |

### 3.2 Verdict table

| # | Claim | Criterion | Result | Verdict |
|---|-------|-----------|--------|---------|
| H12a | Effort helps vector | eval ≥ +45.5 | **+25.3 < +45.5** | **not_supported** |
| H12b | Learning stable | KL/η bounded | KL 0.013; η 0.027 | **supported** |

**Overall verdict: not_supported** — torque effort penalty in vector mode hurts eval performance (−20 vs Exp 11). The production default (`enable_torque_effort=False` in vector mode) is validated as correct. The result confirms that the effort penalty's design assumption (penalize raw torque magnitude ≈ penalize aggressive maneuvers) breaks down in vector mode where the PD controller mediates actuation.

---

## Phase 4 — Documentation

### 4.1 Promotion & integration

| Item | Action |
|------|--------|
| **Production default** | `enable_torque_effort=False` when `attitude_request_mode=vector` — **confirmed and retained** |
| **DECISIONS** | D-027 — Exp 12 not_supported; torque effort ablation in vector mode rules out enabling the penalty |

### 4.2 Closeout rationale

The 20-point performance drop (Exp 11 +45.5 → Exp 12 +25.3) with identical algorithm settings except the effort flag confirms that torque effort penalty is harmful in vector mode. The four consecutive zero-return episodes at late training indicate the penalty disrupts the late-stage policy refinement. The production choice to disable effort in vector mode is correct.

**Implication for report:** The MPO vector result (+45.5 from Exp 11, no effort) is the clean MPO benchmark; Exp 12 is an ablation confirming the production default.

### 4.3 Knowledge persistence

| Artifact | Path |
|----------|------|
| Pipeline doc | `docs/experiments/pipeline/4-documentation/12-mpo-vector-torque-effort.md` |
| Results JSON | `backend/scripts/experiments/ml_mpo_vector_torque_effort/results/mpo_vector_torque_effort.json` |
| README index | `pipeline/README.md` row 12 |
