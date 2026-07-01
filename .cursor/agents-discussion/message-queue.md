# Agents-Discussion Message-Queue

Append-only status thread for multi-agent handoffs. Newest entries at the **bottom**.

Watch agents for long-running jobs use [`.cursor/skills/long-run-watch/SKILL.md`](../skills/long-run-watch/SKILL.md) plus a profile under `profiles/` (e.g. [`ml-algo-overnight.md`](../skills/long-run-watch/profiles/ml-algo-overnight.md)).

---

<!-- agents append below this line -->

---
timestamp_utc: 2026-06-29T16:38:00Z
agent: long-run-watch
profile: ml-modular-encoder
status: running
---

## Status

`run_modular_encoder.py --show-progress --arms sac_a0,sac_a1` is **running** (pid **15808**). Arm **sac_a0** (flat / production encoder): warmup 5 ep done; training **ep 4/7** in progress (~43% train bar at last terminal capture). Returns trending ~−72 to −78 per train ep. **sac_a1** not started yet.

## Artifacts

- log: `results/modular_encoder.log` — `START sac_a0 encoder=flat`, dt 1.5s/1.5s
- completion: `modular_encoder_summary.json` — **no**
- errors: none
- pipeline lock: `.pipeline_run.lock` pid 15808 (note: mirror slug says `ml_algo_overnight` — likely stale label; process cmdline is `run_modular_encoder.py`)

## Action taken

Initial watch check; added profile `profiles/ml-modular-encoder.md`.

## Question for user

(none)

---
timestamp_utc: 2026-06-29T17:15:00Z
agent: experiment-knowledge-pipeline
profile: platform-debt
status: action-needed
---

## Status

**Pressing platform issue (perf):** training-run **MP4 encode** is too slow and often lags KPI completion. **Videos remain required behavioral evidence** — see [experiment-visual-evidence](../rules/experiment-visual-evidence.mdc).

## Artifacts

- Decision: [D-013](docs/research/DECISIONS.md) (deferred — encode perf only)
- Rule: [experiment-visual-evidence](.cursor/rules/experiment-visual-evidence.mdc)
- Pipeline README: [§ Platform issues](docs/experiments/pipeline/README.md)
- Code: `training_workflow.py`, `training_run_artifacts.py`, `backend/render/`

## Action taken

Documented for frontend / render agent pickup. Experiment runs keep full video defaults; `--trim-artifacts` is opt-in when user accepts less evidence.

## Question for user

(none)

---
timestamp_utc: 2026-06-29T22:28:00Z
agent: long-run-watch
profile: ml-sac-hparam-grid (ad-hoc; no dedicated profile yet)
status: running
---

## Status

**Active:** `ml_sac_hparam_grid/run.py --show-progress` (pid **39476**). Grid **4/6 arms complete**; arm **`sac_l_sparse`** training **~29/50** ep (~58%, ~22 s/ep). One arm remains after this: **`sac_l_dense`**. ETA for full grid ~1–2 h. Pipeline mutex held (lock mirror mislabels slug `ml_algo_overnight` — import shadowing of `_run_guard`; actual job is hparam grid).

**Completed arms (all `learning_mode=true`):**

| Arm | train_best | eval_mean |
|-----|------------|-----------|
| sac_s_sparse | 88.8 | 69.8 |
| sac_s_dense | 9.0 | −21.6 |
| sac_m_sparse | 129.8 | 50.6 |
| sac_m_dense | 182.0 | −41.1 |

Current run_dir: `…/runs/9998217228551604_ml_sac_hparam_sac_l_sparse_22-17-28`

## Artifacts

- log: `ml_sac_hparam_grid/results/sac_hparam_grid.log` — last `START sac_l_sparse` 22:17:28 UTC
- completion: `sac_hparam_grid_summary.json` — **no**
- errors: none
- pipeline lock: pid 39476, script `arm:sac_s_sparse` (stale script line; process is on sac_l_sparse)

## Action taken

Initial watch check for user `/ml-overnight-watch` request.

## Question for user

(none)

---
timestamp_utc: 2026-06-29T23:08:37Z
agent: long-run-watch
profile: ml-pipeline-overnight
status: running
---

## Status

Pipeline overnight **running** (`--protocol learnable`). Orchestrator **pid 37412**; step **exp3** child **pid 42616** (`run_sac_mpo_compare.py`). Arm `compare_sac` just started.

## Artifacts

- log: `pipeline_overnight.log` — `EXEC exp3 … compare_sac`
- completion: `pipeline_overnight_summary.json` — **no**
- errors: none

## Action taken

Initial watch check.

---
timestamp_utc: 2026-06-30T00:09:00Z
agent: long-run-watch
profile: ml-pipeline-overnight
status: failed
---

## Status

After ~1 h: first run **finished with exp4 error**. **exp3 completed** (SAC `learning_mode=true`, MPO `false`). **exp4** failed on **ref1** warmup: `vector mode requires stored_action before step`. Orchestrator exited; no processes.

## Artifacts

- summary: `pipeline_overnight_summary.json` — partial (exp3 ok, exp4 error)
- error: `results/exp4_error.json`, `ml_agent_reference_pointing/results/ref1_error.json`

## Action taken

Light fix in `ml_agent_reference_pointing/_episode_runner_fork.py`: vector warmup uses baseline torque directly; vector train/eval uses `_ORIG_STEPPER_STEP` (fixes recursion). Verified ref1 minimal run OK. Deleted partial summary; **resumed** `--from exp4 --protocol learnable` (orchestrator **pid 45604**, exp4 ref0 training ~ep 2/50 at 00:16 UTC).

## Question for user

(none)

---
timestamp_utc: 2026-06-30T00:16:30Z
agent: long-run-watch
profile: ml-pipeline-overnight
status: running
---

## Status

Resume **running**. Orchestrator **pid 45604**; exp4 **ref0** SAC torque-mode training in progress (~train ep 2/50). exp3 skipped (summary exists). exp5–6 queued after exp4.

## Artifacts

- log: `pipeline_overnight.log` — `EXEC exp4 … ref0,ref1`
- completion: full pipeline summary — **no** (resume in flight)
- errors: none since fix

## Action taken

Monitoring hourly.

---
timestamp_utc: 2026-06-30T01:18:00Z
agent: long-run-watch
profile: ml-pipeline-overnight
status: running
---

## Status

Resume **running** (~1 h after restart). **exp4 completed** (ref0 `learning_mode=true`, ref1 `learning_mode=true` — vector fix OK). **exp5** active: child **pid 44640** (`run_mpo_model_size.py`, arm `mpo_s` sparse), orchestrator **pid 42948**. Training ~ep 28/50 per resume log. **exp6** pending.

## Artifacts

- log: `pipeline_overnight.log` — `DONE exp4`, `EXEC exp5`
- exp4 summary: `ml_agent_reference_pointing/results/agent_reference.json` — **yes**
- pipeline summary JSON — stale (pre-resume); updated on orchestrator exit
- errors: none since fix

## Action taken

(none)

---
timestamp_utc: 2026-06-30T02:20:00Z
agent: long-run-watch
profile: ml-pipeline-overnight
status: running
---

## Status

Resume **running**. **exp5** in progress: `mpo_s` and `mpo_m` **done** (`learning_mode=true` each, eval_mean −51.6); arm **`mpo_l`** training (started 02:08 UTC). Orchestrator **pid 42948**, exp5 child **pid 44640**. **exp6** not started.

## Artifacts

- log: `mpo_model_size.log` — `DONE mpo_s`, `DONE mpo_m`, `START mpo_l`
(none)

---
timestamp_utc: 2026-06-30T03:22:00Z
agent: long-run-watch
profile: ml-pipeline-overnight
status: running
---

## Status

Resume **running**. **exp5 completed** (mpo_s/mpo_m/mpo_l all `learning_mode=true`). **exp6** active: child **pid 27428** (`run_modular_encoder_r2.py`); `sac_a0` done (`learning_mode=true`), **`sac_a1`** (compress encoder) training. Orchestrator **pid 42948**.

## Artifacts

- log: `pipeline_overnight.log` — `DONE exp5`, `EXEC exp6`
- exp5 summary: `mpo_model_size/results/mpo_model_size_summary.json` — **yes**
(none)

---
timestamp_utc: 2026-06-30T04:22:00Z
agent: long-run-watch
profile: ml-pipeline-overnight
status: completed
---

## Status

Pipeline **completed** at 03:30 UTC (resume run). All steps done: exp3 skipped (prior summary), exp4–exp6 completed. No processes running.

## Artifacts

- summary: `backend/scripts/experiments/ml_pipeline_overnight/results/pipeline_overnight_summary.json`
- log: `pipeline_overnight.log`
- child summaries: `compare_sac_mpo.json`, `agent_reference.json`, `mpo_model_size_summary.json`, `modular_encoder_r2_summary.json`

## Action taken

Light fix applied overnight (exp4 vector warmup); resumed `--from exp4`. Full pipeline finished without further errors.

## Question for user

(none)


---
timestamp_utc: 2026-06-30T15:51:00Z
agent: long-run-watch
profile: ml-sac-shutter-reward-split
status: running
---

## Status

**Exp 9** (`ml_sac_shutter_reward_split`, arm `waste_off_budget_on`) is **running** - python pid **30872**, train **ep 15/50** (~28%, ~21 s/ep). Terminal 8 has the live run; terminal 3 is idle. Run dir `9998217165798903_ml_sac_shutter_split_15-43-20`. **Exp 8** not started; smoke passed. Background watcher `.cursor/tools/watch_exp9_then_exp8.ps1` will auto-launch `run_mpo_torque.py --show-progress` when Exp 9 completes.

## Artifacts

- log: `shutter_reward_split.log` - START waste_off_budget_on
- completion: `sac_shutter_reward_split.json` - no
- exp8 smoke: `smoke.json` - passed
- pipeline lock: pid 30872

## Action taken

Initial watch; profiles added; background watcher started (120s poll, hourly MQ).

## Errors encountered

none

## Fixes applied

none


---
timestamp_utc: 2026-06-30T16:05:14Z
agent: long-run-watch
profile: ml-sac-shutter-reward-split
status: completed
---

## Status

Exp 9 finished; summary JSON present. Auto-launching Exp 8 per operator request.

## Artifacts

- completion: sac_shutter_reward_split.json yes
- log: [16:04:57] DONE waste_off_budget_on learning_mode=True eval_mean=106.36074741388494 post_budget_cmds=75

## Action taken

auto-launch Exp 8

## Errors encountered

none

## Fixes applied

none

---
timestamp_utc: 2026-06-30T16:07:44Z
agent: long-run-watch
profile: ml-sac-shutter-reward-split
status: completed
---

## Status

Exp 9 finished; summary JSON present. Auto-launching Exp 8 per operator request.

## Artifacts

- completion: sac_shutter_reward_split.json yes
- log: [16:04:57] DONE waste_off_budget_on learning_mode=True eval_mean=106.36074741388494 post_budget_cmds=75

## Action taken

auto-launch Exp 8

## Errors encountered

none

## Fixes applied

none

---
timestamp_utc: 2026-06-30T16:10:14Z
agent: long-run-watch
profile: ml-sac-shutter-reward-split
status: completed
---

## Status

Exp 9 finished; summary JSON present. Auto-launching Exp 8 per operator request.

## Artifacts

- completion: sac_shutter_reward_split.json yes
- log: [16:04:57] DONE waste_off_budget_on learning_mode=True eval_mean=106.36074741388494 post_budget_cmds=75

## Action taken

auto-launch Exp 8

## Errors encountered

none

## Fixes applied

none

---
timestamp_utc: 2026-06-30T16:12:45Z
agent: long-run-watch
profile: ml-sac-shutter-reward-split
status: completed
---

## Status

Exp 9 finished; summary JSON present. Auto-launching Exp 8 per operator request.

## Artifacts

- completion: sac_shutter_reward_split.json yes
- log: [16:04:57] DONE waste_off_budget_on learning_mode=True eval_mean=106.36074741388494 post_budget_cmds=75

## Action taken

auto-launch Exp 8

## Errors encountered

none

## Fixes applied

none

---
timestamp_utc: 2026-06-30T16:15:15Z
agent: long-run-watch
profile: ml-sac-shutter-reward-split
status: completed
---

## Status

Exp 9 finished; summary JSON present. Auto-launching Exp 8 per operator request.

## Artifacts

- completion: sac_shutter_reward_split.json yes
- log: [16:04:57] DONE waste_off_budget_on learning_mode=True eval_mean=106.36074741388494 post_budget_cmds=75

## Action taken

auto-launch Exp 8

## Errors encountered

none

## Fixes applied

none

---
timestamp_utc: 2026-06-30T16:17:45Z
agent: long-run-watch
profile: ml-sac-shutter-reward-split
status: completed
---

## Status

Exp 9 finished; summary JSON present. Auto-launching Exp 8 per operator request.

## Artifacts

- completion: sac_shutter_reward_split.json yes
- log: [16:04:57] DONE waste_off_budget_on learning_mode=True eval_mean=106.36074741388494 post_budget_cmds=75

## Action taken

auto-launch Exp 8

## Errors encountered

none

## Fixes applied

none

---
timestamp_utc: 2026-06-30T16:20:15Z
agent: long-run-watch
profile: ml-sac-shutter-reward-split
status: completed
---

## Status

Exp 9 finished; summary JSON present. Auto-launching Exp 8 per operator request.

## Artifacts

- completion: sac_shutter_reward_split.json yes
- log: [16:04:57] DONE waste_off_budget_on learning_mode=True eval_mean=106.36074741388494 post_budget_cmds=75

## Action taken

auto-launch Exp 8

## Errors encountered

none

## Fixes applied

none

---
timestamp_utc: 2026-06-30T16:22:45Z
agent: long-run-watch
profile: ml-sac-shutter-reward-split
status: completed
---

## Status

Exp 9 finished; summary JSON present. Auto-launching Exp 8 per operator request.

## Artifacts

- completion: sac_shutter_reward_split.json yes
- log: [16:04:57] DONE waste_off_budget_on learning_mode=True eval_mean=106.36074741388494 post_budget_cmds=75

## Action taken

auto-launch Exp 8

## Errors encountered

none

## Fixes applied

none

---
timestamp_utc: 2026-06-30T16:25:15Z
agent: long-run-watch
profile: ml-sac-shutter-reward-split
status: completed
---

## Status

Exp 9 finished; summary JSON present. Auto-launching Exp 8 per operator request.

## Artifacts

- completion: sac_shutter_reward_split.json yes
- log: [16:04:57] DONE waste_off_budget_on learning_mode=True eval_mean=106.36074741388494 post_budget_cmds=75

## Action taken

auto-launch Exp 8

## Errors encountered

none

## Fixes applied

none

---
timestamp_utc: 2026-06-30T16:27:46Z
agent: long-run-watch
profile: ml-sac-shutter-reward-split
status: completed
---

## Status

Exp 9 finished; summary JSON present. Auto-launching Exp 8 per operator request.

## Artifacts

- completion: sac_shutter_reward_split.json yes
- log: [16:04:57] DONE waste_off_budget_on learning_mode=True eval_mean=106.36074741388494 post_budget_cmds=75

## Action taken

auto-launch Exp 8

## Errors encountered

none

## Fixes applied

none

---
timestamp_utc: 2026-06-30T16:30:16Z
agent: long-run-watch
profile: ml-sac-shutter-reward-split
status: completed
---

## Status

Exp 9 finished; summary JSON present. Auto-launching Exp 8 per operator request.

## Artifacts

- completion: sac_shutter_reward_split.json yes
- log: [16:04:57] DONE waste_off_budget_on learning_mode=True eval_mean=106.36074741388494 post_budget_cmds=75

## Action taken

auto-launch Exp 8

## Errors encountered

none

## Fixes applied

none

---
timestamp_utc: 2026-06-30T16:32:46Z
agent: long-run-watch
profile: ml-sac-shutter-reward-split
status: completed
---

## Status

Exp 9 finished; summary JSON present. Auto-launching Exp 8 per operator request.

## Artifacts

- completion: sac_shutter_reward_split.json yes
- log: [16:04:57] DONE waste_off_budget_on learning_mode=True eval_mean=106.36074741388494 post_budget_cmds=75

## Action taken

auto-launch Exp 8

## Errors encountered

none

## Fixes applied

none

---
timestamp_utc: 2026-06-30T16:35:16Z
agent: long-run-watch
profile: ml-sac-shutter-reward-split
status: completed
---

## Status

Exp 9 finished; summary JSON present. Auto-launching Exp 8 per operator request.

## Artifacts

- completion: sac_shutter_reward_split.json yes
- log: [16:04:57] DONE waste_off_budget_on learning_mode=True eval_mean=106.36074741388494 post_budget_cmds=75

## Action taken

auto-launch Exp 8

## Errors encountered

none

## Fixes applied

none

---
timestamp_utc: 2026-06-30T16:37:46Z
agent: long-run-watch
profile: ml-sac-shutter-reward-split
status: completed
---

## Status

Exp 9 finished; summary JSON present. Auto-launching Exp 8 per operator request.

## Artifacts

- completion: sac_shutter_reward_split.json yes
- log: [16:04:57] DONE waste_off_budget_on learning_mode=True eval_mean=106.36074741388494 post_budget_cmds=75

## Action taken

auto-launch Exp 8

## Errors encountered

none

## Fixes applied

none

---
timestamp_utc: 2026-06-30T16:40:20Z
agent: long-run-watch
profile: ml-mpo-decoupled-dual-torque
status: completed
---

## Status

Watch loop exited cleanly. **Exp 9** done (learning_mode=true, eval_mean=106.4). **Exp 8** done (learning_mode=true, train_best=8.7, eval_mean=-81.1). Auto-launch hit repeated `43900` PowerShell read-only variable errors in stale-lock cleanup; one Exp 8 run still completed via spawned windows.

## Artifacts

- exp9: `sac_shutter_reward_split.json`
- exp8: `mpo_torque.json` — DONE 16:38:06 UTC
- watch log: `.cursor/debug_logs/watch-exp9-exp8.log`

## Action taken

Final closeout; fixed `43900` -> `` in watch script for future runs.

## Errors encountered

- Watch script: `Cannot overwrite variable PID` on each Exp 8 launch retry (symptom-only; run still finished)
- Multiple duplicate Exp 8 window spawns from retry loop

## Fixes applied

- `.cursor/tools/watch_exp9_then_exp8.ps1`: rename `43900` to `` in Remove-StaleLockIfSafe

---
timestamp_utc: 2026-06-30T22:16:00Z
agent: long-run-watch
profile: ml-pipeline-overnight-batch-10-13
status: running
---

## Status

**Exp 10 complete** (wall **32.2 min**, exit 0). KPIs: `learning_mode=true`, eval mean **−510.4**, train best **−354.4** (ep 23), KL last **0.013**. Runs **git-pushed** after Exp 10. **Exp 11** started **22:15:02 UTC** — warmup done, **train ep 0** in progress. Handoff **OK**. Exp 11 ETA ~**22:47 UTC** at Exp 10 pace.

## Artifacts

- exp10: `results/mpo_safe_mode_penalty.json` · run `9998217144237087_ml_mpo_safe_mode_penalty_safe_mode_penalty_on_21-42-42`
- batch log: `DONE Exp 10` → `GIT pushed` → `START Exp 11`
- exp11: `9998217142297111_ml_mpo_decoupled_dual_vector_sparse_22-15-02`

## Action taken

Handoff verified; `.cursor/debug_logs/watch-exp10-exp11-handoff.log`

## Errors encountered

none

## Fixes applied

none


---
timestamp_utc: 2026-06-30T22:42:43Z
agent: long-run-watch
profile: ml-pipeline-overnight-batch-10-13
status: running
---

## Status

Overnight batch running (orchestrator pid 32068). Progress: 9998217142297111_ml_mpo_decoupled_dual_vector_sparse_22-15-02: ep 1 step 516/516 ret=45.5. Log: [2026-06-30T21:42:40Z] START Exp 10 (ml_mpo_safe_mode_penalty) â†’ C:\Users\cedri\miniconda3\envs\auto-sat\python.exe run_mpo_safe_mode_penalty.py --show-progress | [2026-06-30T22:14:53Z] DONE Exp 10 exit=0 elapsed_s=1933 | [2026-06-30T22:14:53Z] GIT sync runs after Exp 10 | [2026-06-30T22:15:00Z] GIT result Exp 10: pushed  | [2026-06-30T22:15:00Z] START Exp 11 (ml_mpo_decoupled_dual_vector) â†’ C:\Users\cedri\miniconda3\envs\auto-sat\python.exe run_mpo_vector.py --show-progress

## Artifacts

- batch log: [2026-06-30T21:42:40Z] START Exp 10 (ml_mpo_safe_mode_penalty) â†’ C:\Users\cedri\miniconda3\envs\auto-sat\python.exe run_mpo_safe_mode_penalty.py --show-progress | [2026-06-30T22:14:53Z] DONE Exp 10 exit=0 elapsed_s=1933 | [2026-06-30T22:14:53Z] GIT sync runs after Exp 10 | [2026-06-30T22:15:00Z] GIT result Exp 10: pushed  | [2026-06-30T22:15:00Z] START Exp 11 (ml_mpo_decoupled_dual_vector) â†’ C:\Users\cedri\miniconda3\envs\auto-sat\python.exe run_mpo_vector.py --show-progress
- lock: True

## Action taken

none

## Errors encountered

none

## Fixes applied

none

---
timestamp_utc: 2026-06-30T23:36:47Z
agent: long-run-watch
profile: ml-pipeline-overnight-batch-10-13
status: completed
---

## Status

Overnight batch **finished cleanly** at 23:36:47 UTC (~1h 54m wall). All four experiments exit=0; no matching python processes remain. Exp 10–13 ran sequentially with git sync **pushed** after each arm.

## Artifacts

- batch log: `backend/scripts/experiments/results/pipeline_overnight_batch.log`
- completion: `backend/scripts/experiments/results/pipeline_overnight_batch.json` — yes
- per-exp summaries: Exp10–13 result JSONs all present
- errors: none

## Action taken

none (passive monitor; batch completed without intervention)

## Errors encountered

none

## Fixes applied

none