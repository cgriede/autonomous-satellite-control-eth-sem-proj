# Subagent charter — ml_mpo_episode_seed_diversity (Exp 15)

## Protected paths (read-only during cycle)

- `backend/autonomous_control/**` (import only)
- `backend/simulation/**` (import only)
- `backend/render/**`
- `backend/notebooks/s01/**` (imports only)

## Editable paths

- `backend/scripts/experiments/ml_mpo_episode_seed_diversity/**`
- `docs/experiments/pipeline/**/15-mpo-episode-seed-diversity.md`

## Entry point

**Only** `run.py`.

## Concurrency

One pipeline training job per machine — global `pipeline_run_guard` ([D-012](../../../docs/research/DECISIONS.md)).

## Stages

| Stage | Command | Episodes |
|-------|---------|----------|
| Verify | `--verify` | checks only |
| Smoke | `--smoke` | 1 warmup + 2 train (paired baseline) |
| Full | `--full` | 5 warmup + 50 train (default) + paired eval |
| Eval | `--eval-comparison` | 5 held-out paired seeds |

## Primary KPI

`delta_score_mean` = mean(treatment − baseline) over identical eval seeds.

## Verdict

`supported` | `not_supported` | `inconclusive` per H15 claims in pipeline doc Phase 0.
