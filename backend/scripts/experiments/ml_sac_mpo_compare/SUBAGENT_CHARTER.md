# Subagent charter — ml_sac_mpo_compare (Exp 3)

## Protected paths (read-only during cycle)

- `backend/autonomous_control/**` (import only)
- `backend/simulation/**`
- `backend/render/**`
- `backend/notebooks/s01/**` (imports only)
- `backend/scripts/experiments/ml_algo_overnight/**` (read-only baseline; copy pattern only)

## Editable paths

- `backend/scripts/experiments/ml_sac_mpo_compare/**`
- `docs/experiments/pipeline/**/03-sac-mpo-compare.md` (stage updates)

## Entry point

**Only** `run_sac_mpo_compare.py`.

## Concurrency

One **pipeline** training job per machine — global `pipeline_run_guard` ([D-012](../../../../docs/research/DECISIONS.md)).

## Arms

| Arm | Agent | Reward |
|-----|-------|--------|
| `compare_sac` | SAC | sparse |
| `compare_mpo` | MPO | dense (H6 formula) |

## Primary KPI

`learning_mode`, eval return, `positive_reward_steps`, MPO `kl_mean_last`, early-abort flags.

## Artifacts

| Artifact | Path |
|----------|------|
| Summary JSON | `results/compare_sac_mpo.json` |
| Analysis card | `compare_sac_mpo_analysis.md` |
| Smoke | `results/smoke.json` |

## Verdict

`supported` | `inconclusive` | `falsified` per arm in summary JSON.
