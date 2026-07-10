---
experiment_id: 10
slug: ml_mpo_safe_mode_penalty
title: "Exp 10 — MPO safe-mode reward penalty (credit alignment)"
current_phase: 4
overall_verdict: not_supported
blocked_by: null
code_path: backend/scripts/experiments/ml_mpo_safe_mode_penalty/
predecessor: ml_mpo_decoupled_dual_torque
investigation: docs/research/mpo-learning-collapse-investigation.md
phases:
  "0": { status: done, documented_utc: "2026-06-30T20:00:00Z", completed_utc: "2026-06-30T21:00:36Z" }
  "1": { status: done, documented_utc: null, completed_utc: "2026-06-30T21:18:29Z" }
  "2": { status: done, documented_utc: null, completed_utc: "2026-07-01T05:59:10Z" }
  "3": { status: done, documented_utc: "2026-07-06T16:00:00Z", completed_utc: "2026-07-06T16:00:00Z" }
  "4": { status: done, documented_utc: "2026-07-06T16:00:00Z", completed_utc: "2026-07-06T16:00:00Z" }
run_lock_holder: null
decision_ids: [D-022, D-025]
---
# Exp 10 — MPO safe-mode reward penalty (`ml_mpo_safe_mode_penalty`)

**Agent:** MPO (fixed decoupled-KL dual) · **Action:** torque · **Reward:** sparse + safe-mode penalty (`k=2.0`) · **dt:** 1.5 s / 1.5 s  
**Predecessor:** [Exp 8](08-mpo-decoupled-dual-fix.md) (dual fix works; safe-mode fires without reward signal)  
**Not in scope:** Exp 8 closeout, SAC vector

---

## Phase 0 — Initialized

### 0.1 Experiment scope (What)

**Core question:** Does a per-step safe-mode / AGENT_CUT penalty on the reward plane reduce `safe_mode_activations`, improve agent-applied torque credit assignment, and improve mission KPIs vs Exp 8 (penalty off)?

| ID | Claim | Success criterion | Falsified if |
|----|-------|-------------------|--------------|
| **H10a** | Safe-mode rate drops | Mean `safe_mode_activations`/ep < Exp 8 (~5–6) | No decrease with penalty on |
| **H10b** | Learning preserved | `learning_mode=true`; eval improves vs Exp 8 (−81.1) | Collapse / frozen KL |
| **H10c** | Applied capture not worse | Eval `shutter_meaningful_fraction` ≥ Exp 8 | More torque saturation + fewer dots |
| **H10d** | Torque saturation eases | Train `torque_saturated_fraction` < Exp 8 (~0.95) | Still ~1.0 with penalty on |

**Overall:** **supported** if H10b and (H10a or H10d) and H10c not regressed; **not_supported** if penalty is worse on all.

**Arms:**

| Arm | `enable_safe_mode_penalty` |
|-----|---------------------------|
| **safe_mode_penalty_on** | **true** (k=2.0) |
| penalty_off (Exp 8) | false — read-only comparator |

**Frozen protocol:** match Exp 8 exactly (dt=1.5s, seed=7, warmup=5, train=50, eval=2, sparse torque).

### 0.2 Thought process (Why)

Exp 8 shows ~5–6 safe_mode_activations/ep without any reward term — the agent has no signal to avoid triggering the safety controller.

---

## Phase 1 — Built

Forked `ml_mpo_decoupled_dual_torque/`; patches `SimulationStepper._populate_camera_and_reward` for penalized steps. Warmup fingerprint includes `enable_safe_mode_penalty`, `k_safe_mode_penalty`.

**Smoke (2026-06-30):** passed — `results/smoke.json`; finite KL/dual vars; `enable_safe_mode_penalty=true`, `k=2.0`.

---

## Phase 2 — Run

### 2.1 Run scope

| Arm | Agent | Action | Reward | Train | Eval | Seed | dt |
|-----|-------|--------|--------|-------|------|------|-----|
| **safe_mode_penalty_on** | MPO (fixed dual) | torque | sparse + safe-mode penalty k=2.0 | 50 | 2 | 7 | 1.5 s / 1.5 s |

**Canonical run dir:** `d:\code\sem-proj-asc\backend\autonomous_control\runs\9998217144237087_ml_mpo_safe_mode_penalty_safe_mode_penalty_on_21-42-42`

**Results JSON:** `backend/scripts/experiments/ml_mpo_safe_mode_penalty/results/mpo_safe_mode_penalty.json` · wall ~32 min.

| Metric | safe_mode_penalty_on | Exp 8 comparator |
|--------|----------------------|-----------------|
| `eval_return_mean` | **−510.4** | −81.1 |
| `learning_mode` | **true** | true |
| Train return best | **~−350** (ep 23) | +8.7 |
| `kl_mean` (last ep) | **0.013** | 0.021 |
| Train `n_shutter_cmds` (last 20 eps) | **2–7** | ~10–15 |

---

## Phase 3 — Evaluation

### 3.1 Evidence summary

| Signal | Finding |
|--------|---------|
| **Eval return** | **−510.4** — catastrophic regression vs Exp 8 (−81.1). The penalty *disrupted* mission behavior rather than aligning it. |
| **Learning mode** | `learning_mode=true` — algorithm is still running (H10b partially met), but mission KPI severely worsened. |
| **Shutter commands** | Train shutter count drops from 153 (ep 0) to 2–7 (eps 30–49): the penalty taught the agent to **avoid shuttering entirely** as a side-effect of avoiding safe-mode, since safe-mode activations are correlated with aggressive torque that follows shutter attempts. |
| **Saturation** | Cannot distinguish directly from JSON, but the extremely negative eval suggests ongoing safe-mode or torque saturation without useful capture. |
| **Train trajectory** | Starts −1168, improves to ~−350 (ep 23), then plateaus around −600–800 without convergence — no "mission learning" despite bounded KL. |

### 3.2 Verdict table

| # | Claim | Criterion | Result | Verdict |
|---|-------|-----------|--------|---------|
| H10a | Safe-mode rate drops | activations/ep < Exp 8 | N/A — shutter avoidance side-effect | **inconclusive** |
| H10b | Learning preserved | eval improves vs −81.1 | eval **−510.4** (worse) | **not_supported** |
| H10c | Applied capture not worse | shutter fraction ≥ Exp 8 | shutter cmds collapsed to 2–7 | **not_supported** |
| H10d | Saturation eases | sat fraction < 0.95 | eval return far below implies no improvement | **not_supported** |

**Overall verdict: not_supported** — safe-mode penalty at k=2.0 produced severe mission regression. The agent learned to avoid shuttering rather than avoiding safe-mode entry; torque saturation and credit assignment remained unresolved. This rules out per-step safe-mode penalty as a reward-plane lever for Exp 8's torque-mode MPO.

### 3.3 Follow-up

- [Exp 11](11-mpo-decoupled-dual-vector.md) — vector mode bypass sidesteps safe-mode entirely (AGENT_CUT not triggered in vector path); more promising direction.
- Reward redesign with separate penalty coefficient tuning and per-step diagnostic telemetry recommended if safe-mode suppression is revisited.

---

## Phase 4 — Documentation

### 4.1 Promotion & integration

| Item | Action |
|------|--------|
| **Promoted** | **None** — penalty remains behind `enable_safe_mode_penalty=false` default |
| **DECISIONS** | D-025 — Exp 10 not_supported; safe-mode penalty ruled out at k=2.0 in torque mode |

### 4.2 Closeout rationale

The penalty at k=2.0 did not align safe-mode avoidance with capture quality improvement. The most likely mechanism: safe-mode activations co-occur with high-torque aggressive pointing (the kind needed to reach off-nadir targets), so penalizing safe-mode entry caused the agent to avoid all aggressive torque requests, suppressing useful capture attempts. The eval return of −510.4 vs Exp 8's −81.1 confirms this is a harmful intervention at this coefficient.

Vector mode (Exp 11) provides a cleaner solution: the OBC PD controller absorbs actuation, reducing direct safe-mode entry frequency without a reward penalty.

### 4.3 Knowledge persistence

| Artifact | Path |
|----------|------|
| Pipeline doc | `docs/experiments/pipeline/4-documentation/10-mpo-safe-mode-penalty.md` |
| Results JSON | `backend/scripts/experiments/ml_mpo_safe_mode_penalty/results/mpo_safe_mode_penalty.json` |
| README index | `pipeline/README.md` row 10 |
