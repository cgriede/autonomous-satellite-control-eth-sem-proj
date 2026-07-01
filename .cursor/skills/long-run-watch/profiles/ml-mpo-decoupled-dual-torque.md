# Profile: ml-mpo-decoupled-dual-torque

**Profile id:** `ml-mpo-decoupled-dual-torque`

Pipeline **Exp 8** — `ml_mpo_decoupled_dual_torque` (MPO fixed dual, sparse, torque).

## Environment

```powershell
$env:KMP_DUPLICATE_LIB_OK='TRUE'
conda activate auto-sat
```

## Paths (repo root)

| Artifact | Path |
|----------|------|
| Runner | `backend/scripts/experiments/ml_mpo_decoupled_dual_torque/run_mpo_torque.py` |
| Human log | `backend/scripts/experiments/ml_mpo_decoupled_dual_torque/results/mpo_torque.log` |
| Summary (completion) | `backend/scripts/experiments/ml_mpo_decoupled_dual_torque/results/mpo_torque.json` |
| Smoke (preflight) | `backend/scripts/experiments/ml_mpo_decoupled_dual_torque/results/smoke.json` |
| Pipeline lock | `backend/scripts/experiments/.pipeline_run.lock` |
| Active run mirror | `docs/experiments/pipeline/.active_run.json` |
| Pipeline doc | `docs/experiments/pipeline/3-evaluation/08-mpo-decoupled-dual-fix.md` |
| Message queue | `.cursor/agents-discussion/message-queue.md` |

## Process check

```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match 'ml_mpo_decoupled_dual_torque\\run_mpo_torque\.py' } |
  Select-Object ProcessId, CommandLine
```

## Read state

```powershell
Get-Content backend/scripts/experiments/ml_mpo_decoupled_dual_torque/results/mpo_torque.log -Tail 20
```

Tail active run `run_log.md` / `telemetry/current_step.json` under latest `backend/autonomous_control/runs/*_ml_mpo_decoupled_*` (non-smoke).

## Completion criteria

`mpo_torque.json` exists **and** no matching python process.

## Start command

```powershell
conda activate auto-sat
cd D:\code\sem-proj-asc\backend\scripts\experiments\ml_mpo_decoupled_dual_torque
python run_mpo_torque.py --show-progress
```

Preflight smoke (already passed 2026-06-30):

```powershell
python run_mpo_torque.py --smoke --allow-cpu
```

## Light-fix scope

`backend/scripts/experiments/ml_mpo_decoupled_dual_torque/` only:

- Stale `.pipeline_run.lock` when no matching process (and Exp 9 not running).
- `KMP_DUPLICATE_LIB_OK=TRUE`.
- Re-run after import/env fix.

## Ask user first

- `--trim-artifacts`, hyperparameter changes.
- Launch while another pipeline slug holds lock.

## Final summary

Read `mpo_torque.json` → `learning_mode`, `eval_return_mean`, KL/η/α metrics vs pre-fix baseline `9998217218692971_ml_mpo_model_size_mpo_s_01-01-46`. Cite run_dir MP4s for behavioral evidence.
