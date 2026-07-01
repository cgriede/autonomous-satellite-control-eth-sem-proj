# ml_mpo_learn_cadence_hparams (Exp 13)

MPO learn cadence sweep + untouched hyperparam screen on Exp 8 decoupled-KL sparse torque protocol.

## Quick start

```powershell
conda activate auto-sat
python backend/scripts/experiments/ml_mpo_learn_cadence_hparams/run_exp13.py --smoke
```

## Layout

| File | Role |
|------|------|
| `run_exp13.py` | CLI entry |
| `_cadence_profiles.py` | Track A arm specs |
| `_hparam_profiles.py` | Track B OAT hparam arms |
| `_runner.py` | Run + timing helpers |
| `profile.json` | Frozen workflow + shared MPO overrides |
| `SUBAGENT_CHARTER.md` | Protected vs editable paths |

## Mutex

Uses global `pipeline_run_guard` via `_run_guard.py`.
