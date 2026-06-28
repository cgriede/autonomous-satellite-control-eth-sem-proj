# Subagent charter — ML algo overnight

## Protected paths (read-only during cycle)

- `backend/autonomous_control/**`
- `backend/simulation/**`
- `backend/notebooks/s01/**` (imports only)
- `backend/render/**`

## Editable paths

- `backend/scripts/experiments/ml_algo_overnight/**`
- `results/` under this experiment folder

## Entry point

**Only** `run_overnight.py`. Phase logic in `_phases/*.py` — not separate schedulable scripts.

## Concurrency

One training job per machine via `.experiment_run.lock` (`_run_guard.py`).

## Deliverables

| Phase | JSON | Analysis card |
|-------|------|---------------|
| smoke | `results/smoke.json` | — |
| H0 | `results/dt_profile.json` | `H0-dt-profile.md` |
| H1a | `results/h1a_mpo_sparse.json` | `H1-mpo-sparse_analysis.md` |
| H1b | `results/h1b_mpo_stable_eta.json` | `H1b-mpo-stable-eta_analysis.md` |
| H6 | `results/h6_mpo_dense_latent.json` | `H6-dense-latent_analysis.md` |
| H4 | `results/h4_sac.json` | `H4-sac_analysis.md` |

Plus `results/overnight_summary.json` and `results/overnight.log`.

## Primary KPI

`learning_mode` from `_runner_common.evaluate_learning_mode` — not baseline beat.

## Verdict

`supported` | `inconclusive` | `falsified` per phase JSON.
