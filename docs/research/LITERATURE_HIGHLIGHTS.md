# Literature highlights — observation encoding & RL learnability

Section pointers for quick review. Full PDFs live in this folder (see [README.md](README.md)).

---

## 1. SRL survey for deep RL (2025)

**File:** `2506.17518_srl_survey_drl.pdf`  
**Cite:** *A Survey of State Representation Learning for Deep Reinforcement Learning* (arXiv:2506.17518)

### Read first

| Section / theme | Why for this project |
|---------------|----------------------|
| **Definition of SRL** | Observation → low-D state that preserves task-relevant information; motivates encoder forks vs raw flatten |
| **Taxonomy (Sec. 3)** | Six classes: reconstruction, contrastive, metric-based, **auxiliary tasks**, model-based, multimodal — pick vocabulary for report |
| **Multimodal SRL** | Separate encoders per sensor → fusion; matches vision CNN + scalar/vector streams |
| **Metric / auxiliary tasks** | Shaping embeddings without changing reward — relevant if we add SRL losses later |
| **Evaluation metrics (Sec. 4)** | Sample efficiency, generalization, robustness — align with `learning_mode` + eval return KPIs |
| **Table 1 (overview)** | Quick map of methods → use in Related Work table |

### Terminology to reuse

- **State representation learning (SRL)** — umbrella term for encoder design experiments (`ml_modular_encoder`)
- **Heterogeneous / multimodal observations** — vision lines + proprio + per-target vectors

---

## 2. Bruin et al. 2018 — Integrating SRL into RL

**File:** `bruin2018_integrating_srl_into_rl.pdf`  
**Cite:** *Integrating State Representation Learning into Deep Reinforcement Learning for Mobile Robot Control* (IEEE RA-L)

### Read first

| Section / figure | Why for this project |
|------------------|----------------------|
| **Abstract + Fig. 1** | Shared embedding `s̄(o)` from all modalities; **RL loss + SRL losses** jointly shape the trunk |
| **§II Problem** | Reward alone may not teach a good representation — justifies structured encoders before hyperparameter tuning |
| **§III Methods — integrated training** | Actor/critic share encoder; SRL terms regularize during RL — template if we add auxiliary losses |
| **Forward / inverse dynamics losses** | Predict next state or action from embedding — optional follow-up on bearing-error predictability |
| **§IV Torcs experiments** | Generalization to new tracks when SRL integrated — analog: new target layouts / cloud seeds |
| **Takeaway** | **Fusion trunk + multiple loss signals** is established; our A1 fork is the minimal structural step without extra losses |

---

## 3. Gorishniy et al. 2022 — Numerical feature embeddings

**File:** `gorishniy2022_numerical_feature_embeddings.pdf`  
**Cite:** *On Embeddings for Numerical Features in Tabular Deep Learning* (NeurIPS 2022)

### Read first

| Section | Why for this project |
|---------|----------------------|
| **Abstract + §1** | Scalars fed through linear+ReLU underperform; **embedding each numeric feature** before mixing helps MLPs |
| **§3 Piecewise linear encoding (PLR)** | Binning-style embed — alternative to `Linear(50→k)` for bearing vectors |
| **§3 Periodic / sinusoidal embed** | Strong on some benchmarks — probably overkill for v1 |
| **§4 Results** | Embeddings help **MLP backbones**, not only Transformers — supports small fusion MLP after compress |
| **§5.3 “MLP also benefits”** | Direct support for **passthrough vs embed ablation** on the ~5 global scalars |

### Mapping to our design

| Our choice | Paper language |
|------------|----------------|
| `Linear(50→embed_dim)` on bearing/mask vectors | Group-wise bottleneck (coarser than per-scalar PLR) |
| Passthrough globals | Paper would suggest optional per-scalar embed — document as ablation, not required v1 |

---

## 4. Entity-based RL (2022) — already on disk

**File:** `2206.02855_efficient_entity_based_rl.pdf`  
**Cite:** Jankovics, Ortíz, Alonso — *Efficient entity-based reinforcement learning* (arXiv:2206.02855)

### Read first

| Section | Why for this project |
|---------|----------------------|
| **Abstract** | Observations as **sets of entities**; flattening hurts sample efficiency |
| **§1 Introduction** | MLP on padded concatenated features vs **entity embeddings + slot attention / GNN** |
| **Method — entity encoder** | Per-entity features → shared φ → aggregate; compare to our ordered `Linear(50→k)` (we keep slot index) |
| **Experiments (Atari / Playgrounds)** | Structured encoders train faster when entity count grows — analog: **50 targets × 2 features** |
| **Takeaway** | Justifies **not** feeding 105 scalars into one `Linear(105,90)`; full Deep Sets is v2 if A1 wins |

---

## 5. Cross-paper cheat sheet (sem-proj-asc experiments)

| Experiment | Primary citations | One-line justification |
|------------|-------------------|------------------------|
| `ml_modular_encoder` (vector compress) | §3–4 Gorishniy; §4 2206.02855; SRL survey multimodal | Flattening 50+50 target features dilutes structure; compress groups before fusion |
| `ml_shutter_threshold` | Action gating less covered — use bug-hunt internal baseline | Threshold as exploration gating; cite adapter semantics in code |
| `mpc_pointing` | Recitation 08 (mpc_lecture); Jonschkowski SRL (optional) | Hierarchical: reference policy + constrained low-level MPC |
| SAC vs MPO compare | Algorithm literature external to this folder | Credit assignment / off-policy stability |
| Model width / capacity ablation | [model-size-investigation.md](model-size-investigation.md); MPO 2018 appendix; Co-Adaptation 2021 (external) | MPO needs larger nets than current 90/140 defaults; test width after encoder |
| Shutter threshold H1 (Exp 1) | [01-shutter-threshold.md](../experiments/pipeline/4-documentation/01-shutter-threshold.md); [investigation](shutter-threshold-investigation.md) | Threshold 0.9 does not cut spam when policy saturates shutter dim |

---

## 5b. Abdolmaleki et al. 2018 — decoupled-KL MPO (algorithm)

**File:** `1812.02256v1.pdf`
**Cite:** *Maximum a Posteriori Policy Optimisation* (relative-entropy regularized policy iteration; arXiv:1812.02256). Companion to MPO [arXiv:1806.06920](https://arxiv.org/abs/1806.06920).

### Read first

| Section / theme | Why for this project |
|-----------------|----------------------|
| **E-step temperature dual** | η solved from the **Q-based dual** `g(η)=η·ε_E + η·E_s[log E_a exp(Q/η)]`; weights `= softmax(Q/η)`. Our `controller_agent.py` instead drives a single `log_eta` from the *policy* KL — the defect Exp 8 fixes |
| **M-step decoupled KL** | Separate Lagrange multipliers **α_μ, α_Σ** enforce trust regions on policy **mean** and **covariance** (ε_μ, ε_Σ). These are **missing** in our code → unconstrained M-step → saturation collapse |
| **Hyperparameter robustness** | Same ε across tasks when the dual is correct — supports "fix the dual structure, not the LR/KL numbers" |

### Mapping to Exp 8

| Our choice | Paper language |
|------------|----------------|
| A0 single `log_eta` from policy KL | (incorrect) conflated E-step temp + M-step multiplier |
| A1 E-step Q-dual η + separate α_μ/α_Σ | canonical decoupled-KL MPO E/M-step |

See [mpo-learning-collapse-investigation.md](mpo-learning-collapse-investigation.md) for the symptom-vs-cause evidence.

---

## 6. Related PDFs (same folder, secondary)

| File | Highlight |
|------|-----------|
| `jonschkowski2015_..._robotic_priors.pdf` | **§4 Robotic priors** (temporal coherence, proportionality, causality) as SRL losses |
| `2410.17551_multimodal_information_bottleneck_rl.pdf` | **MIB objective** — compress multimodal latent while keeping task-relevant info |
