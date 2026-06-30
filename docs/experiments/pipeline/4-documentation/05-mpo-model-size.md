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
