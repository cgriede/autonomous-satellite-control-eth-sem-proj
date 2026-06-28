# Subagent charter — ML learning signal

## Protected paths (read-only during experiments)

- `backend/autonomous_control/**` (except promote phase)
- `backend/simulation/**`
- `backend/notebooks/s01/**` (except experiment imports)
- `backend/render/**`

## Editable paths

| Branch | May edit |
|--------|----------|
| orchestrator | `_runner_common.py`, `_frozen_baseline.py`, `run_baseline.py`, `results/` |
| A fundamental | `a_fundamental_limit/**`, `results/fundamental_*` |
| B bug hunt | `b_bug_hunt/**` (forks + runners only) |
| C hparam | `c_hparam_search/**` |

## Budget

- **3 train episodes** per branch run (warmup from cache, not counted)
- **Max 3 treatment runs** per branch after shared baseline
- Do not rebuild warmup cache unless fingerprint changes
- **One concurrent training job on a dev machine** — enforced by `results/../.experiment_run.lock` via `_run_guard.py` (second `run_*.py` exits immediately). Subagents must not launch parallel runners on the same host.

## Deliverables per branch

- `results/<branch>_*.json` (fixed contract)
- `results/<hypothesis_id>_analysis.md` (8-section card)
- Verdict: `supported` | `falsified` | `inconclusive`

## Primary KPI

`increasing_signal.strong_lead` from `_runner_common.evaluate_increasing_signal`.

## Debug workflow

Probe logs under `.cursor/debug_logs/` only (topic prefix `ml_learning_signal`).
