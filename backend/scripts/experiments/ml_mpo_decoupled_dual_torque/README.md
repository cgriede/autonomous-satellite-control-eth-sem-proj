# Exp 8 — MPO fixed dual, sparse, torque (`ml_mpo_decoupled_dual_torque`)

Production `MPOAgent` with decoupled-KL dual fix (`d5af20c`). Single arm: sparse reward, torque mode, dt 1.5 s.

## Run

```powershell
conda activate auto-sat
cd backend/scripts/experiments/ml_mpo_decoupled_dual_torque
python run_mpo_torque.py --smoke --allow-cpu
python run_mpo_torque.py --show-progress
```

## Comparator (read-only)

Pre-fix: `9998217218692971_ml_mpo_model_size_mpo_s_01-01-46` (−51.6 eval, KL→0 frozen).

## Pipeline doc

`docs/experiments/pipeline/4-documentation/08-mpo-decoupled-dual-fix.md`
