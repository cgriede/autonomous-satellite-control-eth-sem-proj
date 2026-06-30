# Profile: <short-id>

**Profile id:** `<short-id>`

## Environment

```powershell
conda activate <env-name>
# optional: $env:VAR='value'
```

## Paths (repo root)

| Artifact | Path |
|----------|------|
| Runner | `<path/to/script.py>` |
| Human log | `<path/to/run.log>` |
| Summary (completion) | `<path/to/completion.json or marker>` |
| Run lock | `<optional lock file>` |
| Message queue | `.cursor/agents-discussion/message-queue.md` |

## Process check

```powershell
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.CommandLine -match '<regex-escaped runner path fragment>' } |
  Select-Object ProcessId, CommandLine
```

## Read state

```powershell
Get-Content <log-path> -Tail 30 -ErrorAction SilentlyContinue
```

List JSON / error artifacts to inspect.

## Completion criteria

Describe when the watch loop should stop (e.g. summary file exists, exit code 0 in log, no process).

## Start command

```powershell
conda activate <env>; python <runner>
```

## Resume / preflight

Optional smoke or `--from` / `--resume` commands.

## Light-fix scope

Directories where you may fix imports, locks, env, resume flags without asking.

## Ask user first

Science knobs, skipping gates, edits outside light-fix scope.

## Final summary

What to read and report when complete.
