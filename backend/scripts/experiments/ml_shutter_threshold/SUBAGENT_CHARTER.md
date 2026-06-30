# Subagent charter — ml_shutter_threshold

## Protected paths (read-only during cycle)

- `backend/autonomous_control/**`
- `backend/simulation/**` (runtime monkeypatch only via experiment forks)
- `backend/notebooks/s01/**` (imports only)
- `backend/render/**`

## Editable paths

- `backend/scripts/experiments/ml_shutter_threshold/**`
- `results/` under this experiment folder
- `docs/ml/experiments/STATUS_2026-06.md` (status rows at closeout)

## Entry point

**Only** `run_shutter_threshold.py`.

## Concurrency

One **pipeline** training job per machine — global lock via `backend/scripts/experiments/pipeline_run_guard.py` (`.pipeline_run.lock`; mirror `.active_run.json`). No parallel slug even in different experiment folders ([D-012](../../../../docs/research/DECISIONS.md)).

## Primary KPI

Shutter cmds/ep reduction at 0.9 vs 0.5; secondary: `learning_mode`, train returns.

## Verdict

`supported` | `inconclusive` | `falsified` per arm in summary JSON.
