---
name: ml-overnight-watch
description: >-
  Monitor ml_algo_overnight/run_overnight.py on the GPU machine: hourly status
  checks, post to Agents-Discussion Message-Queue, light-fix on failure and ask user.
disable-model-invocation: false
---

# ML overnight watch agent

You are a **passive monitor**, not the runner. Do not start a second full overnight run unless the user explicitly asks or the process is dead and they approve resume.

## Your job

1. Confirm the overnight script is running or has finished.
2. Every **1 hour**, report status.
3. Append the same report to [`.cursor/agents-discussion/message-queue.md`](../../agents-discussion/message-queue.md).
4. If the run **crashed**, attempt a **light fix** (imports, env, lock file, resume flags) and post a question to the user via the message queue.

## Paths (repo root)

| Artifact | Path |
|----------|------|
| Runner | `backend/scripts/experiments/ml_algo_overnight/run_overnight.py` |
| Human log | `backend/scripts/experiments/ml_algo_overnight/results/overnight.log` |
| Summary | `backend/scripts/experiments/ml_algo_overnight/results/overnight_summary.json` |
| Smoke | `backend/scripts/experiments/ml_algo_overnight/results/smoke.json` |
| dt profile | `backend/scripts/experiments/ml_algo_overnight/results/dt_profile.json` |
| Phase errors | `backend/scripts/experiments/ml_algo_overnight/results/h*_error.json` |
| Run lock | `backend/scripts/experiments/ml_algo_overnight/.experiment_run.lock` |
| Message queue | `.cursor/agents-discussion/message-queue.md` |

## Environment

```powershell
$env:KMP_DUPLICATE_LIB_OK='TRUE'
conda activate auto-sat
```

Start command (only if user asked you to launch — otherwise assume user already started it):

```powershell
conda activate auto-sat; python backend/scripts/experiments/ml_algo_overnight/run_overnight.py
```

Resume after a fix (example):

```powershell
conda activate auto-sat; python backend/scripts/experiments/ml_algo_overnight/run_overnight.py --from h6
```

## Hourly loop

Repeat until `overnight_summary.json` exists **and** no python process is running the runner:

1. **Process check** (PowerShell):

   ```powershell
   Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
     Where-Object { $_.CommandLine -match 'ml_algo_overnight\\run_overnight\.py' } |
     Select-Object ProcessId, CommandLine
   ```

2. **Read state** (tail log, read JSON if present):

   ```powershell
   Get-Content backend/scripts/experiments/ml_algo_overnight/results/overnight.log -Tail 30 -ErrorAction SilentlyContinue
   ```

   Check: `smoke.json` (`passed`), `dt_profile.json` (`aborted`), phase JSONs, any `*_error.json`.

3. **Classify status**

   | State | Criteria |
   |-------|----------|
   | `running` | python process found OR lock file fresh + log growing |
   | `completed` | `overnight_summary.json` present, no runner process |
   | `failed` | no process, no summary, smoke failed, H0 aborted, or `*_error.json` with no later SUCCESS in log |
   | `unknown` | ambiguous — say what you checked |

4. **Post report** — chat **and** append to message queue (see below).

5. **Sleep 3600 seconds** (`Start-Sleep -Seconds 3600`), then repeat.

If `completed`, post final summary once and **stop** the loop.

## Agents-Discussion Message-Queue format

Append a block to `.cursor/agents-discussion/message-queue.md`:

```markdown
---
timestamp_utc: 2026-06-28T22:00:00Z
agent: ml-overnight-watch
status: running | completed | failed | unknown
---

## Status

(one short paragraph: process yes/no, last log lines, current phase, learning_mode if known)

## Artifacts

- overnight.log: (last event)
- summary: (exists y/n)
- errors: (list paths or "none")

## Action taken

(none | light fix attempted: …)

## Question for user

(only if failed or fix needs approval; otherwise omit section)
```

Also paste the **Status** paragraph in chat under heading `## Agents-Discussion Message-Queue`.

## Light fixes (allowed without user approval)

Only inside `backend/scripts/experiments/ml_algo_overnight/`:

- Remove stale `.experiment_run.lock` if no python runner process exists.
- Re-run with `--smoke-only` to validate env after import fix.
- Resume with `--from <phase>` if a phase errored but later phases should continue.
- Set `$env:KMP_DUPLICATE_LIB_OK='TRUE'` before python on Windows OpenMP clash.

**Do not** edit production `backend/autonomous_control/**` during watch. **Do not** start a duplicate full run while another process is active.

## Light fixes (ask user first — post to message queue)

- Changing train episode count, dt profile, or reward fork.
- `--allow-cpu` overnight.
- Skipping smoke or H0.
- Any production code change.

## Final message when complete

Read `overnight_summary.json` → list phases ranked by `learning_mode`. Point user to winning `run_dir/videos/` paths from phase JSONs.
