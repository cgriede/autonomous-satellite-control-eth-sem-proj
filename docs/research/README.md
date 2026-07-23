# Research library (`docs/research`)

Local PDFs and reading guides for experiment design and semester-report related work.

**Start here:** [PROJECT_KNOWLEDGE.md](PROJECT_KNOWLEDGE.md) (layer index) · [DECISIONS.md](DECISIONS.md) (accept/reject/defer log)

**Agent skills:**

| Skill | Role |
|-------|------|
| [hypothesis-research-literature](../../.cursor/skills/hypothesis-research-literature/SKILL.md) | Find/acquire papers before experiments |
| [document-research](../../.cursor/skills/document-research/SKILL.md) | Persist reasoning, decisions, investigation notes |
| [generate-code-readme](../../.cursor/skills/generate-code-readme/SKILL.md) | Closeout: README from stored layers |
| [generate-research-report](../../.cursor/skills/generate-research-report/SKILL.md) | Closeout: report from stored layers |

**Lecture / course materials** (scraped from LMS, slides + code) live under [`research/`](../research/) — e.g. [`research/mpc_lecture/`](../research/mpc_lecture/). Search there when the user is taking a relevant course.

## Index

| File | Citation | Topic |
|------|----------|--------|
| [2506.17518_srl_survey_drl.pdf](2506.17518_srl_survey_drl.pdf) | SRL survey for DRL (2025) | Taxonomy, benchmarks, multimodal SRL |
| [bruin2018_integrating_srl_into_rl.pdf](bruin2018_integrating_srl_into_rl.pdf) | Bruin et al., IEEE RA-L 2018 | Joint RL + SRL on shared embedding |
| [gorishniy2022_numerical_feature_embeddings.pdf](gorishniy2022_numerical_feature_embeddings.pdf) | Gorishniy et al., NeurIPS 2022 | Scalar / tabular feature embeddings |
| [2206.02855_efficient_entity_based_rl.pdf](2206.02855_efficient_entity_based_rl.pdf) | Jankovics et al., 2022 | Entity-based / set-structured RL |
| [jonschkowski2015_learning_state_representations_robotic_priors.pdf](jonschkowski2015_learning_state_representations_robotic_priors.pdf) | Jonschkowski & Brock, Autonomous Robots 2015 | Robotic priors for SRL |
| [2410.17551_multimodal_information_bottleneck_rl.pdf](2410.17551_multimodal_information_bottleneck_rl.pdf) | Multimodal IB for DRL (2024) | Vision + proprio fusion |
| [2018_haarnoja_sac.pdf](2018_haarnoja_sac.pdf) | Haarnoja et al., ICML 2018 (arXiv:1801.01290) | Soft Actor-Critic (max-entropy off-policy actor-critic) |
| [1812.02256v1.pdf](1812.02256v1.pdf) | Abdolmaleki et al., 2018 (arXiv:1812.02256) | Decoupled-KL MPO companion (E/M-step duals) |

**Reading guide (section highlights):** [LITERATURE_HIGHLIGHTS.md](LITERATURE_HIGHLIGHTS.md)

**Investigation notes (synthesis, not PDFs):**

| File | Topic |
|------|--------|
| [PROJECT_KNOWLEDGE.md](PROJECT_KNOWLEDGE.md) | Master index — knowledge layers, gates, closeout commands |
| [DECISIONS.md](DECISIONS.md) | Accepted / rejected / deferred choices |
| [model-size-investigation.md](model-size-investigation.md) | MPO network sizing, input-dimension effects, train/eval capacity diagnostics |
| [modular-encoder-r2-investigation.md](modular-encoder-r2-investigation.md) | Exp 6 structured target-array encoding (not image compression); Supported A1 vs A0 |
| [shutter-threshold-investigation.md](shutter-threshold-investigation.md) | Exp 1 reasoning; verdict table in [pipeline/4-documentation/01-shutter-threshold.md](../experiments/pipeline/4-documentation/01-shutter-threshold.md) |

## Naming convention

`{arxiv_or_year}_{short_slug}.pdf` — e.g. `2506.17518_srl_survey_drl.pdf`
