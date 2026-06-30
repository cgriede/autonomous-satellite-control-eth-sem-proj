# Subagent charter — ml_modular_encoder_r2

## Protected paths (read-only during cycle)

- `backend/autonomous_control/**` (import only)
- `backend/simulation/**`
- `backend/render/**`
- `backend/notebooks/s01/**` (imports only)

## Editable paths

- `backend/scripts/experiments/ml_modular_encoder_r2/**`
- `docs/experiments/pipeline/**` (stage updates for Exp 6)
- `docs/ml/experiments/STATUS_2026-06.md` (closeout row only)

## Entry point

**Only** `run_modular_encoder_r2.py`.

## Concurrency

One **pipeline** training job per machine — global `pipeline_run_guard` ([D-012](../../../../docs/research/DECISIONS.md)). Slug: `ml_modular_encoder_r2`.

## Primary KPI

A1 vs A0: `learning_mode`, best train return, eval return (≥10% gap), `shutter_meaningful_fraction`.

## Verdict

`supported` | `inconclusive` | `falsified` per arm in `modular_encoder_r2_summary.json`.

## Success bar (H2r)

| Claim | Criterion |
|-------|-----------|
| H2ra | A1 `learning_mode` true while A0 false, or A1 eval return ↑ ≥10% vs A0 |
| H2rb | A1 best train return > A0 |
| H2rc | A1 improves secondary KPIs at equal return |

If **no difference** after profile train slice → stop (no split heads).

## Gates before Phase 2 run

- Exp 3 closeout — reward mode for SAC path  
- **Exp 5 closeout** — `ml_mpo_model_size` width ablation  
- Freeze `profile.json` `reward_mode` + `ref_run_id` in DECISIONS  

## Blocked by

`ml_mpo_model_size` (Exp 5) — build/smoke OK; full training deferred.
