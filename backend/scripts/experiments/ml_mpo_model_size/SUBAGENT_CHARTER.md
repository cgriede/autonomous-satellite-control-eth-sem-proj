# Subagent charter — ml_mpo_model_size (Exp 5)

## Protected paths (read-only during cycle)

- `backend/autonomous_control/**` (import only — use production `MPOAgent`)
- `backend/simulation/**`
- `backend/render/**`
- `backend/notebooks/s01/**` (imports only)
- `backend/scripts/experiments/ml_algo_overnight/**` (read-only baseline; copy pattern only)

## Editable paths

- `backend/scripts/experiments/ml_mpo_model_size/**`
- `docs/experiments/pipeline/**/05-mpo-model-size.md` (stage updates)

## Entry point

**Only** `run_mpo_model_size.py`.

## Concurrency

One **pipeline** training job per machine — global `pipeline_run_guard` ([D-012](../../../../docs/research/DECISIONS.md)).

## Arms

| Arm | Size | Hypothesis |
|-----|------|------------|
| `mpo_s` | S (90/140) | Production default — under-capacity baseline |
| `mpo_m` | M (140/256) | Mid-scale (MPO 2018 humanoid-adjacent) |
| `mpo_l` | L (256/512) | Open-source “Large MPO” scale |

Reward mode: **one fork for all arms** — CLI `--reward-mode sparse|dense` (scaffold default sparse).

## Primary KPI

`learning_mode`; eval return vs S/warmup; MPO KL/η (last train ep); monotonic width when learnable (H5a/H5b).

## Artifacts

| Artifact | Path |
|----------|------|
| Summary JSON | `results/mpo_model_size_summary.json` |
| Per-arm KPIs | `results/arm_kpis/{arm}.json` |
| Smoke | `results/smoke.json` |
| Hypothesis card | `H5-mpo-model-size.md` |

## Verdict

`supported` | `not_supported` | `inconclusive` per H5 claims in charter §0.1.

## Run order

S → M → L (L may OOM or slow).
