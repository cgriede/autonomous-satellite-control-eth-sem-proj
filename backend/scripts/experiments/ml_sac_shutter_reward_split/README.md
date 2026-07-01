# ml_sac_shutter_reward_split — Exp 9 SAC shutter reward plane split

**Pipeline:** [09-sac-shutter-reward-split.md](../../../../docs/experiments/pipeline/4-documentation/09-sac-shutter-reward-split.md)

## Hypothesis

Relax **within-budget** shutter waste penalty while keeping **budget-exhausted** penalty. Sparse capture credit already scales with `quality × (1 − cloud_frac)` — agent may learn good pictures without extra `−k_shutter_waste` on low-applied shutters.

## Arms

| Arm | `enable_shutter_waste_penalty` | `enable_budget_exhausted_shutter_penalty` | Run? |
|-----|-------------------------------|-------------------------------------------|------|
| **waste_off_budget_on** | **false** | **true** | **Yes** (treatment) |
| both_on (Exp 7) | true | true | **No** — baseline = `9998217172220712_ml_sac_vector_budget_13-56-17` |

**Note:** Exp 7 run had `enable_shutter_waste_penalty: true` in config; no existing run with waste off only.

## Run

```powershell
conda activate auto-sat
cd backend/scripts/experiments/ml_sac_shutter_reward_split
python run_sac_shutter_reward_split.py --smoke --allow-cpu
python run_sac_shutter_reward_split.py --show-progress
```
