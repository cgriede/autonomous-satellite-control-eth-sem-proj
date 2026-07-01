---
experiment_id: 8
slug: ml_mpo_decoupled_dual_torque
title: "Exp 8 — MPO fixed dual, sparse, torque mode"
current_phase: 4
overall_verdict: partial
blocked_by: null
code_path: backend/scripts/experiments/ml_mpo_decoupled_dual_torque/
plan_ref: ".cursor/plans/sac_vs_mpo_compare_821ab4d5.plan.md — MPO debug track"
phases:
  "0": { status: done, documented_utc: "2026-06-30T15:10:00Z", completed_utc: "2026-06-30T15:40:00Z" }
  "1": { status: done, documented_utc: null, completed_utc: "2026-06-30T16:38:06Z", notes: "smoke + canonical 50-ep run" }
  "2": { status: done, documented_utc: "2026-06-30T20:43:59Z", completed_utc: "2026-06-30T20:43:59Z" }
  "3": { status: done, documented_utc: "2026-06-30T20:43:59Z", completed_utc: "2026-06-30T20:56:08Z" }
  "4": { status: done, documented_utc: "2026-06-30T20:56:00Z", completed_utc: "2026-06-30T20:56:00Z" }
run_lock_holder: null
decision_ids: [D-023, D-024]
predecessor: ml_mpo_model_size
investigation: docs/research/mpo-learning-collapse-investigation.md
---
# Exp 8 — MPO fixed dual, sparse, torque mode (`ml_mpo_decoupled_dual_torque`)

**Agent:** MPO (fixed decoupled-KL dual) · **Action:** torque (production default) · **Reward:** sparse · **dt:** 1.5 s / 1.5 s
**Fix commit:** `d5af20c` — `fix(mpo): implement decoupled-KL dual`
**Predecessor:** [Exp 5](../4-documentation/05-mpo-model-size.md) (torque mode, identical collapse across widths — pre-fix)
**Investigation:** [mpo-learning-collapse-investigation.md](../../research/mpo-learning-collapse-investigation.md) · [D-023](../../research/DECISIONS.md) · [D-024](../../research/DECISIONS.md)
**Pair:** [Exp 11](../1-built/11-mpo-decoupled-dual-vector.md) (same fixed agent, vector mode)

---

## Phase 0 — Initialized

### 0.1 Experiment scope (What)

**Core question:** With the MPO dual now correctly implemented (E-step Q-value dual η + enforced M-step α_μ/α_Σ trust region, committed in `d5af20c`), does MPO achieve `learning_mode=true` on sparse reward in torque mode — the same mode that produced the −51.6 / −243.5 collapse in all prior runs?

**Hypothesis (H8):**

> The fixed MPO agent achieves `learning_mode=true` (returns rise above the −51.6 floor established by Exp 3/5) with bounded KL/η, on the same sparse + torque + dt-1.5 s protocol that previously collapsed.

| ID | Claim | Success criterion | Falsified if |
|----|-------|-------------------|--------------|
| **H8a** | Dual fix unblocks learning | `learning_mode=true` **or** eval return ≥ −41 (≥20% above −51.6 floor) with rising best-train trajectory | Returns still pin at −51.6 floor |
| **H8b** | KL/η stay bounded | `kl_mean` stays within ~10× target over 50 eps; no monotonic η→1e11 ramp | KL/η still explode |
| **H8c** | Policy escapes saturation | Train `torque_saturated_fraction` < 0.9 (was 0.998 in all prior MPO runs) | Still ~1.0 |
| **H8d** | α_μ/α_Σ remain finite and active | Both alpha values track KL constraint errors; neither collapses to 0 or explodes | Either hits extremes immediately |

**Overall:** **supported** if H8a **and** H8b; **not_supported** otherwise (then H8d still resolves symptom-vs-cause for Exp 11 design).

**Single arm:** no control re-run of the broken implementation needed — Exp 3/5 already provide the pre-fix baseline at identical protocol.

**Frozen protocol** (match Exp 3 `compare_mpo` / Exp 5 `mpo_s` exactly for comparability):

| Knob | Value |
|------|-------|
| dt | 1.5 s / 1.5 s |
| seed | 7 |
| warmup | 5 (rebuild) |
| train | 50 |
| eval | 2 |
| reward | sparse |
| action mode | **torque** (production default) |
| actor/critic units | S = 90/140 (production default) |
| new hparams | `eps_eta=0.1`, `target_kl_mu=0.1`, `target_kl_sigma=0.01`, `lr_alpha=1e-3` (fixed-dual defaults from `MPOConfig`) |
| videos | 3 train + 2 eval |

**Out of scope:** dense reward (Exp 3), width sweep (Exp 5), vector mode (→ Exp 11), encoder changes.

**Gate:** `pipeline_run_guard.check_pipeline_run_clear(slug="ml_mpo_decoupled_dual_torque")` before Phase 2.

### 0.2 Thought process (Why)

| Prior fact | Implication |
|------------|-------------|
| All MPO runs pre-fix collapsed to −51.6 / −243.5 within ep 1 | torque + sparse is the hard baseline to beat |
| `h1b_stable_eta`: η frozen=1.0 still explodes KL, critic diverges | M-step unconstrained — α fix is the lever |
| KL≈5.6e4 at ep 0 while η≈4 ([investigation §3a](../../research/mpo-learning-collapse-investigation.md)) | η lag confirms dual is the cause, not symptom |
| SAC learns sparse torque (Exp 3, [D-017](../../research/DECISIONS.md)) | Environment is learnable — MPO just needed the correct algorithm |
| Width identical collapse (Exp 5, [D-018](../../research/DECISIONS.md)) | Not capacity — the fix targets the right lever |

#### 0.2.1 Shoulders of giants

- **Abdolmaleki et al. 2018 (`docs/research/1812.02256v1.pdf`)** — decoupled-KL MPO: E-step Q-dual η + separate α_μ/α_Σ M-step trust region. The exact structure implemented in `d5af20c`.
- **Abdolmaleki et al. 2018 (`arXiv:1806.06920`)** — MPO robustness claim: same hyperparameters across tasks when the dual is correct.

### 0.3 Preliminary implementation remarks (How)

**Scaffold:** copy `ml_mpo_model_size/` (nearest MPO fork); swap `MPOConfig` fields to production defaults (the fix is already in production `MPOConfig` / `controller_agent.py`). No agent fork needed — use `MPOAgent` directly.

| Component | Planned path |
|-----------|--------------|
| Entry | `run_mpo_torque.py` (`--smoke`, `--show-progress`) |
| Runner | `_torque_runner.py` — standard MPO train/eval loop, no reward or agent fork |
| dt constants | `_sim_constants_fork.py` — 1.5 s / 1.5 s |
| Mutex | `_run_guard.py` → `pipeline_run_guard` |
| Results | `results/mpo_torque.json`, `mpo_torque_analysis.md` |

**Smoke:** one warmup + one train step; assert `log_alpha_mu` and `log_alpha_sigma` present on agent; check `kl_mean` finite in returned metrics; `torque_saturated_fraction` logged.

**Comparators (read-only, no re-run):**

| Run | Return | Notes |
|-----|--------|-------|
| `9998217224670341_ml_compare_compare_mpo_23-22-09` | −51.6 | Exp 3 MPO dense — KL→1.5e11 |
| `9998217218692971_ml_mpo_model_size_mpo_s_01-01-46` | −51.6 | Exp 5 mpo_s sparse — KL→0 frozen |

---

## Phase 1 — Built

### 1.1 What was built

| Component | Path |
|-----------|------|
| Entry | `run_mpo_torque.py` |
| Runner | `_torque_runner.py` — production `MPOAgent`, sparse torque |
| dt constants | `_sim_constants_fork.py` — 1.5 s / 1.5 s |
| Mutex | `_run_guard.py` → `pipeline_run_guard` |
| Results | `results/mpo_torque.json`, `results/smoke.json` |

### 1.2 Why

No agent fork — dual fix already in production `MPOConfig` / `controller_agent.py` (`d5af20c`).

### 1.3 How to run

```powershell
conda activate auto-sat
cd backend/scripts/experiments/ml_mpo_decoupled_dual_torque
python run_mpo_torque.py --smoke --allow-cpu
python run_mpo_torque.py --show-progress
```

**Smoke + canonical run (2026-06-30):** `results/mpo_torque.json`; duplicate re-run (`9998217154247371_*`) aborted — use canonical dir only.

---

## Phase 2 — Run

### 2.1 Run scope (What)

| Arm | Agent | Action | Reward | Train | Eval | Seed | dt |
|-----|-------|--------|--------|-------|------|------|-----|
| **torque_sparse** | MPO (fixed dual) | torque | sparse | 50 | 2 | 7 | 1.5 s / 1.5 s |

**Canonical run dir:** `d:\code\sem-proj-asc\backend\autonomous_control\runs\9998217164480175_ml_mpo_decoupled_dual_torque_sparse_16-05-19`

**Results JSON:** `backend/scripts/experiments/ml_mpo_decoupled_dual_torque/results/mpo_torque.json` · wall ~33 min.

| Metric | torque_sparse | Pre-fix comparator (`mpo_s` −51.6) |
|--------|---------------|--------------------------------------|
| `learning_mode` | **true** | false (floor) |
| Eval return mean | **−81.1** | −51.6 |
| Train return best | **+8.7** (ep 28) | −51.6 |
| `kl_mean` (last ep) | **0.021** | →0 frozen / →1e11 |
| `eta_mean` (last ep) | **0.788** | frozen |
| Train `torque_saturated_fraction` | **0.951** | ~0.998 |
| Eval `torque_saturated_fraction` | **0.986** | ~1.0 |
| Eval `shutter_meaningful_fraction` | **0.0** | — |
| Train `shutter_meaningful_fraction` | **0.083** | — |

### 2.2 Run monitoring (Why)

- **Mutex:** cleared after canonical run; duplicate `18-55-51` spawn **KeyboardInterrupt** — ignore for verdict.
- **Operator (Phase 2 review):** dual fix visibly works; returns plateau ~ep 5; safe-mode fires each ep; `pi_loss` plateaus; sparse applied shutters on eval despite latent opportunity peaks.

### 2.3 Run log & artifacts (How)

**Manifest:** `d:\code\sem-proj-asc\backend\autonomous_control\runs\9998217164480175_ml_mpo_decoupled_dual_torque_sparse_16-05-19\artifacts_manifest.json`

**Videos:**

| Clip | Path |
|------|------|
| Eval ep 0 (rank 1) | `d:\code\sem-proj-asc\backend\autonomous_control\runs\9998217164480175_ml_mpo_decoupled_dual_torque_sparse_16-05-19\videos\eval_ep_0_rank1.mp4` |
| Eval ep 1 (rank 2) | `d:\code\sem-proj-asc\backend\autonomous_control\runs\9998217164480175_ml_mpo_decoupled_dual_torque_sparse_16-05-19\videos\eval_ep_1_rank2.mp4` |
| Train best (ep 28, +8.7) | `...\videos\train_ep_28_rank1.mp4` |
| Train ep 11 (rank 2) | `...\videos\train_ep_11_rank2.mp4` |
| Train ep 6 (rank 3) | `...\videos\train_ep_6_rank3.mp4` |

**Plots:** `...\plots\returns_by_episode.png`, `learning_curves.png`, `eval_episode_diagnostics.png`, `train_episode_diagnostics_p01.png` … `p05.png`

**Frame inspect (eval best):** `d:\code\sem-proj-asc\.cursor\video_frame_inspect\data\eval_best_20260630T150214Z\manifest.json` — cyan latent peaks; almost no gold applied-capture dots on eval; train ep 28 shows rare successful captures.

---

## Phase 3 — Evaluation

### 3.1 Claims & success criteria (What)

Restated from Phase 0 — H8a–H8d vs pre-fix −51.6 floor and saturation ~1.0.

### 3.2 Evidence summary (Why)

| Signal | Finding |
|--------|---------|
| **Algorithm** | Dual fix **unblocks learning** — `learning_mode=true`, rising train trajectory, KL ~0.02, η ~0.78 (not frozen / exploded). |
| **Mission** | Eval **−81.1** — worse than pre-fix floor on eval slice; almost **no meaningful eval shutters**; torque still **saturated**. |
| **Safety** | Safe-mode activations ~5–6/ep (telemetry); **no reward penalty** for cuts — motivates [Exp 10](../0-initialized/10-mpo-safe-mode-penalty.md). |
| **Video** | Eval: latent opportunity without applied capture; train ep 28: intermittent good shutters — timing/credit gap, not broken applied-reward kernel. |

**Literature:** [D-022](../../research/DECISIONS.md) — decoupled-KL fix validated; mission outcome partial (branch C: unblock then relapse on eval).

### 3.3 Verdict table (How we decided)

| # | Claim | Criterion | torque_sparse | **Verdict** |
|---|-------|-----------|---------------|-------------|
| H8a | Dual unblocks learning | `learning_mode=true` or eval ≥ −41 | **true**; train best +8.7 | **supported** |
| H8b | KL/η bounded | KL within ~10× target; no η ramp | KL 0.021; η 0.788 | **supported** |
| H8c | Escapes saturation | train sat < 0.9 | **0.951** | **not_supported** |
| H8d | α_μ/α_Σ active | finite, tracking | α_μ ~1e-5, α_σ ~0.28 | **supported** |

**Overall verdict:** **partial** — algorithm fix **supported** (H8a, H8b, H8d); mission / saturation **not** (H8c, eval shutters).

**Follow-up:** [Exp 10](../1-built/10-mpo-safe-mode-penalty.md) safe-mode penalty; [Exp 11 MPO vector](../1-built/11-mpo-decoupled-dual-vector.md) gated on this verdict.

**Promote (Phase 4):** decoupled-KL dual tests only — no new hparams; no production reward changes.

---

## Phase 4 — Documentation

### 4.1 Promotion & integration (What)

| Item | Action |
|------|--------|
| **Already in production** | Decoupled-KL MPO dual (`MPOConfig.decoupled_kl=True`, `target_kl_mu`/`target_kl_sigma`, separate `log_alpha_mu`/`log_alpha_sigma`) — commit `d5af20c` |
| **Promoted at closeout** | **None** — algorithm fix pre-merged; Exp 8 validates behavior |
| **Regression tests** | **Deferred** — add `test_mpo_decoupled_dual_kl_bounded.py` smoke (finite KL over N stores) in follow-up PR |
| **Not promoted** | Reward plane changes; torque saturation mitigations; safe-mode penalty → [Exp 10](../0-initialized/10-mpo-safe-mode-penalty.md) |
| **DECISIONS** | [D-024](../../research/DECISIONS.md) — Exp 8 closeout **partial** |

### 4.2 Closeout rationale (Why)

Exp 8 confirms [D-023](../../research/DECISIONS.md) charter: the decoupled-KL dual is the correct MPO learning lever — `learning_mode=true`, KL ~0.02, η bounded. Mission KPIs remain poor (eval −81, saturation ~0.95, sparse eval shutters). This is **algorithm supported / mission partial** — not a reason to revert the dual fix.

Operator video: eval shows latent capture opportunity without applied gold dots; train ep 28 (+8.7) shows intermittent successful shutters. Safe-mode fires without reward credit — chartered as Exp 10.

**Exp 11 MPO vector** gate cleared: dual fix validated enough to test vector mode (see `11-mpo-decoupled-dual-vector.md`, `blocked_by` cleared).

### 4.3 Knowledge persistence (How)

| Artifact | Path |
|----------|------|
| Pipeline doc (this file) | `docs/experiments/pipeline/4-documentation/08-mpo-decoupled-dual-fix.md` |
| Analysis card | `backend/scripts/experiments/ml_mpo_decoupled_dual_torque/results/mpo_torque_analysis.md` |
| Summary JSON | `backend/scripts/experiments/ml_mpo_decoupled_dual_torque/results/mpo_torque.json` |
| Investigation | [mpo-learning-collapse-investigation.md](../../research/mpo-learning-collapse-investigation.md) § Exp 8 |
| README index | [pipeline/README.md](../README.md) row 8 |

**Report archive:**

- Eval: `...\9998217164480175_ml_mpo_decoupled_dual_torque_sparse_16-05-19\videos\eval_ep_0_rank1.mp4`
- Train peak: `...\videos\train_ep_28_rank1.mp4`
- Returns: `...\plots\returns_by_episode.png`
- Frame manifest: `.cursor/video_frame_inspect/data/eval_best_20260630T150214Z/manifest.json`
