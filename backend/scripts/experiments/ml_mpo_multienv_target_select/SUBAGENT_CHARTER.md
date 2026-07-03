# Subagent charter — ml_mpo_multienv_target_select (Exp 14)

## Protected paths (read-only during cycle)

- `backend/autonomous_control/**` (import only)
- `backend/simulation/**` (import only)
- `backend/render/**`
- `backend/notebooks/s01/**` (imports only)

## Editable paths

- `backend/scripts/experiments/ml_mpo_multienv_target_select/**`
- `docs/experiments/pipeline/**/14-mpo-multienv-target-select.md`

## Entry point

**Only** `run.py`.

## Concurrency

One pipeline training job per machine — global `pipeline_run_guard` ([D-012](../../../docs/research/DECISIONS.md)).

## Stages

| Stage | Command | Episodes |
|-------|---------|----------|
| Verify | `--verify` | checks only |
| Smoke | `--smoke` | 1 warmup + 2 train |
| Screen | `--screen` | 5 arms × (5+20+1) |
| Full | `--full` | 10 env × (5+30) |
| Eval baseline | `--eval-baseline` | 5 held-out seeds |

## Primary KPI

`score_mean` over 5 held-out eval envs (quality × coverage); training return secondary.

## Artifacts

| Artifact | Path |
|----------|------|
| Smoke | `results/smoke.json` |
| Screen summary | `results/screen_summary.json` |
| Stage B | `results/stage_b_summary.json` |
| Eval comparison | `results/eval_comparison.json` |

## Verdict

`supported` | `not_supported` | `inconclusive` per H14 claims in pipeline doc Phase 0.
