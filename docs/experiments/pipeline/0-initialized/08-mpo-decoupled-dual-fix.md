---
experiment_id: 8
slug: ml_mpo_decoupled_dual
title: "Exp 8 — MPO decoupled-KL dual (learn or bust)"
current_phase: 0
overall_verdict: pending
blocked_by: null
code_path: backend/scripts/experiments/ml_mpo_decoupled_dual/
plan_ref: ".cursor/plans/sac_vs_mpo_compare_821ab4d5.plan.md — MPO debug track"
phases:
  "0": { status: in_progress, documented_utc: "2026-06-30T15:10:00Z", completed_utc: null }
  "1": { status: pending, documented_utc: null, completed_utc: null }
  "2": { status: pending, documented_utc: null, completed_utc: null }
  "3": { status: pending, documented_utc: null, completed_utc: null }
  "4": { status: pending, documented_utc: null, completed_utc: null }
run_lock_holder: null
decision_ids: [D-022]
predecessor: ml_sac_mpo_compare
investigation: docs/research/mpo-learning-collapse-investigation.md
---

# Exp 8 — MPO decoupled-KL dual (`ml_mpo_decoupled_dual`)

**Agent:** MPO only · **Action:** torque (production default) · **Reward:** sparse · **dt:** 1.5 s / 1.5 s
**Predecessor:** [Exp 3](../4-documentation/03-sac-mpo-compare.md) (SAC learns, MPO does not) · [Exp 5](../4-documentation/05-mpo-model-size.md) (width ruled out)
**Investigation:** [mpo-learning-collapse-investigation.md](../../research/mpo-learning-collapse-investigation.md) · [D-022](../../research/DECISIONS.md)

---

## Phase 0 — Initialized

### 0.1 Experiment scope (What)

**Core question:** MPO has **never learned** on this task (flat penalty floor since Exp 1), while SAC learns on the **same sparse reward**. The deep dive ([investigation](../../research/mpo-learning-collapse-investigation.md)) classified the "KL explosion" as a **symptom** of an **unconstrained M-step**: the implementation uses a **single `log_eta`** as both the E-step softmax temperature and the M-step trust-region multiplier, updated from the parametric policy KL against a mis-scaled `target_kl_sigma=1e-4`. The policy collapses to **saturated max-torque** actions within one episode.

Does implementing the **correct decoupled-KL MPO dual** unblock MPO learning?

**Hypothesis (H8):**

> An MPO agent with a **decoupled dual** — E-step temperature η solved from the **Q-based dual** (ε_E ≈ 0.1) **and separate, enforced** M-step trust-region multipliers **α_μ, α_Σ** (decoupled KL, sane targets ε_μ ≈ 1e-2, ε_Σ ≈ 1e-4) — achieves `learning_mode=true` (returns rise above the −51.6 floor) with **bounded** KL/η, on the same sparse reward and frozen protocol where the current MPO collapses.

| ID | Claim | Success criterion | Falsified if |
|----|-------|-------------------|--------------|
| **H8a** | Decoupled dual unblocks learning | A1 `learning_mode=true` **or** eval return ≥ **20%** above A0 floor (−51.6 → ≥ −41) with rising best-train | A1 also pins at the −51.6 floor |
| **H8b** | KL/η stay bounded | A1 `kl_mean` stays within ~10× target through training; **no** monotonic η→1e11 ramp (cf. A0 η→1.5e11) | KL/η still explode like A0 |
| **H8c** | Policy escapes saturation | A1 train `torque_saturated_fraction` < **0.9** (A0 ≈ 0.998) | Still ≈ 1.0 (degenerate saturated action) |
| **H8d** | Symptom-vs-cause resolved | KL bounded **and** returns rise ⇒ dual was **causal**; KL bounded **but** returns flat ⇒ KL was a **pure symptom** (reframe to reward/credit) | — (diagnostic, always informative) |

**Overall:** **supported** if H8a **and** H8b; **not_supported** if A1 collapses like A0 (then H8d still yields the cause verdict).

**Arms:**

| Arm | Dual | Runs? | Purpose |
|-----|------|-------|---------|
| **A0** `dual_baseline` | current single-`log_eta` (production) | **Yes** (control re-run, sparse, 50 ep) | Reproduce −51.6 + η→1e11 under frozen protocol; parity anchor |
| **A1** `decoupled_dual` | E-step Q-dual η (ε_E=0.1) + enforced α_μ/α_Σ (ε_μ=1e-2, ε_Σ=1e-4) | **Yes** (treatment) | Test H8 |
| A2 `temp_only` | E-step Q-dual η only; keep scalar trust region | **Optional** ablation | Isolate E-step coupling if A1 ambiguous (ponytail — defer unless needed) |

**Frozen protocol** (match Exp 5 / Exp 3 MPO so A0 is comparable):

| Knob | Value |
|------|-------|
| dt | 1.5 s / 1.5 s ([D-002](../../research/DECISIONS.md)) |
| seed | 7 |
| warmup | 5 (rebuild per arm) |
| train | 50 |
| eval | 2 |
| reward | **sparse** (SAC-learnable regime; dense ruled out [D-007](../../research/DECISIONS.md)) |
| heads | S = 90/140 (production default; width ruled out [D-018](../../research/DECISIONS.md)) |
| videos | 3 train + 2 eval (default workflow) |

**Out of scope:** width sweep (Exp 5 closed), dense reward (Exp 3 closed), encoder A0/A1 (Exp 2/6), vector OBC (Exp 4/7), critic-recipe changes (LayerNorm/ELU — deferred follow-up), **any production `controller_agent.py` edit** until Phase 4 promote ([D-003](../../research/DECISIONS.md)).

**Gate:** Phase 2 requires `pipeline_run_guard.check_pipeline_run_clear(slug="ml_mpo_decoupled_dual")` ([D-012](../../research/DECISIONS.md)).

### 0.2 Thought process (Why)

| Prior fact | Implication |
|------------|-------------|
| KL ≈1e5 at **first** train ep while η≈4 ([investigation §3a](../../research/mpo-learning-collapse-investigation.md)) | η-largeness is downstream → fix the **dual**, not η scale |
| η frozen=1.0 still explodes KL + diverges critic (§3c) | M-step is unconstrained → must enforce α_μ/α_Σ trust region |
| Width identical collapse (Exp 5, [D-018](../../research/DECISIONS.md)) | Not capacity — algorithm/dual lever |
| Dense only raises floor (Exp 3, [D-007](../../research/DECISIONS.md)) | Stay sparse (SAC-learnable) |
| SAC learns sparse (Exp 3, [D-017](../../research/DECISIONS.md)) | Target regime is reachable; MPO dual is the gap |

**Reject / defer:**

| Path | Why |
|------|-----|
| Tune η LR / `target_kl_sigma` numbers only | Prior `ml_ls_*` probes already nudged LR/KL with no effect; the **structure** (single η, no α) is the defect |
| Dense reward to "help" MPO | [D-007](../../research/DECISIONS.md) — raises floor only |
| Width / encoder changes | Exp 5 / Exp 2 closed |
| Edit production agent now | [D-003](../../research/DECISIONS.md) — fork only until Phase 4 |

#### 0.2.1 Shoulders of giants

- **Abdolmaleki et al. 2018 — decoupled-KL MPO** (`docs/research/1812.02256v1.pdf`): E-step temperature η from the Q-based dual; **separate** parametric M-step KL constraints on mean and covariance with Lagrange multipliers **α_μ, α_Σ** (ε_μ, ε_Σ). **Maps to** A1 — the exact mechanism missing from `controller_agent.py`.
- **Abdolmaleki et al. 2018 — MPO** ([arXiv:1806.06920](https://arxiv.org/abs/1806.06920)): E-step/M-step structure; robustness claim across tasks with **same** hyperparameters when the dual is correct.
- **Co-Adaptation NeurIPS 2021** (via [model-size-investigation.md](../../research/model-size-investigation.md)): MPO is recipe-sensitive (LayerNorm/ELU, critic wider). Noted as **deferred** critic-side follow-up, not in A1 scope.
- **Internal:** [mpo-learning-collapse-investigation.md](../../research/mpo-learning-collapse-investigation.md) symptom-vs-cause verdict; Exp 3/5 traces.

### 0.3 Preliminary implementation remarks (How)

**Scaffold:** copy `backend/scripts/experiments/ml_mpo_model_size/` (closest MPO fork): `_run_guard.py` (→ `pipeline_run_guard`), `_sim_constants_fork.py` (1.5/1.5), `_warmup_fingerprint_patch.py`, runner pattern → new slug `ml_mpo_decoupled_dual/`.

| Component | Planned path |
|-----------|--------------|
| Entry | `run_mpo_decoupled_dual.py` (`--arm {dual_baseline,decoupled_dual}`, `--smoke`, `--show-progress`) |
| Runner | `_dual_runner.py` |
| **Dual fork** | `_mpo_dual_fork.py` — subclass/patch `MPOAgent.train` with E-step Q-dual η + α_μ/α_Σ M-step constraints; **no production edit** |
| Mutex | `_run_guard.py` → `pipeline_run_guard` |
| Results | `results/mpo_decoupled_dual.json`, `mpo_decoupled_dual_analysis.md` |

**Dual math (A1, from `1812.02256` §E/M-step):**
- E-step temperature: η minimizes `g(η) = η·ε_E + η·mean_s log mean_a exp(Q(s,a)/η)`; weights `= softmax(Q/η)` (η from Q-dual, **not** policy KL).
- M-step: maximize `Σ q(a|s) log π_θ(a|s)` s.t. `KL_μ < ε_μ`, `KL_Σ < ε_Σ`; Lagrangian with **separate** `α_μ, α_Σ` updated by `α ← α + lr·(ε − KL)` (projected ≥0).

**Smoke:** both arms run ≥1 train step; assert η, α_μ, α_Σ finite and updating; A0 reproduces the single-`log_eta` behavior.

**Risks / open questions:**
- Numerical stability of the E-step η dual (clip η ∈ [1e-3, 1e3]; log-space).
- KL is currently pre-tanh — keep pre-tanh for A1 parity, flag squashed-space KL as a follow-up only if A1 bounds KL but returns stay flat (H8d branch).
- Wall time: 2 arms × ~33 min ≈ 70 min (Exp 5 reference).

**Follow-up (if inconclusive):** H8d "KL bounded but flat" ⇒ open a reward/credit experiment with bounded-KL MPO as the new baseline; "still explodes" ⇒ A2 temp-only ablation + critic recipe (Co-Adaptation).

*(Phases 1–4 appended by `/document-experiment-step`.)*
