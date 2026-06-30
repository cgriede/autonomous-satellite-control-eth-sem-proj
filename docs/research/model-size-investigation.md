# Model size investigation — RL policy / value networks

Research note for MPO sizing, input-dimension effects, and how to read train/eval metrics when judging capacity. Written for sem-proj-asc experiment design (`ml_modular_encoder`, SAC vs MPO compare, width ablations).

**Knowledge index:** [PROJECT_KNOWLEDGE.md](PROJECT_KNOWLEDGE.md) · **Decision IDs:** [D-005](DECISIONS.md), [D-006](DECISIONS.md)

**Related code:** `backend/autonomous_control/mpo_config.py`, `controller_encoder.py`, `controller_actor.py`, `controller_critic.py`  
**Related presentation record:** `docs/presentation/machine-learning.md` (networks & vision encoder slide)

---

## 1. What the MPO paper states (Abdolmaleki et al., ICLR 2018)

**Not in local PDF library** — cite from [arXiv:1806.06920](https://arxiv.org/abs/1806.06920). Extended KL decoupling: [arXiv:1812.02256](https://arxiv.org/abs/1812.02256).

The original paper does **not** give a formula for network width from observation dimension. It fixes **task-family architectures** and reuses them across all DeepMind Control Suite tasks (observation size varies by task; architecture does not).

| Component | DeepMind Control Suite | Humanoid |
|-----------|------------------------|----------|
| Policy MLP | **100–100** (2 layers) | **200–200** |
| Q-network MLP | **200–200** | **300–300** |

Other appendix points:

- Feed-forward MLPs everywhere except Parkour-2d (architecture from Heess et al. 2017).
- **Same hyperparameters** for all Control Suite experiments — robustness to hyperparameter choice is a main claim.
- Gaussian policy; critic trained with bootstrapped Q targets (same family as SAC/TD3).
- M-step is supervised MAP on reweighted samples — any policy parameterization works; paper uses MLPs.

Implementation details emphasized in later DeepMind work (MO-MPO supplementary material, building on the 2018 stack):

- **LayerNorm on the first hidden layer + tanh** on that layer output — reported as important for stability.
- **ELU** activations on subsequent hidden layers.
- Critic typically **wider and/or deeper** than policy.

### Follow-up: MPO is network-size-sensitive (external)

**Co-Adaptation of Algorithmic and Implementational Innovations in Inference-based Deep RL** (NeurIPS 2021) — not on disk; referenced from the MPO implementation lineage.

| Label | Policy hidden layers | Critic hidden layers |
|-------|----------------------|----------------------|
| Large (typical open-source MPO) | (256, 256, 256) | (512, 512, 256) |
| Medium (typical SAC) | (256, 256) | (256, 256) |
| Small (typical AWR) | (128, 64) | (128, 64) |

Key finding: **MPO performance depends strongly on the large network**; SAC is more robust across sizes. Swapping sizes across algorithms hurts MPO most. Normalization/activation choices (ELU, LayerNorm) are part of the “implementation recipe,” not optional decoration.

---

## 2. How input dimension influences sizing

The 2018 MPO paper treats input size implicitly: same 100–100 policy on tasks with ~20–60 dimensional proprioceptive states. **No explicit scaling rule** with state dimension.

For **this project** (105 scalar features + 2 vision observation lines), local research papers are more relevant than the MPO appendix alone.

### Local library — representation before width

| Local PDF | Citation | Relevance to input size |
|-----------|----------|-------------------------|
| [2206.02855_efficient_entity_based_rl.pdf](2206.02855_efficient_entity_based_rl.pdf) | Jankovics et al., 2022 | Observations as **entity sets**; flattening padded features hurts sample efficiency as entity count grows — analog: 50 targets × 2 features (bearing + imaged mask). |
| [gorishniy2022_numerical_feature_embeddings.pdf](gorishniy2022_numerical_feature_embeddings.pdf) | Gorishniy et al., NeurIPS 2022 | Raw `Linear(N→k)` on many scalars underperforms; **embed/compress groups** before mixing. Supports `Linear(50→k)` bottlenecks vs one `Linear(105→90)`. |
| [bruin2018_integrating_srl_into_rl.pdf](bruin2018_integrating_srl_into_rl.pdf) | Bruin et al., IEEE RA-L 2018 | Shared multimodal embedding before actor/critic; reward alone may not learn a good trunk — **encoder design before hyperparameter tuning**. |
| [2506.17518_srl_survey_drl.pdf](2506.17518_srl_survey_drl.pdf) | SRL survey, 2025 | Multimodal SRL taxonomy; evaluation via sample efficiency and generalization — aligns with `learning_mode` KPIs. |
| [2410.17551_multimodal_information_bottleneck_rl.pdf](2410.17551_multimodal_information_bottleneck_rl.pdf) | Multimodal IB for DRL, 2024 | Bottleneck fusion — avoid forcing all modalities through one undifferentiated vector. |

### Practical synthesis

```
capacity_needed ≈ f(task_complexity, input_structure)
                ≠ f(raw_scalar_count) alone
```

When scalar input grows (e.g. `scalar_dim: 105` = 5 globals + 50 imaged masks + 50 bearing errors):

1. **First-layer fan-in grows linearly** — `Linear(105, 90)` has ~3× the first-layer weights of a ~30-D DMC state with width 100.
2. A fixed hidden width is a **tighter bottleneck** unless structured encoding reduces effective input dimension first.
3. Literature favors **compress structured groups → fuse → policy head**, not proportional widening of one flat MLP.

### Current sem-proj-asc stack (baseline)

From `MPOConfig` defaults:

| Block | Shape (conceptual) |
|-------|-------------------|
| Scalar encoder | `105 → 90` (1 hidden layer) |
| Vision | 2× 1D-CNN → 32-D each → fusion MLP → **90-D** |
| Actor trunk | **180-D** concat → **90-D** → action (μ, log σ) |
| Critic trunk | **180-D** + action → **140–140** → Q |

Compared to MPO literature:

- **Smaller** than Control Suite reference (100–100 policy, 200–200 critic on ~30-D proprio).
- **Much smaller** than open-source “Large MPO” (256³ policy, 512–512–256 critic).
- **Structured encoder** (dual-path) is aligned with Bruin / SRL survey / multimodal IB — but width ablation is still untested on this codebase.

Encoder experiment fork: `backend/scripts/experiments/ml_modular_encoder/` (A0 flat vs A1 vector-compress).

---

## 3. Diagnosing “too small” vs “too large” from train / test results

RL capacity diagnosis **differs from supervised learning**. A bad train return with an equally bad eval return is usually **not** classical overfitting.

### Signs the model is **too small / under-expressive**

| Signal | Interpretation |
|--------|----------------|
| **Width ablation helps monotonically** (e.g. 90 → 140 → 256) | Classic under-capacity |
| Return **plateaus well below warmup or baseline** despite a usable reward signal | Policy/value cannot represent useful mapping |
| **Q-loss / TD error stay high** with no downward trend | Critic cannot fit bootstrapped targets |
| **Feature rank collapse** in critic penultimate layer | “Implicit under-parameterization” (Kumar et al., ICLR 2021 — external) — network behaves like a smaller net despite parameter count |
| Slow improvement only (no collapse) | Often representation or capacity, not algorithm blow-up |

**Fu et al. 2019** (*Diagnosing Bottlenecks in Deep Q-learning*, ICML): larger networks often **improve stability** in RL and can compensate for overfitting-like effects — opposite to typical supervised intuition.

### Signs the model is **too large / unstable (RL sense)**

| Signal | Interpretation |
|--------|----------------|
| Learning curves **oscillate or diverge** when width/depth increases | Instability at high update-to-data (UTD) ratio |
| Performance **degrades with more gradient steps per env step** | Primacy bias / plasticity loss (Nikishin et al. 2022; plasticity survey 2024 — external) |
| **Early good performance, then collapse** after many updates | Often plasticity or early-sample memorization, not train/eval generalization gap |
| **MPO-specific:** small net underperforms; very large net without LayerNorm/ELU recipe fails differently | Co-Adaptation 2021 network-size swap experiments |

### Signals that usually indicate **something other than capacity**

| Signal | More likely cause |
|--------|-------------------|
| Train ≈ eval, both poor | Reward sparsity, credit assignment, exploration, algorithm instability |
| Warmup good, first train episodes collapse | Policy destabilization, KL/η blow-up, passive optimum — not width alone |
| Flat return at a **penalty floor** (e.g. −243.5) | Dense penalty regime, not a capacity ceiling |
| Huge KL / η (e.g. 10⁵–10⁶ in overnight MPO logs) | MPO dual variables / reward scale — tune before width sweep |

### External references for RL-specific capacity pathology

| Paper | arXiv | Claim |
|-------|-------|-------|
| Implicit under-parameterization | [2010.14498](https://arxiv.org/abs/2010.14498) | Bootstrapping + gradient descent → rank collapse → TD error rise → plateau |
| Regulating overfitting in sample-efficient RL | [2304.10466](https://arxiv.org/abs/2304.10466) | Many gradient steps per transition cause overfitting-like failure; track train vs validation TD error |
| Plasticity loss survey | [2411.04832](https://arxiv.org/abs/2411.04832) | UTD ratio, resets, rank/norm diagnostics |

---

## 4. Reading sem-proj-asc overnight runs (Jun 2026)

Illustrative artifacts: `ml_overnight_h1a_mpo_sparse_*`, `ml_overnight_h4_sac_*` (`summary_metrics.json`).

| Phase | MPO sparse (H1a) | SAC sparse (H4) |
|-------|------------------|-----------------|
| Warmup return mean | **+459** | **+459** |
| Train return mean | −243 (flat after ep 0) | −141 |
| Eval return mean | −243 | −168 |
| Torque saturated fraction (train) | ~100% | ~24% |
| Meaningful shutter fraction | 0% | ~0.04% |
| KL / η (MPO) | ~10⁵ / ~10⁶ | N/A |

**Interpretation for capacity:**

- Warmup proves the pipeline can produce good behavior — not an irreducible env bug.
- Train and eval fail **equally** — not a generalization-gap story.
- Post-train **policy collapse** (saturation, zero meaningful captures) with exploding MPO KL — **algorithm + reward / credit assignment first**, not “add hidden units” as the first lever.
- SAC also fails but less catastrophically → compare algorithms before attributing to model size alone.

Aligns with project doc guidance: check passive-policy / reward shaping before MPO hyperparameter tuning (`docs/presentation/machine-learning.md`).

Model size becomes the leading hypothesis only if:

- A **width sweep** improves returns **without** KL explosion, or
- Q-loss remains high while action diagnostics (torque distribution, shutter quality) look reasonable.

---

## 5. Decision flow (experiment planning)

```text
Returns flat / bad
  └─ Warmup or baseline OK?
       No  → env / reward / obs bug
       Yes → Train vs eval gap large?
              Yes → eval mismatch / generalization
              No  → KL / η / Q-loss stable?
                     No  → algorithm + reward scale first
                     Yes → Width ablation monotonic improvement?
                            Yes → under-capacity (widen critic first for MPO)
                            No  → representation (encoder compress before wider MLP)
```

### Recommended experiment order (this repo)

1. **Representation** — `ml_modular_encoder` A0 vs A1 (local papers §2 above).
2. **MPO reference scale** — critic toward (256, 256) or (512, 512, 256); policy trunk ≥ (256, 256) per Co-Adaptation / open-source MPO.
3. **Width ablation** — 2–3 points on `num_units_actor` / `num_units_critic` with fixed encoder; KPI: `learning_mode`, eval return, `action_diagnostics`.
4. **Diagnostics** — Q-loss trend, KL/η, optional critic feature rank (Kumar-style).

Example ablation matrix (hypothesis doc only — not yet run):

| Arm | `num_units_actor` | `num_units_critic` | `num_layers_actor` | Notes |
|-----|-------------------|--------------------|--------------------|-------|
| S (current) | 90 | 140 | 1 | Production default |
| M | 140 | 256 | 2 | Between current and MPO 2018 humanoid |
| L | 256 | 512 | 2–3 | Open-source “Large MPO” scale |

Hold encoder architecture fixed within each phase so representation and width effects are separable.

Hold encoder architecture fixed within each phase so representation and width effects are separable.

---

## 6. Decisions taken

| ID | Status | Decision |
|----|--------|----------|
| [D-005](DECISIONS.md) | deferred | MPO width ablation not first — reward/credit assignment and KL stability first |
| [D-006](DECISIONS.md) | accepted | Modular encoder (A0 vs A1) before raw width tuning |

Full log: [DECISIONS.md](DECISIONS.md).

---

## 7. Rejected or deferred

| Path | Status | Why |
|------|--------|-----|
| Lead with `num_units_actor/critic` sweep | deferred | Overnight collapse + KL blow-up; see §4 |
| Single `Linear(105→90)` without structure | rejected (design) | Entity-based + Gorishniy literature; use encoder compress |

---

## 8. Experiments already conducted

| Slug | Arm | Verdict | Artifacts |
|------|-----|---------|-----------|
| `ml_algo_overnight` | H1a mpo_sparse | inconclusive | `backend/scripts/experiments/ml_algo_overnight/results/h1a_mpo_sparse.json` |
| `ml_algo_overnight` | H1b mpo_stable_eta | inconclusive | `results/h1b_mpo_stable_eta.json` |
| `ml_algo_overnight` | H6 mpo_dense_latent | inconclusive | `results/h6_mpo_dense_latent.json` |
| `ml_algo_overnight` | H4 sac sparse | inconclusive | `results/h4_sac.json` |

Do not re-run identical frozen inputs expecting width ablation answers — width ablation matrix in §5 not yet executed.

---

## 9. Gaps in local library

| Topic | Status | Action |
|-------|--------|--------|
| MPO 2018 / 1812.02256 PDFs | Missing | Add to `docs/research/` if repeated citation needed |
| Co-Adaptation NeurIPS 2021 | Missing | Network-size swap evidence for MPO |
| Kumar 2021 rank collapse | Missing | Diagnostic methodology for critic capacity |
| This note | **Present** | `model-size-investigation.md` |

---

## 10. Cross-paper cheat sheet (sem-proj-asc)

| Experiment / question | Primary citations | One-line justification |
|-----------------------|-------------------|------------------------|
| Modular encoder before width tuning | Gorishniy 2022; 2206.02855; Bruin 2018; SRL survey 2025 | High-D structured inputs need compression, not only wider MLP |
| SAC vs MPO compare | MPO 2018; Co-Adaptation 2021 | MPO needs larger nets; different stability profile |
| Width ablation on MPO | MPO 2018 appendix; Co-Adaptation §5.4 | Empirical test of under-capacity vs current 90/140 defaults |
| Reading flat −243 returns | Project reward docs; §4 above | Penalty floor + collapse ≠ capacity ceiling without ablation |

---

## References

### Local (`docs/research/`)

- Jankovics et al., 2022 — [2206.02855_efficient_entity_based_rl.pdf](2206.02855_efficient_entity_based_rl.pdf)
- Gorishniy et al., NeurIPS 2022 — [gorishniy2022_numerical_feature_embeddings.pdf](gorishniy2022_numerical_feature_embeddings.pdf)
- Bruin et al., IEEE RA-L 2018 — [bruin2018_integrating_srl_into_rl.pdf](bruin2018_integrating_srl_into_rl.pdf)
- SRL survey, 2025 — [2506.17518_srl_survey_drl.pdf](2506.17518_srl_survey_drl.pdf)
- Multimodal IB for DRL, 2024 — [2410.17551_multimodal_information_bottleneck_rl.pdf](2410.17551_multimodal_information_bottleneck_rl.pdf)
- Section highlights — [LITERATURE_HIGHLIGHTS.md](LITERATURE_HIGHLIGHTS.md)

### External (algorithm / capacity pathology)

- Abdolmaleki, A. et al. Maximum a posteriori policy optimisation. ICLR 2018. [arXiv:1806.06920](https://arxiv.org/abs/1806.06920)
- Abdolmaleki, A. et al. Maximum a posteriori policy optimisation with trust-region. 2018. [arXiv:1812.02256](https://arxiv.org/abs/1812.02256)
- Co-adaptation of algorithmic and implementational innovations in inference-based deep RL. NeurIPS 2021.
- Kumar, A. et al. Implicit under-parameterization inhibits data-efficient deep RL. ICLR 2021. [arXiv:2010.14498](https://arxiv.org/abs/2010.14498)
- Fu, J. et al. Diagnosing bottlenecks in deep Q-learning algorithms. ICML 2019.
- Nikishin, E. et al. The primacy bias in deep RL. ICML 2022.
- Nauman et al. Efficient deep RL requires regulating overfitting. 2023. [arXiv:2304.10466](https://arxiv.org/abs/2304.10466)

### Project code & runs

- `backend/autonomous_control/mpo_config.py` — `num_units_actor`, `num_units_critic`, encoder layer counts
- `backend/autonomous_control/controller_encoder.py` — dual-path scalar + vision fusion
- `backend/autonomous_control/runs/ml_overnight_h1a_mpo_sparse_23-20-15/summary_metrics.json`
- `backend/autonomous_control/runs/ml_overnight_h4_sac_00-28-52/summary_metrics.json`
