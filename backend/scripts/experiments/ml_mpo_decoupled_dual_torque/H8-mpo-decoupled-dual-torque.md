# H8 — MPO fixed decoupled-KL dual, sparse, torque mode

**Experiment:** `ml_mpo_decoupled_dual_torque`  
**Fix commit:** `d5af20c` — decoupled E-step η + M-step α_μ/α_Σ trust region in production `MPOAgent`  
**Investigation:** [mpo-learning-collapse-investigation.md](../../../../docs/research/mpo-learning-collapse-investigation.md)

## Single logical delta

No agent fork — uses production `MPOAgent` after the dual fix. One arm: **sparse reward + torque mode** @ dt 1.5 s, same protocol as Exp 5 `mpo_s` pre-fix comparator.

## Arm

| ID | Mode | Reward | Hypothesis ID |
|----|------|--------|---------------|
| `torque_sparse` | torque | sparse | `mpo_dual_torque_sparse` |

## Frozen protocol

| Knob | Value |
|------|-------|
| dt | 1.5 s / 1.5 s |
| seed | 7 |
| warmup | 5 (rebuild) |
| train | 50 |
| eval | 2 |
| actor/critic | 90/140 (production S) |
| LRs | π 4.5e-4, Q 1e-3, dropout 0 (match Exp 5) |
| Dual | `eps_eta=0.1`, `target_kl_mu=0.1`, `target_kl_sigma=0.01`, `lr_alpha=1e-3` (MPOConfig defaults) |

## Numbered claims

| ID | Claim |
|----|-------|
| **H8a** | `learning_mode=true` or eval ≥ −41 |
| **H8b** | KL/η bounded (no η→1e11 ramp) |
| **H8c** | `torque_saturated_fraction` < 0.9 |
| **H8d** | α_μ/α_Σ finite and active |

## Primary KPI

`learning_mode`; eval return vs pre-fix −51.6 floor; KL/η/α per episode; `action_diagnostics`.

## JSON contract

- `results/mpo_torque.json` — full arm KPIs
- `results/smoke.json` — smoke pass + first-step dual metrics

## Smoke

`python run_mpo_torque.py --smoke --allow-cpu` — warmup + one `train()`; assert `log_alpha_mu`/`log_alpha_sigma` on agent; finite `kl`, `alpha_mu`, `alpha_sigma`, `eta`.

## Literature basis

- **Abdolmaleki et al. 2018** (`1812.02256v1.pdf`) — decoupled-KL MPO E/M-step dual.
- [mpo-learning-collapse-investigation.md](../../../../docs/research/mpo-learning-collapse-investigation.md) — symptom-vs-cause evidence.
