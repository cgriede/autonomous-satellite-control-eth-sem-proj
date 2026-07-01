# Subagent charter — ml_mpo_decoupled_dual_vector (Exp 11)

## Protected paths (read-only during cycle)

- `backend/autonomous_control/**` (import only — production `MPOAgent` with dual fix)
- `backend/simulation/**`
- `backend/render/**`
- `backend/notebooks/s01/**` (imports only)

## Editable paths

- `backend/scripts/experiments/ml_mpo_decoupled_dual_vector/**`
- `docs/experiments/pipeline/**/11-mpo-decoupled-dual-vector.md`

## Entry point

**Only** `run_mpo_vector.py`.

## Concurrency

One pipeline training job per machine — global `pipeline_run_guard` ([D-012](../../../../docs/research/DECISIONS.md)).

## Arm

| Arm | Mode | Reward |
|-----|------|--------|
| `vector_sparse` | vector | sparse |

## Primary KPI

`learning_mode`; eval return vs Exp 8 torque (−81.1); KL/η/α bounded; torque saturation < 0.9.

## Artifacts

| Artifact | Path |
|----------|------|
| Summary JSON | `results/mpo_vector.json` |
| Smoke | `results/smoke.json` |
| Hypothesis card | `H11-mpo-decoupled-dual-vector.md` |

## Verdict

`supported` | `not_supported` | `inconclusive` per H11 claims in pipeline doc §0.1.
