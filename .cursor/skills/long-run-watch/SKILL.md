---
name: long-run-watch
description: >-
  Passively monitor a long-running script or experiment: hourly status checks,
  append to Agents-Discussion message-queue, light-fix scoped failures (imports,
  env, lock files, resume flags). Use when the user starts a background run,
  says "watch this", "/long-run-watch", or hands off a multi-hour job to monitor.
disable-model-invocation: false
---

# Long-run watch agent

You are a **passive monitor**, not the runner. Do not start a second full run unless the user explicitly asks, the process is dead, and they approve resume.

## Your job

1. Confirm the watched process is running or has finished.
2. Every **1 hour**, report status.
3. Append the same report to [`.cursor/agents-discussion/message-queue.md`](../../agents-discussion/message-queue.md).
4. If the run **crashed**, attempt a **light fix** within the profile's allowed scope; post questions to the message queue when approval is needed.

## Pick a profile

Read the matching file under [`profiles/`](profiles/) before watching:

| Profile | When |
|---------|------|
| [`ml-algo-overnight.md`](profiles/ml-algo-overnight.md) | `ml_algo_overnight/run_overnight.py` on GPU machine |
| [`ml-modular-encoder.md`](profiles/ml-modular-encoder.md) | `ml_modular_encoder/run_modular_encoder.py` (Exp 2 SAC A0/A1) |
| [`ml-pipeline-overnight.md`](profiles/ml-pipeline-overnight.md) | `ml_pipeline_overnight/run_pipeline_overnight.py` — sequential Exp 3–6 |

No profile fits? Copy [`profiles/_template.md`](profiles/_template.md), fill it in, and watch using that profile for this session.

## Core loop (all profiles)

Repeat until **completion criteria** in the profile are met **and** no matching process is running:

1. **Process check** — use the profile's `process_check` command (Windows: `Get-CimInstance Win32_Process` + `CommandLine` match).
2. **Read state** — tail log, read status JSON / lock / error artifacts listed in the profile. For ML pipeline runs, also read `docs/experiments/pipeline/.active_run.json` and `backend/scripts/experiments/.pipeline_run.lock`.
3. **Classify status**

   | State | Criteria |
   |-------|----------|
   | `running` | process found OR lock fresh + log growing |
   | `completed` | profile completion artifact present, no process |
   | `failed` | no process, completion missing, preflight failed, or errors with no later recovery in log |
   | `unknown` | ambiguous — say what you checked |

4. **Post report** — chat **and** append to message queue (format below).
5. **Sleep 3600 s** (`Start-Sleep -Seconds 3600`), then repeat.

If `completed`, post the profile's **final summary** once and **stop** the loop.

## Agents-Discussion message-queue format

Append a block to `.cursor/agents-discussion/message-queue.md`:

```markdown
---
timestamp_utc: 2026-06-28T22:00:00Z
agent: long-run-watch
profile: <profile-id>
status: running | completed | failed | unknown
---

## Status

(one short paragraph: process yes/no, last log lines, current step/phase if known)

## Artifacts

- log: (last event)
- completion: (exists y/n)
- errors: (list paths or "none")

## Action taken

(none | light fix attempted: …)

## Errors encountered

(list each crash/ERROR; `none` only if truly none)

## Fixes applied

(file + one-line change + resume cmd; note symptom-only vs semantic fix)

## Question for user

(only if failed or fix needs approval; otherwise omit section)
```

Also paste the **Status** paragraph in chat under heading `## Agents-Discussion Message-Queue`.

## Light fixes (general rules)

**Allowed without user approval** — only inside paths listed in the profile's `light_fix_scope`:

- Remove stale lock file when no matching process exists.
- Re-run preflight / smoke command from the profile after an import or env fix.
- Resume with profile resume flags when a phase errored but later work should continue.
- Set profile `env_vars` (e.g. `KMP_DUPLICATE_LIB_OK=TRUE` on Windows OpenMP clash).

**Ask user first** — post to message queue:

- Changing experiment hyperparameters, data, or science knobs.
- Skipping preflight or gating phases.
- Any edit outside `light_fix_scope` (especially production library code).

**Never** start a duplicate full run while another matching process is active. For pipeline experiments (`experiment-knowledge-pipeline`), never start **any** other slug while `.active_run.json` shows a live holder.

**Symptom-only fixes:** If a light fix unblocks a crash but leaves wrong action semantics (e.g. vector warmup still on torque), document it as **symptom-only**, flag prior run artifacts invalid, and ask user before resume — see learnings.md `experiment-light-fix-action-space-semantics`.

## Launch (only if user asked)

Use the profile's `start_command`. Otherwise assume the user already started the run.

## Final message when complete

Follow the profile's `final_summary` section (read completion JSON, list key outcomes, point to artifact paths).

**Mandatory closeout audit** (chat + final message-queue block) — do not skip even when `status: completed`:

### Errors encountered

- List every crash, non-zero exit, or logged `ERROR` line (step id, arm, exception message).
- Include **invalid-but-unblocked** science issues (e.g. wrong action semantics) as errors, not successes.
- If none after recovery, say `none after resume` and note what failed on the first attempt.

### Fixes applied

- For each error: file(s) touched, one-line what changed, resume command (if any), and whether the fix is **symptom-only** vs **semantically correct**.
- If a fix needs user design approval before re-run, say so — do not mark the experiment valid.

### Outcomes (brief)

- Step statuses, summary JSON path, key KPIs — after the audit sections above.
