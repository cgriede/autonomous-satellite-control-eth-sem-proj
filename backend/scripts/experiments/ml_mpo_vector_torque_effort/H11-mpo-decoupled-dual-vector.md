# H11 — MPO fixed decoupled-KL dual, sparse, vector mode

**Experiment:** `ml_mpo_decoupled_dual_vector`  
**Fix commit:** `d5af20c` — decoupled E-step η + M-step α_μ/α_Σ trust region in production `MPOAgent`  
**Investigation:** [mpo-learning-collapse-investigation.md](../../../../docs/research/mpo-learning-collapse-investigation.md)

## Single logical delta

No agent fork — uses production `MPOAgent` after the dual fix. One arm: **sparse reward + vector OBC mode** @ dt 1.5 s, same protocol as Exp 8 except `attitude_request_mode=vector`.

## Arm

| ID | Mode | Reward | Hypothesis ID |
|----|------|--------|---------------|
| `vector_sparse` | vector | sparse | `mpo_dual_vector_sparse` |

## Frozen protocol

| Knob | Value |
|------|-------|
| dt | 1.5 s / 1.5 s |
| seed | 7 |
| warmup | 5 (rebuild) |
| train | 50 |
| eval | 2 |
| actor/critic | 90/140 (production S) |
| LRs | π 4.5e-4, Q 1e-3, dropout 0 (match Exp 8) |
| Dual | `eps_eta=0.1`, `target_kl_mu=0.1`, `target_kl_sigma=0.01`, `lr_alpha=1e-3` (MPOConfig defaults) |

## Numbered claims

| ID | Claim |
|----|-------|
| **H11a** | Vector eval ≥ Exp 8 torque **or** `learning_mode=true` in both |
| **H11b** | KL/η bounded (no η→1e11 ramp) |
| **H11c** | `torque_saturated_fraction` < 0.9 |

## Primary KPI

`learning_mode`; eval return vs Exp 8 torque canonical run; KL/η/α bounded.

## Comparator (read-only)

Exp 8: `9998217164480175_ml_mpo_decoupled_dual_torque_sparse_16-05-19`

## Pipeline doc

[11-mpo-decoupled-dual-vector.md](../../../../docs/experiments/pipeline/3-evaluation/11-mpo-decoupled-dual-vector.md)
