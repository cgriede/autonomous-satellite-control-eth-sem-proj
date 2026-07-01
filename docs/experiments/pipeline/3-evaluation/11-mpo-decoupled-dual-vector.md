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
