---
experiment_id: 3
slug: ml_sac_mpo_compare
title: "Exp 3 — SAC vs MPO compare"
current_phase: 4
overall_verdict: supported
blocked_by: null
code_path: backend/scripts/experiments/ml_sac_mpo_compare/
plan_ref: ".cursor/plans/sac_vs_mpo_compare_821ab4d5.plan.md — Track 3"
phases:
  "0": { status: done, documented_utc: "2026-06-29T20:00:00Z", completed_utc: "2026-06-29T21:30:00Z" }
  "1": { status: done, documented_utc: "2026-06-29T21:30:00Z", completed_utc: "2026-06-30T13:00:00Z", arms: [compare_sac, compare_mpo] }
  "2": { status: done, documented_utc: "2026-06-30T13:00:00Z", completed_utc: "2026-06-30T13:00:00Z" }
  "3": { status: done, documented_utc: "2026-06-30T13:00:00Z", completed_utc: "2026-06-30T13:00:00Z" }
  "4": { status: pending, documented_utc: null, completed_utc: null }
run_lock_holder: null
decision_ids: [D-002, D-007, D-011, D-012, D-013, D-017]
---

# Exp 3 — SAC vs MPO compare (`ml_sac_mpo_compare`)

**Plan:** [sac_vs_mpo_compare plan](../../../../.cursor/plans/sac_vs_mpo_compare_821ab4d5.plan.md) **§ Track 3**  
**Agents:** SAC sparse + MPO dense · **dt:** 1.5 s / 1.5 s  
**Investigation:** [sac-mpo-compare-investigation.md](../../research/sac-mpo-compare-investigation.md)

---

## Phase 0 — Initialized

### 0.1 Experiment scope (What)

**Core question:** Does **SAC + sparse** vs **MPO + dense** (H6 formula) produce a fair algorithm comparison at dt 1.5 s — and can dense credit unblock MPO?

**Hypothesis (H3):** SAC learns; MPO dense achieves `learning_mode=true` or ≥20% eval improvement vs H6 (−243).

| ID | Claim |
|----|-------|
| H3a | SAC sparse learnable |
| H3b | Dense unblocks MPO vs H6 |
| H3c | Algorithm × reward pairing matters |
| H3d | Early abort informative |

### 0.2 Thought process (Why)

Prior H4 SAC learned; H1a/H6 MPO collapsed at dt 1.5 s. Isolates **algorithm × reward** after Exp 1–2.

### 0.3 Preliminary implementation remarks (How)

Slug `ml_sac_mpo_compare/`; patience early abort; `_compare_runner.py`.

---

## Phase 1 — Built

### 1.1 Build plan (What)

SAC sparse vs MPO dense; `results/compare_sac_mpo.json`; `compare_sac_mpo_analysis.md`.

### 1.2 Build implementation (How we forked)

Smoke passed; `_training_loop_fork.py` patience; global mutex.

### 1.3 Run instructions (How to execute)

`python run_sac_mpo_compare.py --show-progress`

---

## Phase 2 — Run

### 2.1 Run scope (What)

**Run at:** 2026-06-29 23:06–23:38 UTC · [`results/compare_sac_mpo.json`](../../../../backend/scripts/experiments/ml_sac_mpo_compare/results/compare_sac_mpo.json)

| Arm | Agent | Reward | `learning_mode` | Best train | Eval mean | Eps | Wall |
|-----|-------|--------|---------------|------------|-----------|-----|------|
| `compare_sac` | SAC | sparse | **true** | +5.33 | −22.17 | 37 | ~16 min |
| `compare_mpo` | MPO | dense | false | −51.6 | −51.6 | 22 | ~16 min |

**Note:** `patience_episodes=20` in JSON (not charter 10). Both arms early-aborted.

### 2.2 Run monitoring (Why)

Sequential arms under global mutex; no parallel slugs.

### 2.3 Run log & artifacts (How)

**compare_sac**

| Artifact | Path |
|----------|------|
| Run dir | `d:\code\sem-proj-asc\backend\autonomous_control\runs\9998217225628033_ml_compare_compare_sac_23-06-11\` |
| Eval ep 0 | `...\videos\eval_ep_0_rank1.mp4` |
| Train best (ep 16) | `...\videos\train_ep_16_rank1.mp4` |
| Manifest | `...\artifacts_manifest.json` |

**compare_mpo**

| Artifact | Path |
|----------|------|
| Run dir | `d:\code\sem-proj-asc\backend\autonomous_control\runs\9998217224670341_ml_compare_compare_mpo_23-22-09\` |
| Eval ep 0 | `...\videos\eval_ep_0_rank1.mp4` |
| Manifest | `...\artifacts_manifest.json` |

MPO diagnostics: eval `shutter_meaningful_fraction=0`; train torque saturated **~99.8%**; `kl_mean ≈ 3.8×10⁵`.

---

## Phase 3 — Evaluation

### 3.1 Claims & success criteria (What)

Restated H3a–H3d from Phase 0.

### 3.2 Evidence summary (Why)

- **H3a:** SAC `learning_mode=true`; best train crosses positive (+5.33 vs ep0 −72).
- **H3b:** MPO `learning_mode=false`; eval −51.6 vs H6 −243 (**~79% better**) but flat plateau; KL blow-up persists — **partial** on floor only, not sustained learning.
- **H3c:** SAC clearly separates from MPO on learning signal and eval (−22 vs −52).
- **H3d:** Early abort fired; SAC had improving segments before abort.

### 3.3 Verdict table (How we decided)

| # | Claim | **Verdict** |
|---|-------|-------------|
| H3a | SAC learnable | **supported** |
| H3b | Dense unblocks MPO | **not_supported** (floor ↑ only) |
| H3c | Algorithm × reward matters | **supported** |
| H3d | Early abort informative | **supported** |

**Overall verdict:** **supported** (H3a + H3c; charter rule: SAC learns, MPO dense does not sustain learning vs H6 goal).

**Implication for Exp 5:** MPO reward mode for width ablation — sparse used in practice; dense did not justify width sweep alone.

*(Phase 4 pending.)*
