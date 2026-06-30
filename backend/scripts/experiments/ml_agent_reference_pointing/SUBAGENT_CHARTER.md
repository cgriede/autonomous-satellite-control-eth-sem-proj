# Subagent charter — ml_agent_reference_pointing (Exp 4)

## Protected paths (read-only during cycle)

- `backend/autonomous_control/**` (import only)
- `backend/simulation/**` (import only — no prod stepper edits)
- `backend/render/**`
- `backend/notebooks/s01/**` (imports only)
- `backend/scripts/experiments/ml_algo_overnight/**` (read-only baseline; copy pattern only)
- `backend/scripts/experiments/ml_sac_mpo_compare/**` (read-only until Exp 3 closeout)

## Editable paths

- `backend/scripts/experiments/ml_agent_reference_pointing/**`
- `docs/experiments/pipeline/**/04-agent-reference-pointing.md` (stage updates)

## Entry point

**Only** `run_agent_reference.py`.

## Concurrency

One **pipeline** training job per machine — global `pipeline_run_guard` ([D-012](../../../../docs/research/DECISIONS.md)).

## Arms

| Arm | `attitude_request_mode` | Agent | Reward |
|-----|-------------------------|-------|--------|
| `ref0` | `torque` | SAC | sparse |
| `ref1` | `vector` | SAC | sparse |
| `ref2` (optional) | `vector` | MPO | dense |

## Primary KPIs

`learning_mode`; eval return; capture yield; `reference_clamp_count`; `safe_mode_takeover_count` (expect ~0 on vector arms).

## Artifacts

| Artifact | Path |
|----------|------|
| Summary JSON | `results/agent_reference.json` |
| Analysis card | `agent_reference_analysis.md` |
| Smoke | `results/smoke.json` |

## Verdict

`supported` | `inconclusive` | `falsified` per arm vs H4 claims in pipeline doc.

## Gate

Do **not** start full Phase 2 runs until Exp 3 (`ml_sac_mpo_compare`) closeout.
