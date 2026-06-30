# Profile: ml-algo-overnight

**Profile id:** `ml-algo-overnight`

## Environment

```powershell
$env:KMP_DUPLICATE_LIB_OK='TRUE'
conda activate auto-sat
```

## Paths (repo root)

| Artifact | Path |
|----------|------|
| Runner | `backend/scripts/experiments/ml_algo_overnight/run_overnight.py` |
| Human log | `backend/scripts/experiments/ml_algo_overnight/results/overnight.log` |
| Summary (completion) | `backend/scripts/experiments/ml_algo_overnight/results/overnight_summary.json` |
| Smoke | `backend/scripts/experiments/ml_algo_overnight/results/smoke.json` |
| dt profile | `backend/scripts/experiments/ml_algo_overnight/results/dt_profile.json` |
| Phase errors | `backend/scripts/experiments/ml_algo_overnight/results/h*_error.json` |
| Run lock | `backend/scripts/experiments/ml_algo_overnight/.experiment_run.lock` |
| Message queue | `.cursor/agents-discussion/message-queue.md` |

## Process check

```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match 'ml_algo_overnight\\run_overnight\.py' } |
  Select-Object ProcessId, CommandLine
```

## Read state

```powershell
Get-Content backend/scripts/experiments/ml_algo_overnight/results/overnight.log -Tail 30 -ErrorAction SilentlyContinue
```

Check: `smoke.json` (`passed`), `dt_profile.json` (`aborted`), phase JSONs (`h1a_mpo_sparse.json`, etc.), any `*_error.json` (may be stale if a later log line shows SUCCESS for that phase).

## Completion criteria

`overnight_summary.json` exists **and** no runner process (above).

## Start command

(only if user asked you to launch)

```powershell
conda activate auto-sat; python backend/scripts/experiments/ml_algo_overnight/run_overnight.py
```

## Resume / preflight

```powershell
# After import/env fix
python -m run_overnight --smoke-only

# Resume from phase (example)
python -m run_overnight --from h6
```

Run from `backend/scripts/experiments/ml_algo_overnight/`.

## Light-fix scope

Only inside `backend/scripts/experiments/ml_algo_overnight/`:

- Stale `.experiment_run.lock` when no process.
- `--smoke-only` after import fix.
- `--from <phase>` when a phase errored but later phases should continue.
- `KMP_DUPLICATE_LIB_OK=TRUE` before python on Windows.

**Do not** edit `backend/autonomous_control/**` during watch without user approval.

## Ask user first

- Train episode count, dt profile, or reward fork changes.
- `--allow-cpu` overnight.
- Skipping smoke or H0.
- Any production code change.

## Final summary

Read `overnight_summary.json` → list phases ranked by `learning_mode`. Point user to winning `run_dir/videos/` paths from phase JSONs (`h4_sac.json`, `h1a_mpo_sparse.json`, etc.).
