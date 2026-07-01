# Subagent charter — ml_mpo_safe_mode_penalty (Exp 10)

## Protected paths (read-only during cycle)

- `backend/autonomous_control/**` (import only — production `MPOAgent` with dual fix)
- `backend/simulation/**` (runtime monkeypatch only via experiment `_safe_mode_reward_fork.py`)
- `backend/render/**`
- `backend/notebooks/s01/**` (imports only)

## Editable paths

- `backend/scripts/experiments/ml_mpo_safe_mode_penalty/**`
- `docs/experiments/pipeline/**/10-mpo-safe-mode-penalty.md`

## Entry point

**Only** `run_mpo_safe_mode_penalty.py`.

## Concurrency

One pipeline training job per machine — global `pipeline_run_guard` ([D-012](../../../../docs/research/DECISIONS.md)).

## Arm

| Arm | `enable_safe_mode_penalty` | Reward |
|-----|---------------------------|--------|
| `safe_mode_penalty_on` | **true** | sparse + per-step safe-mode penalty |

Comparator (read-only): Exp 8 run `9998217164480175_ml_mpo_decoupled_dual_torque_sparse_16-05-19`.

## Primary KPI

`learning_mode`; `safe_mode_activations`/ep vs Exp 8; eval return vs Exp 8 (−81.1); torque saturation < Exp 8 (~0.95).

## Artifacts

| Artifact | Path |
|----------|------|
| Summary JSON | `results/mpo_safe_mode_penalty.json` |
| Smoke | `results/smoke.json` |
| Hypothesis card | `H10-mpo-safe-mode-penalty.md` |

## Verdict

`supported` | `not_supported` | `partial` | `inconclusive` per H10 claims in pipeline Phase 0.1.
