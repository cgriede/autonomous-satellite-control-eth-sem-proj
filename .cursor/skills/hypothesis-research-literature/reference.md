# Hypothesis research — extended reference

## Per-paper section map (page-agnostic)

Use PDF search for these headings if page numbers differ between versions.

### 2506.17518 — SRL survey (2025)

- **Abstract** — defines SRL; sample efficiency, generalization, robustness goals
- **Section 2** — problem settings (partial observability, multimodal)
- **Section 3** — taxonomy: reconstruction, contrastive, metric-based, auxiliary, model-based, multimodal
- **Section 4** — evaluation: downstream return, transfer, ablations
- **Section 5** — future: foundation models, multi-task SRL

**Project hook:** Frame `ml_modular_encoder` as multimodal + structured (entity) SRL, not hyperparameter sweep.

### Bruin 2018 — Integrating SRL into RL

- **Figure 1** — shared embedding + parallel SRL loss heads + RL head
- **Section III** — integrated vs sequential training
- **Forward model loss** — predict next embedding from action
- **Inverse model loss** — predict action from state transition
- **Results** — faster learning + better transfer on Torcs

**Project hook:** If A1 encoder wins, next step is auxiliary bearing prediction—not more MLP depth.

### Gorishniy 2022 — Numerical embeddings

- **Section 2** — related: entity embeddings in CTR vs our per-target groups
- **Section 3.1** — PLR (piecewise linear)
- **Section 3.2** — periodic activations
- **Table 2–3** — MLP gains from embeddings on GBDT-friendly data
- **Section 5.3** — embeddings help non-Transformer backbones

**Project hook:** `embed_dim` ablation {3, 8, 16}; optional PLR if linear compress fails.

### Jankovics 2022 — Entity-based RL

- **Introduction** — fixed-size concat vs entity sets
- **Architecture** — slot attention / GNN over entities
- **Results** — training time and robustness vs MLP on structured envs

**Project hook:** Ordered targets along stripe → v1 keeps index; v2 could embed `(bearing_i, seen_i)` pairs with sum pool.

### Jonschkowski 2015 — Robotic priors

- **Section 4.1** — five priors: simplicity, temporal coherence, proportionality, causality, repeatability
- **Section 4.2** — loss formulation
- **Results** — RL on learned states vs raw pixels

**Project hook:** Future SRL aux losses on satellite sim (not v1 modular encoder).

### 2410.17551 — Multimodal IB

- **Method** — image encoder + proprio encoder → bottleneck variable z
- **Objective** — maximize relevant info, compress irrelevant
- **Locomotion results** — sample efficiency vs concat baseline

**Project hook:** Vision + proprio + mission scalars fusion in report; optional IB loss if fusion fork grows.

## Search queries (when library misses)

- `state representation learning reinforcement learning multimodal survey`
- `entity based reinforcement learning structured observation`
- `embeddings numerical features tabular deep learning`
- `deep sets reinforcement learning permutation invariant`
- `model predictive control attitude spacecraft reaction wheel` (MPC — use `research/mpc_lecture` first)

## Integration with other skills

| Skill | Relationship |
|-------|----------------|
| `hypothesis-experiment-cycle` | Research phase runs **before** fork layout |
| `isolated-notebook-hypotheses` | Same JSON contract; literature in §1 analysis card |
| `architecture-planning` | Literature informs slice boundaries |
| `math-physics-technical-docs` | If fork changes documented ML architecture, update `docs/presentation/machine-learning.md` after promote |
