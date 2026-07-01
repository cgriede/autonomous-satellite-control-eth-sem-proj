# Subagent charter — ml_mpo_learn_cadence_hparams (Exp 13)

## Protected paths (read-only during cycle)

- `backend/autonomous_control/**` (import only)
- `backend/simulation/**`
- `backend/render/**`
- `backend/notebooks/s01/**` (imports only)

## Editable paths

- `backend/scripts/experiments/ml_mpo_learn_cadence_hparams/**`
- `docs/experiments/pipeline/**/13-mpo-learn-cadence-hparams.md`

## Entry point

**Only** `run_exp13.py`.

## Concurrency

One pipeline training job per machine — global `pipeline_run_guard` ([D-012](../../../../docs/research/DECISIONS.md)).

## Arms

### Track A — cadence (sim : collect : learn)

| arm_id | ratio | controller_interval_s | train_every | updates |
|--------|-------|----------------------|-------------|---------|
| `baseline_1_1_1` | 1:1:1 | 1.5 | 1 | 1 |
| `cadence_1_1_10` | 1:1:10 | 1.5 | 10 | 10 |
| `cadence_1_1_50` | 1:1:50 | 1.5 | 50 | 50 |
| `cadence_1_2_4` | 1:2:4 | 3.0 | 4 | 4 |
| `duty_100x100` | 1:1:100 | 1.5 | 100 | 100 |

### Track B — hparam screen (on cadence winner)

See `_hparam_profiles.py` (`hparam_*` arm_ids).

## Primary KPI

Track A: `wall_s`, `steps_per_s`, eval/train return parity vs baseline; pick fastest parity-passing cadence.  
Track B: eval return / wall vs default hparams on winning cadence.

## Artifacts

| Artifact | Path |
|----------|------|
| Summary JSON | `results/learn_cadence_hparams_summary.json` |
| Smoke | `results/smoke.json` |
| Timing A0 | `results/timing_a0.json`, `results/timing_a0.md` |
| Per-arm | `results/<arm_id>.json` |
| Hypothesis card | `H13-learn-cadence-hparams.md` |

## Verdict

`supported` | `not_supported` | `partial` | `inconclusive` per H13 claims in pipeline Phase 0.
