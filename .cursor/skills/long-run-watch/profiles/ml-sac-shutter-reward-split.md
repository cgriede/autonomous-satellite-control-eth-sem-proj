# Profile: ml-sac-shutter-reward-split

**Profile id:** `ml-sac-shutter-reward-split`

Pipeline **Exp 9** — `ml_sac_shutter_reward_split` (SAC vector, waste_off_budget_on).

## Environment

```powershell
$env:KMP_DUPLICATE_LIB_OK='TRUE'
conda activate auto-sat
```

## Paths (repo root)

| Artifact | Path |
|----------|------|
| Runner | `backend/scripts/experiments/ml_sac_shutter_reward_split/run_sac_shutter_reward_split.py` |
| Human log | `backend/scripts/experiments/ml_sac_shutter_reward_split/results/shutter_reward_split.log` |
| Summary (completion) | `backend/scripts/experiments/ml_sac_shutter_reward_split/results/sac_shutter_reward_split.json` |
| Error artifact | `backend/scripts/experiments/ml_sac_shutter_reward_split/results/waste_off_error.json` |
| Pipeline lock | `backend/scripts/experiments/.pipeline_run.lock` |
| Active run mirror | `docs/experiments/pipeline/.active_run.json` |
| Run dir (current) | `backend/autonomous_control/runs/9998217165798903_ml_sac_shutter_split_15-43-20` |
| Message queue | `.cursor/agents-discussion/message-queue.md` |

## Process check

```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match 'ml_sac_shutter_reward_split\\run_sac_shutter_reward_split\.py' } |
  Select-Object ProcessId, CommandLine
```

## Read state

```powershell
Get-Content backend/scripts/experiments/ml_sac_shutter_reward_split/results/shutter_reward_split.log -Tail 20
Get-Content backend/autonomous_control/runs/9998217165798903_ml_sac_shutter_split_15-43-20/telemetry/current_step.json
Get-Content backend/autonomous_control/runs/9998217165798903_ml_sac_shutter_split_15-43-20/run_log.md -Tail 15
```

## Completion criteria

`sac_shutter_reward_split.json` exists **and** no matching python process.

## Start command

```powershell
conda activate auto-sat
cd D:\code\sem-proj-asc\backend\scripts\experiments\ml_sac_shutter_reward_split
python run_sac_shutter_reward_split.py --show-progress
```

## Resume

No checkpoint resume — if crashed mid-run, re-run full command (warmup cache should speed restart).

## Light-fix scope

`backend/scripts/experiments/ml_sac_shutter_reward_split/` only:

- Stale `.pipeline_run.lock` when no matching process.
- `KMP_DUPLICATE_LIB_OK=TRUE` on Windows.
- Re-run after import/env fix.

## Ask user first

- `--trim-artifacts`, `--train-episodes` changes.
- Starting Exp 8 while Exp 9 still holds lock.

## Final summary

Read `sac_shutter_reward_split.json` → `learning_mode`, `eval_return_mean`, `post_budget_shutter_cmds_total`, `run_dir`. Compare to Exp 7 baseline in JSON. Point to eval MP4s under run_dir.
