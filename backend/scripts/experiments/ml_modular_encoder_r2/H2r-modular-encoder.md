# H2r — Modular encoder r2 (SAC)

**Experiment:** `ml_modular_encoder_r2` (Exp 6)  
**Predecessor:** Exp 2 v1 (`ml_modular_encoder`) — [02-modular-encoder.md](../../../../docs/experiments/pipeline/4-documentation/02-modular-encoder.md)  
**Decision context:** [D-015](../../../../docs/research/DECISIONS.md) — retest encoder structure in a learnable regime after Exp 3 + Exp 5.

## Single logical delta vs v1

**Protocol only** — reward mode + train length + raised LRs from Exp 3/5 gates. Encoder arms unchanged.

## Arms

| ID | `encoder_kind` | Hypothesis ID |
|----|----------------|---------------|
| `sac_a0` | `flat` | `encoder_flat_baseline` |
| `sac_a1` | `compress` | `encoder_vector_compress` |

## Frozen protocol (placeholder — update after gates)

| Knob | Placeholder | Gate |
|------|-------------|------|
| Agent | SAC | unchanged |
| Reward | `sparse` (`profile.json`) | Exp 3 SAC path; else dense if Exp 5 M/L learns |
| dt | 1.5 s / 1.5 s | unchanged [D-002] |
| Train episodes | 50 | Match learnable slice from Exp 3/5 |
| Warmup | 5 (rebuild per arm) | unchanged |
| Eval | 2 | unchanged |
| LRs | pi=4.5e-4, q=1e-3, dropout=0 | hparam grid raised values |

## Hypothesis statements

> With reward / training protocol aligned to the best learnable regime from Exp 3 + Exp 5, **A1** beats **A0** on `learning_mode` and eval return.

## Primary KPI

`learning_mode` true and improved train/eval returns vs A0; secondary: shutter meaningful fraction.

## JSON contract

`results/modular_encoder_r2_summary.json` — arms map with verdict, `learning_mode`, returns, `wall_s`, `reward_mode`.

## Blocked by

Exp 5 (`ml_mpo_model_size`) closeout before Phase 2 full run.
