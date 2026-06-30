# Profile: ml-pipeline-overnight

**Profile id:** `ml-pipeline-overnight`

Sequential orchestrator for pipeline **Exp 3–6** (`ml_pipeline_overnight/run_pipeline_overnight.py`).

## Environment

```powershell
$env:KMP_DUPLICATE_LIB_OK='TRUE'
conda activate auto-sat
```

## Paths (repo root)

| Artifact | Path |
|----------|------|
| Orchestrator | `backend/scripts/experiments/ml_pipeline_overnight/run_pipeline_overnight.py` |
| Human log | `backend/scripts/experiments/ml_pipeline_overnight/results/pipeline_overnight.log` |
| Summary (completion) | `backend/scripts/experiments/ml_pipeline_overnight/results/pipeline_overnight_summary.json` |
| Step errors | `backend/scripts/experiments/ml_pipeline_overnight/results/exp*_error.json` |
| Pipeline lock | `backend/scripts/experiments/.pipeline_run.lock` |
| Active run mirror | `docs/experiments/pipeline/.active_run.json` |
| Per-step summaries | see [orchestrator README](../../../backend/scripts/experiments/ml_pipeline_overnight/README.md) |
| Message queue | `.cursor/agents-discussion/message-queue.md` |

## Process check

```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match 'ml_pipeline_overnight\\run_pipeline_overnight\.py' } |
  Select-Object ProcessId, CommandLine
```

Also check child slugs (only one should run at a time):

```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match 'ml_sac_mpo_compare|ml_agent_reference|ml_mpo_model_size|ml_modular_encoder_r2' } |
  Select-Object ProcessId, CommandLine
```

## Read state

```powershell
Get-Content backend/scripts/experiments/ml_pipeline_overnight/results/pipeline_overnight.log -Tail 40 -ErrorAction SilentlyContinue
python backend/scripts/experiments/ml_pipeline_overnight/run_pipeline_overnight.py --preflight
```

Tail the **active child** log when a step is running, e.g.:

- `ml_sac_mpo_compare/results/compare.log`
- `ml_mpo_model_size/results/mpo_model_size.log` (if present)

## Completion criteria

`pipeline_overnight_summary.json` exists **and** no orchestrator process (above).  
All **selected** steps show `status: completed` or `skipped_complete` in summary JSON.

## Start command

(only if user asked you to launch)

```powershell
conda activate auto-sat
cd D:\code\sem-proj-asc\backend\scripts\experiments\ml_pipeline_overnight
python .\run_pipeline_overnight.py --show-progress --protocol learnable
```

Preflight / smoke before long run:

```powershell
python .\run_pipeline_overnight.py --preflight
python .\run_pipeline_overnight.py --smoke-all --allow-cpu
```

## Resume

```powershell
python .\run_pipeline_overnight.py --from exp5 --show-progress --protocol learnable
python .\run_pipeline_overnight.py --steps exp3 --show-progress --force
```

## Light-fix scope

Only inside `backend/scripts/experiments/ml_pipeline_overnight/` and **child slug folders** (Exp 3–6):

- Stale `.pipeline_run.lock` when no matching process.
- `--smoke-all --allow-cpu` after import/env fix.
- `--from <step>` / `--continue-on-error` when a step errored but queue should continue.
- `KMP_DUPLICATE_LIB_OK=TRUE` on Windows.

**Do not** edit production `autonomous_control/` / `simulation/` / `render/` during watch without user approval.

## Ask user first

- `--protocol charter` vs `learnable` (train length / patience / exp5 reward).
- `--ignore-gates` (skip exp3 before exp5).
- `--trim-artifacts` (less video evidence).
- Skipping smoke or starting while `--preflight` shows `scaffold_pending`.

## Final summary

Read `pipeline_overnight_summary.json` → list each step `status`, link child summary paths, note `learning_mode_by_arm` when present. Point user to eval MP4 paths under `backend/autonomous_control/runs/` for completed steps; run `video-frame-inspect` before verdict language ([experiment-visual-evidence](../../../rules/experiment-visual-evidence.mdc)).
