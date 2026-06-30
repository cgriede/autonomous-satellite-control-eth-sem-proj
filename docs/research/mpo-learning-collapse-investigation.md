# MPO learning collapse — symptom vs cause of the "KL explosion"

**Scope:** Deep dive across **all** SAC and MPO runs to date (Exp 1–7 + undocumented probes) to answer one question the operator keeps hitting:

> *"KL explodes on MPO — is that the **symptom** or the **cause** of MPO never learning?"*

**Verdict (high conviction):** The KL/η explosion is a **symptom**. The **cause** is that the MPO policy-improvement (M-step) is effectively an **unconstrained weighted MLE** — the implementation collapses the E-step temperature and the M-step trust-region into a **single `log_eta`** and drives it from the *parametric policy KL* against a mis-scaled target. With no working trust region the Gaussian policy collapses to **saturated max-torque actions inside one episode**; the reported KL is large only because the pre-tanh Gaussian parameters diverge while the squashed action is pinned at the boundary.

**Feeds:** [Exp 08 charter](../experiments/pipeline/0-initialized/08-mpo-decoupled-dual-fix.md) · **Decision:** [D-022](DECISIONS.md)
**Knowledge index:** [PROJECT_KNOWLEDGE.md](PROJECT_KNOWLEDGE.md) · **Related:** [model-size-investigation.md](model-size-investigation.md), [sac-mpo-compare-investigation.md](sac-mpo-compare-investigation.md), [mpo-model-size-investigation.md](mpo-model-size-investigation.md), [shutter-threshold-investigation.md](shutter-threshold-investigation.md)
**Code:** `backend/autonomous_control/controller_agent.py` (`MPOAgent.train`), `controller_actor.py`, `mpo_config.py`

---

## 1. Reasoning chain

1. **Observation across every MPO run** — warmup is healthy (+390 to +530 mean return), then the **first train episode collapses** to a flat penalty floor (−51.6 dense / −101.6 sparse-window / −243.5 0.4 s-dt sparse) and never recovers. `learning_mode=true` reported in some summaries is a **false positive** (flat returns after ep 1).
2. **SAC on the same env learns** (Exp 3 `compare_sac`: `learning_mode=true`, best train +5.33; Exp 4 ref1 train ep 11 +95.8). So the env, reward, warmup, and dt profile are **not** the blocker — the algorithm is.
3. **The "KL exploded" note** appears in Exp 1, 3, 5 and the overnight campaign. To decide symptom-vs-cause we read the **per-episode** `episodes.csv` learning columns (`kl_mu_mean`, `kl_sigma_mean`, `eta_mean`, `q_loss_mean`, `pi_loss_mean`) — not just the summary.
4. **The trajectories discriminate** (Section 3): KL is already ~10⁵ at the **first** train episode while η is still ≈1–4, i.e. **η lags KL by many episodes** → η-largeness cannot be causing the initial KL blow-up. Freezing η does **not** prevent it.
5. **Code reading** (Section 4): a single `log_eta` plays two roles, is updated from the parametric KL, and `target_kl_sigma=1e-4` is ~100× tighter than any working MPO σ-trust-region. There is **no separately-enforced M-step trust region** (`α_μ`, `α_Σ` from the decoupled-KL paper are missing).
6. **Conclusion** — KL/η explosion is the downstream **symptom** of a policy that saturates because the M-step is unconstrained. Highest-conviction fix: implement the **decoupled MPO dual** (Section 6) → tested as **Exp 08**.

---

## 2. Run inventory (what actually exists on disk)

`backend/autonomous_control/runs/` — mapping via `config.json → experiment.experiment_id`. Beyond the documented Exp 1–7, several **undocumented probe sweeps** exist (operator runs faster than the pipeline documents them):

| Run slug cluster | Exp | Agent / reward | Documented? | Relevance here |
|------------------|-----|----------------|-------------|----------------|
| `ml_compare_compare_mpo_23-22-09` | 3 | MPO dense | yes | **Primary KL-explosion trace** (η→1.5e11) |
| `ml_mpo_model_size_mpo_{s,m,l}_*` | 5 | MPO sparse | yes | KL **freeze** at 0 trace; width ruled out |
| `ml_overnight_h1a_mpo_sparse_*` | legacy | MPO sparse 0.4 s | partly | ~968 cmds/ep spam; KL ~10⁵ |
| `ml_overnight_h1b_mpo_stable_eta_*` | legacy | MPO sparse, **η frozen=1.0** | **no** | **Discriminator** — η fixed, KL still 10⁵, **critic diverges** |
| `ml_overnight_h6_mpo_dense_latent_*` | legacy | MPO dense | partly | dense raises floor only (→ D-007) |
| `ml_ls_c1_no_dropout_high_pi_lr_*` | probe | MPO | **no** | early LR/dropout probe (0.4 s dt, 55-D obs) |
| `ml_ls_c2_high_q_lr_tight_kl_*` | probe | MPO | **no** | "tight_kl" label but config still `kl_sigma=1e-4` |
| `ml_ls_b1_lower_threshold_*`, `ml_ls_b2_controller_store_*` | probe | MPO | **no** | shutter/replay probes |
| `ml_sac_hparam_sac_{s,m,l}_{sparse,dense}_*` | **no** | **SAC** width×reward sweep | **no** | SAC capacity/reward sweep — never written up |
| `ml_encoder_r2_sac_a{0,1}_*` | 6 | SAC | **deferred** (D-021) but **ran** | encoder r2 actually executed |
| `ml_compare_compare_sac_*` | 3 | SAC sparse | yes | SAC learns (control) |
| `ml_ref_ref{0,1}_*`, `ml_sac_vector_budget_*` | 4 / 7 | SAC | yes | vector OBC; SAC learns |

> **Documentation gaps flagged for the operator:** the `ml_sac_hparam_*` SAC sweep and `ml_encoder_r2_*` runs have no pipeline doc/verdict; `ml_ls_*` MPO probes are undocumented. None change the Exp 08 conclusion, but they should be closed out or archived so they are not silently re-run.

---

## 3. The discriminating evidence (per-episode trajectories)

Source: `runs/<dir>/episodes.csv`. `kl_mu_mean == kl_sigma_mean` in the summary because the aggregator splits a single `kl` 50/50 — read magnitudes, not the split.

### 3a. `compare_mpo` (Exp 3, **dense**, dt 1.5 s) — η EXPLODES, lagging KL

| train ep | return | q_loss | pi_loss | kl (≈mu=sigma) | **eta** |
|---------:|-------:|-------:|--------:|---------------:|--------:|
| 0 | −100.5 | 53.0 | −0.784 | **5.6e4** | **4.29** |
| 1 | −51.6 | 3.08 | −0.8698 | 8.0e4 | 9.5 |
| 4 | −51.6 | 1.22 | −0.8698 | 1.0e5 | 190 |
| 10 | −51.6 | 0.34 | −0.8698 | 1.3e5 | 2.3e5 |
| 21 | −51.6 | 0.11 | −0.8698 | 1.9e5 | **1.5e11** |

**Read:** KL is already 5.6e4 at ep 0 when **η is only 4.3**. η then ramps ×~3/episode chasing the KL error. **η-largeness is downstream of KL, not its cause.** Critic fits fine (q_loss → 0.1).

### 3b. `mpo_s` (Exp 5, **sparse**, dt 1.5 s) — KL FREEZES at 0

| train ep | return | q_loss | kl | eta |
|---------:|-------:|-------:|----:|----:|
| 0 | −101.3 | 28.7 | 79.3 | 2.95 |
| 1 | −51.6 | 0.90 | **~0** | 2.97 |
| 25 | −51.6 | 0.07 | ~0 | 2.18 |
| 49 | −51.6 | 0.07 | ~0 | 0.030 |

**Read:** opposite endpoint — policy stops moving entirely (KL≈0), η slowly decays. Same −51.6 floor, same frozen `pi_loss=−0.8698`. The policy is **stuck**, not exploring.

### 3c. `h1b_mpo_stable_eta` (legacy sparse, **η frozen = 1.0**) — the discriminator

| train ep | return | **q_loss** | kl |
|---------:|-------:|-----------:|----:|
| 1 | −241 | 54.5 | 2.4e5 |
| 3 | −243.5 | 724.9 | 3.1e5 |
| 5 | −243.5 | **1039** | 3.2e5 |
| 7 | −243.5 | 861.9 | 3.5e5 |

**Read:** with η **held fixed at a sane 1.0**, KL **still explodes** to ~3e5 **and the critic diverges** (q_loss 54 → 1039). This is the decisive result: **the η dual loop is not what blows up the policy** — the M-step is unstable on its own, and the unbounded policy then poisons the critic targets.

### 3d. Shared collapse signature (every MPO run)

| Signal | Value | Source |
|--------|-------|--------|
| `torque_norm_mean` (train) | ~1.00, `torque_saturated_fraction` 0.998–1.000 | summary_metrics action_diagnostics |
| `pi_loss_mean` | bit-identical **−0.8698350627755009** across dense/sparse/frozen-η | episodes.csv |
| `shutter_meaningful_fraction` | 0.0 | action_diagnostics |
| eval `torque_saturated_fraction` | 1.0 (deterministic mean action is fully saturated) | action_diagnostics |

The bit-identical `pi_loss` + 100 % torque saturation says the **policy has collapsed to a degenerate, fully-saturated deterministic action**; the loss is pinned at a constant determined by the tanh-jacobian/log-std clamp, independent of reward.

---

## 4. Mechanism (code-level root cause)

`MPOAgent.train()` (`controller_agent.py`) deviates from canonical MPO (Abdolmaleki et al. 2018, decoupled-KL `1812.02256`):

```text
E-step weights:   weights = softmax(Q / eta)            # eta = exp(log_eta)
M-step loss:      pi_loss = -(weights * log_prob).mean()  # weighted MLE on tanh-squashed samples
"trust region":   eta_loss = eta*(target_kl_mu - kl_mu) + eta*(target_kl_sigma - kl_sigma)
```

Four defects, in order of impact:

1. **One `log_eta` for two jobs.** Canonical MPO has a *separate* E-step temperature η (softmax temperature, solved from a **Q-based dual** with ε_E≈0.1) **and** M-step trust-region multipliers **α_μ, α_Σ** (Lagrangian on the parametric KL). Here a single η is the softmax temperature **and** is updated from the parametric KL. The two objectives fight: when the policy moves a lot, η rises → softmax weights → uniform → E-step gives no advantage preference → M-step maximizes mean log-prob of **all** samples → variance collapses → tanh saturates.
2. **No enforced M-step trust region.** `α_μ`, `α_Σ` are absent. The M-step is an **unconstrained weighted MLE**; nothing stops the pre-tanh Gaussian μ/σ from diverging. This is exactly the `h1b` result (KL explodes even with η frozen).
3. **`target_kl_sigma = 1e-4` is mis-scaled** (~100× tighter than working MPO σ-targets) and is fed into the wrong (η) update, so the σ-constraint is both unenforceable and absurd.
4. **KL measured in pre-tanh space.** `kl_mu/kl_sigma` compare the raw Gaussian before/after one π step. Once tanh saturates, μ can run to ±∞ with no behavioral change, so the **metric** explodes while the **action** is frozen — i.e. the KL number is a *thermometer of saturation*, not a driver.

**Why SAC escapes the same trap:** SAC's max-entropy term explicitly keeps policy entropy up (temperature α tuned to an entropy target), preventing the deterministic-saturation collapse; SAC has no E/M dual to mis-couple. Hence SAC learns where MPO collapses — consistent with [D-017](DECISIONS.md).

---

## 5. What this rules in / out

| Candidate cause | Status | Evidence |
|-----------------|--------|----------|
| Network **capacity** (width) | **ruled out** | Exp 5: 90/140→256/512 identical −51.6 collapse ([D-018](DECISIONS.md)) |
| **Reward sparsity** alone | **ruled out as sole cause** | dense only raises the floor, still collapses ([D-007](DECISIONS.md)); SAC learns on **sparse** |
| **Shutter threshold / window** | **ruled out** | Exp 1 ([D-009](DECISIONS.md), [D-010](DECISIONS.md)) |
| **η dynamics** (the "explosion") | **symptom, not cause** | KL ≈1e5 at ep 0 with η≈4; η frozen still explodes (3c) |
| **M-step unconstrained / dual mis-specified** | **leading cause** | code (Sec 4) + η-frozen critic divergence (3c) + saturation signature (3d) |
| Critic instability | **secondary** | q_loss diverges only once the policy is already unbounded (3c) |

---

## 6. Hypotheses ranked by conviction (→ Exp 08)

| Rank | Hypothesis | Conviction | Test |
|------|------------|-----------|------|
| **1** | **Decoupled MPO dual** (separate E-step η via Q-dual ε_E≈0.1 **+** enforced M-step α_μ/α_Σ trust region, sane ε_μ/ε_Σ) restores learning on **sparse** reward where SAC already learns | **High** | **Exp 08 A1** vs control A0 |
| 2 | E-step temperature fix **only** (proper Q-based η dual, keep scalar trust region) is enough | Medium | Exp 08 optional ablation A2 |
| 3 | Action/observation rescaling or output-saturation guard (e.g. squashed-space KL, log-std init) is the dominant lever | Low–Med | follow-up if A1 bounds KL but returns stay flat |
| 4 | Reward/credit assignment still blocks once KL is bounded | Low | falls out of Exp 08 H8d branch |

**Symptom-vs-cause as a falsifiable test (Exp 08):**
- If the decoupled dual **bounds KL/η AND lifts returns above −51.6** → the dual was **causal**.
- If it **bounds KL but returns stay flat** → KL was a **pure symptom** of a deeper reward/credit problem; reframe toward reward shaping with bounded-KL MPO as the new baseline.

Either outcome resolves the operator's open question with evidence.

---

## 7. Decisions taken

| ID | Status | Decision | Link |
|----|--------|----------|------|
| D-022 | accepted | Charter **Exp 08** (`ml_mpo_decoupled_dual`) — test decoupled-KL MPO dual as the MPO learning lever; KL explosion classified as symptom | [DECISIONS.md](DECISIONS.md) |

---

## 8. Open questions / deferred

- Close out or archive the undocumented `ml_sac_hparam_*` and `ml_encoder_r2_*` runs (Section 2) so they are not re-run.
- Squashed-space (post-tanh) KL vs pre-tanh KL — defer until Exp 08 isolates the dual.
- Critic stabilization (LayerNorm+tanh first layer, ELU per Co-Adaptation 2021 recipe) — defer; only revisit if critic still diverges after the dual fix.

---

## 9. References

### Local (`docs/research/`)
- **`1812.02256v1.pdf`** — Abdolmaleki et al., *Maximum a Posteriori Policy Optimisation* (decoupled-KL / relative-entropy regularized policy iteration). **§ E-step temperature dual + § M-step decoupled trust region (α_μ, α_Σ)** — canonical reference for the Exp 08 fix.
- [model-size-investigation.md](model-size-investigation.md) — Co-Adaptation 2021 recipe (LayerNorm/ELU, critic wider); capacity ruled out.
- [LITERATURE_HIGHLIGHTS.md](LITERATURE_HIGHLIGHTS.md) — MPO section.

### External
- Abdolmaleki et al. 2018, *MPO*, [arXiv:1806.06920](https://arxiv.org/abs/1806.06920).
- Co-adaptation of algorithmic and implementational innovations in inference-based deep RL, NeurIPS 2021.

### Project code & runs
- `backend/autonomous_control/controller_agent.py::MPOAgent.train`, `controller_actor.py`, `mpo_config.py`
- Traces: `runs/9998217224670341_ml_compare_compare_mpo_23-22-09/episodes.csv`, `runs/9998217218692971_ml_mpo_model_size_mpo_s_01-01-46/episodes.csv`, `runs/ml_overnight_h1b_mpo_stable_eta_23-42-59/episodes.csv`
