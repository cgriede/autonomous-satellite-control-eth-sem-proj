# Exp 12 — MPO vector + torque effort (`ml_mpo_vector_torque_effort`)

**Pipeline:** [12-mpo-vector-torque-effort.md](../../../../docs/experiments/pipeline/3-evaluation/12-mpo-vector-torque-effort.md)

Production `MPOAgent`, vector OBC, sparse reward — **single delta:** force `enable_torque_effort=True` (production disables effort in vector mode).

## Run

```powershell
conda activate auto-sat
cd backend/scripts/experiments/ml_mpo_vector_torque_effort
python run_mpo_vector_torque_effort.py --smoke --allow-cpu
python run_mpo_vector_torque_effort.py --show-progress
```

## Comparator

Exp 11 vector (effort off) — run in same overnight batch before this arm.

## Status

**Phase 2** — ready for overnight queue slot 3.
