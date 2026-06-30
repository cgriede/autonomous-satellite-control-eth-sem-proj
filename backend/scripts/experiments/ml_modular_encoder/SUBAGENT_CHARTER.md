# Subagent charter — ml_modular_encoder

## Protected paths (read-only during cycle)

- `backend/autonomous_control/**` (import only)
- `backend/simulation/**`
- `backend/render/**`
- `backend/notebooks/s01/**` (imports only)

## Editable paths

- `backend/scripts/experiments/ml_modular_encoder/**`
- `docs/experiments/pipeline/4-documentation/02-modular-encoder.md` (stage updates)
- `docs/ml/experiments/STATUS_2026-06.md` (closeout row only)

## Entry point

**Only** `run_modular_encoder.py`.

## Concurrency

One **pipeline** training job per machine — global `pipeline_run_guard` ([D-012](../../../../docs/research/DECISIONS.md)).

## Primary KPI

A1 vs A0: `learning_mode`, best train return, `positive_reward_steps`, shutter meaningful fraction.

## Verdict

`supported` | `inconclusive` | `falsified` per arm in `modular_encoder_summary.json`.

## Success bar

A1 **strictly better** than A0 on learning KPIs. If **no difference** after 7 eps → stop (do not add split heads).
