# Subagent charter — ml_mpo_decoupled_dual_torque (Exp 8)

## Protected paths (read-only during cycle)

- `backend/autonomous_control/**` (import only — production `MPOAgent` with dual fix)
- `backend/simulation/**`
- `backend/render/**`
- `backend/notebooks/s01/**` (imports only)

## Editable paths

- `backend/scripts/experiments/ml_mpo_decoupled_dual_torque/**`
- `docs/experiments/pipeline/**/08-mpo-decoupled-dual-fix.md`

## Entry point

**Only** `run_mpo_torque.py`.

## Concurrency

One pipeline training job per machine — global `pipeline_run_guard` ([D-012](../../../../docs/research/DECISIONS.md)).

## Arm

| Arm | Mode | Reward |
|-----|------|--------|
| `torque_sparse` | torque | sparse |

## Primary KPI

`learning_mode`; eval return vs pre-fix −51.6; KL/η/α bounded; torque saturation < 0.9.

## Artifacts

| Artifact | Path |
|----------|------|
| Summary JSON | `results/mpo_torque.json` |
| Smoke | `results/smoke.json` |
| Hypothesis card | `H8-mpo-decoupled-dual-torque.md` |

## Verdict

`supported` | `not_supported` | `inconclusive` per H8 claims in charter §0.1.
