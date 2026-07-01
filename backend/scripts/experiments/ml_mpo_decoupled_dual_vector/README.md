# Exp 11 — MPO fixed dual, sparse, vector (`ml_mpo_decoupled_dual_vector`)

Production `MPOAgent` with decoupled-KL dual fix (`d5af20c`). Single arm: sparse reward, **vector** OBC mode, dt 1.5 s.

## Run

```powershell
conda activate auto-sat
cd backend/scripts/experiments/ml_mpo_decoupled_dual_vector
python run_mpo_vector.py --smoke --allow-cpu
python run_mpo_vector.py --show-progress
```

## Comparator (read-only)

Exp 8 torque: `9998217164480175_ml_mpo_decoupled_dual_torque_sparse_16-05-19` (train_best +8.7, eval_mean −81.1).

## Pipeline doc

`docs/experiments/pipeline/3-evaluation/11-mpo-decoupled-dual-vector.md`

## Status

**Phase 2** — ready for overnight run (queue slot 2).
