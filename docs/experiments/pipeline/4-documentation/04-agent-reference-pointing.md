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
