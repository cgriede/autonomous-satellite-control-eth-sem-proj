# ml_sac_hparam_grid

SAC flat encoder hparam screen after positive 50-ep baseline (`9998217234669516_ml_encoder_sac_a0_20-35-29`).

## Grid (6 arms)

| Arm | Size | Reward | Actor / Critic |
|-----|------|--------|----------------|
| `sac_s_sparse` | S | sparse (production shutter credit) | 90 / 140 |
| `sac_s_dense` | S | dense (H6 latent + 10× applied) | 90 / 140 |
| `sac_m_sparse` | M | sparse | 140 / 256 |
| `sac_m_dense` | M | dense | 140 / 256 |
| `sac_l_sparse` | L | sparse | 256 / 512 |
| `sac_l_dense` | L | dense | 256 / 512 |

Shared raised LRs (vs 50-ep baseline): `learning_rate_pi=4.5e-4`, `learning_rate_q=1e-3`, `actor_dropout=0`.

Protocol: dt 1.5s/1.5s, 50 train + 2 eval, 3 train + 2 eval videos (workflow defaults).

## Run

```powershell
conda activate auto-sat
cd D:\code\sem-proj-asc\backend\scripts\experiments\ml_sac_hparam_grid
python .\run.py --show-progress
python .\run.py --show-progress --arms sac_s_sparse,sac_m_sparse
```

Results: `results/sac_hparam_grid_summary.json`, `results/arm_kpis/{arm}.json`
