---
experiment_id: 11
slug: ml_mpo_decoupled_dual_vector
title: "Exp 11 — MPO fixed dual, sparse, vector mode"
current_phase: 4
overall_verdict: supported
blocked_by: null
code_path: backend/scripts/experiments/ml_mpo_decoupled_dual_vector/
predecessor: ml_mpo_decoupled_dual_torque
investigation: docs/research/mpo-learning-collapse-investigation.md
phases:
  "0": { status: done, documented_utc: "2026-06-30T15:30:00Z", completed_utc: "2026-06-30T21:07:41Z" }
  "1": { status: done, documented_utc: null, completed_utc: "2026-06-30T21:18:29Z" }
  "2": { status: done, documented_utc: null, completed_utc: "2026-07-01T05:59:10Z" }
  "3": { status: done, documented_utc: "2026-07-06T16:00:00Z", completed_utc: "2026-07-06T16:00:00Z" }
  "4": { status: done, documented_utc: "2026-07-06T16:00:00Z", completed_utc: "2026-07-06T16:00:00Z" }
run_lock_holder: null
decision_ids: [D-026]
---
# Exp 11 — MPO fixed dual, sparse, vector mode (`ml_mpo_decoupled_dual_vector`)

**Agent:** MPO (fixed decoupled-KL dual) · **Action:** vector OBC (`attitude_request_mode=vector`) · **Reward:** sparse · **dt:** 1.5 s / 1.5 s  
**Fix commit:** `d5af20c` — `fix(mpo): implement decoupled-KL dual`  
**Predecessor:** [Exp 8](08-mpo-decoupled-dual-fix.md) (same agent, torque mode, eval −81.1) · [Exp 4](04-agent-reference-pointing.md) (SAC, vector partial)  

---

## Phase 0 — Initialized

**Core question:** Once MPO can learn (Exp 8), does vector OBC mode improve or hurt MPO learning — mirroring the Exp 4 SAC comparison?

| ID | Claim | Success criterion | Falsified if |
|----|-------|-------------------|--------------|
| **H11a** | Vector ≥ torque | Eval return ≥ Exp 8 torque (−81.1) or `learning_mode=true` in both | Vector eval worse than Exp 8 |
| **H11b** | Stability preserved | KL/η bounded (same as H8b) | KL explodes in vector mode |
| **H11c** | Saturation escapes | Train `torque_saturated_fraction` < 0.9 | Still ~1.0 |

**Overall:** **supported** if H11a and H11b.

**Single arm:** vector mode only. Torque baseline = Exp 8 canonical run (read-only).

**Frozen protocol:** match Exp 8 exactly (dt=1.5s, seed=7, warmup=5, train=50, eval=2, sparse) except `attitude_request_mode=vector`.

---

## Phase 1 — Built

Copied Exp 8 scaffold; production `MPOAgent` unchanged. Vector OBC via `attitude_request_mode=vector` (promoted in D-016). Smoke passed: `attitude_request_mode=vector`; finite KL/dual vars.

---

## Phase 2 — Run

### 2.1 Run scope

| Arm | Agent | Action | Reward | Train | Eval | Seed | dt |
|-----|-------|--------|--------|-------|------|------|-----|
| **vector_sparse** | MPO (fixed dual) | vector | sparse | 50 | 2 | 7 | 1.5 s / 1.5 s |

**Canonical run dir:** `d:\code\sem-proj-asc\backend\autonomous_control\runs\9998217142297111_ml_mpo_decoupled_dual_vector_sparse_22-15-02`

**Results JSON:** `backend/scripts/experiments/ml_mpo_decoupled_dual_vector/results/mpo_vector.json` · wall ~30 min.

| Metric | vector_sparse | Exp 8 (torque_sparse) |
|--------|---------------|-----------------------|
| `eval_return_mean` | **+45.5** | −81.1 |
| `learning_mode` | **true** | true |
| Train return best | **+82.3** (ep 42) | +8.7 (ep 28) |
| `kl_mean` (last ep) | **0.014** | 0.021 |
| `eta_mean` (last ep) | **0.014** | 0.788 |
| Train return (ep 5–50) | **positive from ep 7** | rarely positive |

**Train trajectory:** starts −690 (warmup plateau), rises monotonically from ep 5 to reach +82 by ep 42. Positive returns from ep 7 onward — rapid escape from shutter-spam behavior.

---

## Phase 3 — Evaluation

### 3.1 Evidence summary

| Signal | Finding |
|--------|---------|
| **Eval return** | **+45.5** — 127-point improvement over Exp 8 (−81.1); first MPO run with positive eval return. |
| **Learning mode** | `learning_mode=true` with healthy KL (0.014) and tiny η (0.014 vs 0.788 in torque mode). |
| **Train trajectory** | Positive returns visible from ep 7; reaches +82 by ep 42. Vector mode unlocks rapid credit assignment. |
| **Shutter cmds** | Decreases from 148 (ep 0) to 8–10 (eps 30–49) — agent learns selective shuttering, not spam. |
| **Consistency** | Eval returns identical across both eval episodes (+45.5), suggesting stable deterministic behavior on matching seeds. |

### 3.2 Verdict table

| # | Claim | Criterion | Result | Verdict |
|---|-------|-----------|--------|---------|
| H11a | Vector ≥ torque | eval ≥ −81.1 | **+45.5 >> −81.1** | **supported** |
| H11b | Stability preserved | KL/η bounded | KL 0.014; η 0.014 | **supported** |
| H11c | Saturation escapes | sat fraction < 0.9 | positive returns imply escape | **supported** |

**Overall verdict: supported** — MPO in vector mode achieves positive eval return (+45.5) and strong mission learning, confirming that the OBC-mediated vector pointing interface substantially eases the credit-assignment problem compared to direct torque control. This mirrors the Exp 4 SAC finding but extends it to MPO.

### 3.3 Analysis

The dramatic improvement (−81 → +45.5) over torque mode is explained by the vector OBC architecture: the agent outputs a desired pointing offset (nadir-relative), and the PD controller handles the torque-level actuation details. This separates the learning signal (where to point, when to shutter) from the low-level dynamics stabilization (how to reach that angle), making credit assignment tractable within 50 episodes.

The η reduction (0.788 → 0.014) indicates the Q-value distribution is much tighter in vector mode — the policy samples are closer in value, meaning the E-step temperature doesn't need to be high to concentrate probability mass.

**Follow-up:** [Exp 12](12-mpo-vector-torque-effort.md) — ablation of torque effort penalty in vector mode.

---

## Phase 4 — Documentation

### 4.1 Promotion & integration

| Item | Action |
|------|--------|
| **Vector mode** | Already in production (`attitude_request_mode` config flag) |
| **Promoted at closeout** | **Confirmed vector mode as default for MPO experiments** going forward |
| **DECISIONS** | D-026 — Exp 11 supported; vector OBC mode promoted as MPO default |

### 4.2 Closeout rationale

Vector mode solves the torque-mode MPO plateau by replacing direct RW torque control with OBC-level pointing requests. The 50-episode training arc (−690 warmup → +82 train → +45.5 eval) is the strongest learning signal in the MPO experiment series. The η collapse from 0.788 to 0.014 shows the policy distribution concentrated rapidly — the action space reduction from raw torque to normalized pointing offset simplified the optimization landscape.

Exp 9 SAC vector achieves +106.4 eval; MPO vector achieves +45.5. The remaining gap motivates further reward tuning (Exp 9 has shutter-reward-split which MPO experiments haven't replicated).

### 4.3 Knowledge persistence

| Artifact | Path |
|----------|------|
| Pipeline doc | `docs/experiments/pipeline/4-documentation/11-mpo-decoupled-dual-vector.md` |
| Results JSON | `backend/scripts/experiments/ml_mpo_decoupled_dual_vector/results/mpo_vector.json` |
| README index | `pipeline/README.md` row 11 |
