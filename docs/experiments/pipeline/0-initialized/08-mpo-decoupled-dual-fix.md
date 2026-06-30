---
experiment_id: 8
slug: ml_mpo_decoupled_dual_torque
title: "Exp 8 — MPO fixed dual, sparse, torque mode"
current_phase: 0
overall_verdict: pending
blocked_by: null
code_path: backend/scripts/experiments/ml_mpo_decoupled_dual_torque/
plan_ref: ".cursor/plans/sac_vs_mpo_compare_821ab4d5.plan.md — MPO debug track"
phases:
  "0": { status: in_progress, documented_utc: "2026-06-30T15:10:00Z", completed_utc: null }
  "1": { status: pending, documented_utc: null, completed_utc: null }
  "2": { status: pending, documented_utc: null, completed_utc: null }
  "3": { status: pending, documented_utc: null, completed_utc: null }
  "4": { status: pending, documented_utc: null, completed_utc: null }
run_lock_holder: null
decision_ids: [D-022]
predecessor: ml_mpo_model_size
investigation: docs/research/mpo-learning-collapse-investigation.md
---

# Exp 8 — MPO fixed dual, sparse, torque mode (`ml_mpo_decoupled_dual_torque`)

**Agent:** MPO (fixed decoupled-KL dual) · **Action:** torque (production default) · **Reward:** sparse · **dt:** 1.5 s / 1.5 s
**Fix commit:** `d5af20c` — `fix(mpo): implement decoupled-KL dual`
**Predecessor:** [Exp 5](../4-documentation/05-mpo-model-size.md) (torque mode, identical collapse across widths — pre-fix)
**Investigation:** [mpo-learning-collapse-investigation.md](../../research/mpo-learning-collapse-investigation.md) · [D-022](../../research/DECISIONS.md)
**Pair:** [Exp 9](09-mpo-decoupled-dual-vector.md) (same fixed agent, vector mode)

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

**Overall:** **supported** if H8a **and** H8b; **not_supported** otherwise (then H8d still resolves symptom-vs-cause for Exp 9 design).

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

**Out of scope:** dense reward (Exp 3), width sweep (Exp 5), vector mode (→ Exp 9), encoder changes.

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

*(Phases 1–4 appended by `/document-experiment-step`.)*
