# H1 — Modular encoder (SAC sparse)

**Experiment:** `ml_modular_encoder`  
**Decision context:** [D-006](../../../../docs/research/DECISIONS.md) — test encoder structure before MPO width ablation.

## Single logical delta

Replace flat concat of 50-D bearing + 50-D mask vectors with **`Linear(n, k)` compressors** (`k=8` default) while keeping passthrough globals and vision CNN path unchanged.

## Arms

| ID | `encoder_kind` | Hypothesis ID |
|----|----------------|---------------|
| `sac_a0` | `flat` | `encoder_flat_baseline` |
| `sac_a1` | `compress` | `encoder_vector_compress` |

## Frozen protocol

| Knob | Value |
|------|-------|
| Agent | SAC sparse (`_reward_fork`) |
| dt | 1.5 s / 1.5 s |
| Train episodes | 7 |
| Warmup | 5 (cached bundle rebuild per arm) |
| Eval | 2 |

## Literature basis

- Entity-/set-structured observations: ordered target slots → group bottleneck (not full Deep Sets).
- Multimodal fusion: CNN vision + scalar passthrough + compressed vectors → trunk MLP.
- See plan § Literature & naming and [model-size-investigation.md](../../../../docs/research/model-size-investigation.md).

## Primary KPI

`learning_mode` true and improved train/eval returns vs A0.

## JSON contract

`results/modular_encoder_summary.json` — arms map with verdict, `learning_mode`, returns, `wall_s`.
