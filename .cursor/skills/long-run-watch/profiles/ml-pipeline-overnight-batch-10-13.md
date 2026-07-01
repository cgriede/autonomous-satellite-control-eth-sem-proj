# Profile: ml-pipeline-overnight-batch-10-13

**Profile id:** `ml-pipeline-overnight-batch-10-13`

Sequential orchestrator for pipeline **Exp 10–13** (`run_pipeline_overnight_batch.py`).

## Environment

```powershell
$env:KMP_DUPLICATE_LIB_OK='TRUE'
conda activate auto-sat
```

## Paths (repo root)

| Artifact | Path |
|----------|------|
| Orchestrator | `backend/scripts/experiments/run_pipeline_overnight_batch.py` |
| Batch log | `backend/scripts/experiments/results/pipeline_overnight_batch.log` |
| Summary (completion) | `backend/scripts/experiments/results/pipeline_overnight_batch.json` |
| Git sync helper | `backend/scripts/experiments/_git_sync_runs.py` |
| Pipeline lock | `backend/scripts/experiments/.pipeline_run.lock` |
| Active run mirror | `docs/experiments/pipeline/.active_run.json` |
| Runs output | `backend/autonomous_control/runs/` |
| Message queue | `.cursor/agents-discussion/message-queue.md` |
| Watch script | `.cursor/tools/watch_pipeline_overnight_batch.ps1` |

### Per-step logs / completion

| Step | Slug | Log | Completion JSON |
|------|------|-----|-----------------|
| Exp 10 | `ml_mpo_safe_mode_penalty` | `.../results/mpo_safe_mode_penalty.log` | `.../results/mpo_safe_mode_penalty.json` |
| Exp 11 | `ml_mpo_decoupled_dual_vector` | `.../results/mpo_vector.log` | `.../results/mpo_vector.json` |
| Exp 12 | `ml_mpo_vector_torque_effort` | `.../results/mpo_vector_torque_effort.log` | `.../results/mpo_vector_torque_effort.json` |
| Exp 13 | `ml_mpo_learn_cadence_hparams` | `.../results/learn_cadence_hparams.log` | `.../results/learn_cadence_overnight.json` (or `learn_cadence_hparams_summary.json`) |

Exp 13 preflight: `results/smoke.json` must exist unless batch launched with `--skip-not-ready`.

## Process check

```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match 'run_pipeline_overnight_batch\.py' } |
  Select-Object ProcessId, CommandLine
```

Child slugs (only one at a time):

```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object {
    $_.CommandLine -match 'ml_mpo_safe_mode_penalty|ml_mpo_decoupled_dual_vector|ml_mpo_vector_torque_effort|ml_mpo_learn_cadence_hparams'
  } |
  Select-Object ProcessId, CommandLine
```

## Read state

```powershell
Get-Content backend/scripts/experiments/results/pipeline_overnight_batch.log -Tail 40
Get-Content backend/scripts/experiments/results/pipeline_overnight_batch.json -ErrorAction SilentlyContinue
```

Tail active child log + `telemetry/current_step.json` under latest matching `backend/autonomous_control/runs/*` folder.

## Completion criteria

`pipeline_overnight_batch.json` exists **and** no orchestrator process.  
All **executed** steps show `status: ok` or intentional `skipped` (Exp 13 if smoke missing at launch).

## Start command

```powershell
conda activate auto-sat
cd D:\code\sem-proj-asc\backend\scripts\experiments
python run_pipeline_overnight_batch.py --show-progress --git-sync-runs --skip-not-ready --continue-on-error
```

Preflight:

```powershell
python run_pipeline_overnight_batch.py --smoke-only
```

## Resume

```powershell
python run_pipeline_overnight_batch.py --from-slug ml_mpo_decoupled_dual_vector --show-progress --git-sync-runs --skip-not-ready --continue-on-error
```

## Light-fix scope

- `backend/scripts/experiments/run_pipeline_overnight_batch.py`
- `backend/scripts/experiments/_git_sync_runs.py`
- Child slug folders Exp 10–13 only
- Stale `.pipeline_run.lock` when no matching process
- `KMP_DUPLICATE_LIB_OK=TRUE`

**Do not** edit production `autonomous_control/` / `simulation/` / `render/` during watch.

## Ask user first

- Skipping `--git-sync-runs` / changing commit scope
- Running Exp 13 without smoke (`--skip-not-ready` vs wait)
- Hyperparam / cadence knob changes mid-run
- `--trim-artifacts` on Exp 10–12 (less video evidence)

## Final summary

Read `pipeline_overnight_batch.json` → per-slug `status`, `elapsed_s`, `git_sync`.  
Link each child summary JSON + canonical `run_dir` from KPI files.  
Note Exp 13 overnight = Track A0 + A1 parity only (B0 hparam screen deferred).  
Cite eval/train MP4 paths under `backend/autonomous_control/runs/` for behavioral claims.
