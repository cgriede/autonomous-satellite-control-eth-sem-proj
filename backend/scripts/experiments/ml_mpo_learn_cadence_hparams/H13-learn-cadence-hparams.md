# Exp 13 — Learn cadence + untouched MPO hyperparams

**Hypothesis ID:** `learn_cadence_hparams`  
**Script:** `run_exp13.py`  
**Pipeline doc:** [`13-mpo-learn-cadence-hparams.md`](../../../../docs/experiments/pipeline/2-run/13-mpo-learn-cadence-hparams.md)

## Single delta

Vary **when** the agent collects (`controller_interval_s`) and **when/how** MPO learns (`train_every_n_steps`, `updates_per_step`) plus optional **MPOConfig** overrides — no reward/architecture change.

## Claims

See pipeline Phase 0.1 (H13a–H13e).

## Run

```powershell
conda activate auto-sat
cd backend/scripts/experiments/ml_mpo_learn_cadence_hparams
python run_exp13.py --smoke
python run_exp13.py --timing-a0
python run_exp13.py --arm baseline_1_1_1 --show-progress
python run_exp13.py --arm cadence_1_1_10 --trim-artifacts --train-episodes 10
```

## Comparator

Exp 8 `9998217164480175_ml_mpo_decoupled_dual_torque_sparse_16-05-19` at `baseline_1_1_1`.
