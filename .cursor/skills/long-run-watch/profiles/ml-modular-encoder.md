# Profile: ml-modular-encoder

**Profile id:** `ml-modular-encoder`

## Environment

```powershell
$env:KMP_DUPLICATE_LIB_OK='TRUE'
conda activate auto-sat
```

## Paths (repo root)

| Artifact | Path |
|----------|------|
| Runner | `backend/scripts/experiments/ml_modular_encoder/run_modular_encoder.py` |
| Log | `backend/scripts/experiments/ml_modular_encoder/results/modular_encoder.log` |
| Summary (completion) | `backend/scripts/experiments/ml_modular_encoder/results/modular_encoder_summary.json` |
| Smoke | `backend/scripts/experiments/ml_modular_encoder/results/smoke.json` |
| dt profile | `backend/scripts/experiments/ml_modular_encoder/results/dt_profile.json` |
| Arm errors | `backend/scripts/experiments/ml_modular_encoder/results/sac_a*_error.json` |
| Pipeline lock | `backend/scripts/experiments/.pipeline_run.lock` |
| Active run mirror | `docs/experiments/pipeline/.active_run.json` |
| Message queue | `.cursor/agents-discussion/message-queue.md` |

## Process check

```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match 'run_modular_encoder\.py' } |
  Select-Object ProcessId, CommandLine
```

## Read state

```powershell
Get-Content backend/scripts/experiments/ml_modular_encoder/results/modular_encoder.log -Tail 20 -ErrorAction SilentlyContinue
```

Terminal: user-launched session (e.g. Cursor terminal running `run_modular_encoder.py --show-progress`).

Check: `modular_encoder_summary.json` (completion), `*_error.json`, pipeline lock + `.active_run.json`.

## Completion criteria

`modular_encoder_summary.json` exists **and** no `run_modular_encoder.py` process.

## Start command

(only if user asked you to launch)

```powershell
conda activate auto-sat
cd D:\code\sem-proj-asc\backend\scripts\experiments\ml_modular_encoder
python .\run_modular_encoder.py --show-progress --arms sac_a0,sac_a1
```

## Resume / preflight

```powershell
cd backend/scripts/experiments/ml_modular_encoder
python .\run_modular_encoder.py --smoke --allow-cpu
# Single arm after partial run:
python .\run_modular_encoder.py --show-progress --arms sac_a1
```

## Light-fix scope

Only inside `backend/scripts/experiments/ml_modular_encoder/`:

- Stale `backend/scripts/experiments/.pipeline_run.lock` when no matching process.
- `--smoke` after import/env fix in experiment folder.
- `KMP_DUPLICATE_LIB_OK=TRUE` on Windows.

**Do not** edit production `backend/autonomous_control/**` during watch without user approval.

## Ask user first

- Arm list, `vector_embed_dim`, train episode count.
- Starting a second pipeline slug while lock is held.
- Any production code change.

## Final summary

Read `modular_encoder_summary.json` → per-arm `learning_mode`, verdict, `wall_s`. Point to `run_dir` paths and `videos/` if exported. Remind user to `/document-experiment-step` Phase 2 when complete.
