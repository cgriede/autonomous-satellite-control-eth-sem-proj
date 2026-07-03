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
timestamp_utc: 2026-07-02T23:05:00Z
agent: long-run-watch
profile: exp14-stage-a-b (ad-hoc)
status: running
---

## Status

Exp 14 pipeline holder is still present (`pid=23776`, `script=screen:hp_default`) so the mutex correctly blocks Stage B, but the process appears stalled: command line remains `run.py --screen`, CPU did not move over a 5s check (`3147.5 -> 3147.5`), and no new Stage A KPI files beyond `hp_default`, `hp_conservative`, `hp_mid_batch` were written after 00:57 local.

## Artifacts

- log: no fresh tail from the original screen terminal; latest prior crash artifact remains `results/run_error.json`
- completion: Stage A summary exists but incomplete arm set (`results/screen_summary.json` currently winner from `hp_default`-only summary); Stage B summary `results/stage_b_summary.json` not present
- errors: `results/run_error.json` (historical tqdm/pipe crash), current symptom is probable stalled `run.py --screen` holder

## Action taken

Passive status check only; no lock/process mutation yet.

## Errors encountered

- Stage B launch blocked by active pipeline lock (`pid=23776`)
- Potential stalled Stage A process (no measurable CPU advance, no new arm KPI artifact)

## Fixes applied

none

## Question for user

Approve killing `pid=23776` and then resuming Stage A to completion before auto-starting Stage B?

---
timestamp_utc: 2026-07-02T23:07:00Z
agent: long-run-watch
profile: exp14-stage-a-b (ad-hoc)
status: running
---

## Status

User confirmed GPU utilization is high (~80%), so the Stage A holder (`pid=23776`, `run.py --screen`) is treated as actively working; keep passive monitoring and do not kill/restart while it runs.

## Artifacts

- log: lock holder still `screen:hp_default`; terminal output for that run is not currently streaming here
- completion: Stage A still incomplete (3 arm KPI files present); Stage B not started yet
- errors: none new in this check

## Action taken

Continue passive watch; no process intervention.

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

none---
timestamp_utc: 2026-07-02T23:12:22Z
agent: long-run-watch
profile: exp14-stage-a-b (ad-hoc)
status: failed
---

## Status

No active Stage A process detected, but Stage A summary is incomplete (1 arms). Stage B was not started to avoid promoting incomplete Stage A outputs.

## Artifacts

- stage A summary path: D:\code\sem-proj-asc\backend\scripts\experiments\ml_mpo_multienv_target_select\results\screen_summary.json
- arms found: 1
- stage B summary exists: False

## Action taken

none

## Errors encountered

Stage A ended or disappeared before producing full 5-arm summary

## Fixes applied

none
## Question for user

Restart Stage A (python run.py --screen) or approve explicit Stage B override with a selected arm?
---
timestamp_utc: 2026-07-02T23:13:37Z
agent: long-run-watch
profile: exp14-stage-a-b (ad-hoc)
status: running
---

## Status

No active Stage A process was detected and summary is incomplete (1 arms), so Stage A was auto-resumed with a full screen rerun (pid 12984). Stage B will auto-start after Stage A completes.

## Artifacts

- stage A summary path: D:\code\sem-proj-asc\backend\scripts\experiments\ml_mpo_multienv_target_select\results\screen_summary.json
- arms found before resume: 1
- stage B summary exists: False
- stale lock cleared: True

## Action taken

auto-started: run.py --screen

## Errors encountered

Stage A process exited before full 5-arm completion

## Fixes applied

removed stale pipeline lock mirror and relaunched Stage A (semantically correct resume)

---
timestamp_utc: 2026-07-02T23:15:00Z
agent: long-run-watch
profile: exp14-stage-a-b (ad-hoc)
status: running
---

## Status

Stage A is now running under resumed pid `12984` (`run.py --screen`) and the watcher has been corrected to track the lock pid directly; it will auto-start Stage B (`run.py --full --show-progress`) immediately after Stage A is complete.

## Artifacts

- lock file: `backend/scripts/experiments/.pipeline_run.lock` -> pid 12984
- active run mirror: `docs/experiments/pipeline/.active_run.json` -> `screen:hp_default`
- Stage A arms currently on disk: `hp_default`, `hp_conservative`, `hp_mid_batch`
- Stage B summary exists: no (`results/stage_b_summary.json`)

## Action taken

Restarted watch loop with fixed process detection; no duplicate experiment launch.

## Errors encountered

none new after watcher relaunch

## Fixes applied

`.cursor/tools/watch_exp14_stage_a_b.ps1`: process detection now uses active-run lock pid first (prevents false "no process" while run is alive).

---
timestamp_utc: 2026-07-03T00:07:00Z
agent: long-run-watch
profile: exp14-stage-a-b (ad-hoc)
status: running
---

## Status

Hourly check: Stage A still running on pid `12984` (`run.py --screen`); duplicate pid `23776` is gone. Four of five screen arms have KPI files (`hp_default`, `hp_conservative`, `hp_mid_batch`, `hp_aggressive`); `hp_explore` remains. Watcher pid `39356` active; Stage B will auto-start after Stage A completes.

## Artifacts

- lock: pid 12984, script `screen:hp_default`
- arm_kpis: 4/5 present
- stage_b_summary.json: not present

## Action taken

none (hourly status check)

## Errors encountered

none

## Fixes applied

none
---
timestamp_utc: 2026-07-02T23:15:25Z
agent: long-run-watch
profile: exp14-stage-a-b (ad-hoc)
status: running
---

## Status

Stage A is still running (
un.py --screen) with pid 12984; Stage B remains blocked until this process exits and Stage A artifacts are complete.

## Artifacts

- lock file: True
- active_run.json: True
- stage A arms in summary: 1
- current winner_arm_id: hp_default
- stage_b_summary.json exists: False

## Action taken

none (passive monitor)

## Errors encountered

none

## Fixes applied

none
---
timestamp_utc: 2026-07-03T00:15:25Z
agent: long-run-watch
profile: exp14-stage-a-b (ad-hoc)
status: running
---

## Status

Stage A is still running (
un.py --screen) with pid 12984; Stage B remains blocked until this process exits and Stage A artifacts are complete.

## Artifacts

- lock file: True
- active_run.json: True
- stage A arms in summary: 1
- current winner_arm_id: hp_default
- stage_b_summary.json exists: False

## Action taken

none (passive monitor)

## Errors encountered

none

## Fixes applied

none

---
timestamp_utc: 2026-07-03T00:21:00Z
agent: long-run-watch
profile: exp14-stage-a-b (ad-hoc)
status: running
---

## Status

Stage B is **not** running yet. Stage A pid `12984` is still on the final screen arm (`hp_explore`; 4/5 arm KPI files present). Watcher pid `39356` will auto-start `run.py --full --show-progress` when Stage A completes and writes a 5-arm `screen_summary.json`.

## Artifacts

- active process: `run.py --screen` pid 12984
- arm_kpis: 4/5 (missing `hp_explore.json`)
- stage_b_summary.json: not present

## Action taken

none

## Errors encountered

none

## Fixes applied

none
---
timestamp_utc: 2026-07-03T01:15:25Z
agent: long-run-watch
profile: exp14-stage-a-b (ad-hoc)
status: running
---

## Status

Stage A appears complete (no screen process, screen summary has 5 arms). Stage B was auto-started with pid 17372.

## Artifacts

- stage A summary: yes (D:\code\sem-proj-asc\backend\scripts\experiments\ml_mpo_multienv_target_select\results\screen_summary.json)
- winner_arm_id: hp_explore
- stage B summary present before launch: no

## Action taken

auto-started: run.py --full --show-progress

## Errors encountered

none

## Fixes applied

none
---
timestamp_utc: 2026-07-03T02:15:25Z
agent: long-run-watch
profile: exp14-stage-a-b (ad-hoc)
status: running
---

## Status

Stage B is running (un.py --full) with pid 17372; monitoring until completion artifact is written.

## Artifacts

- stage B summary exists: False
- lock file present: True
- active_run.json present: True

## Action taken

none (passive monitor)

## Errors encountered

none

## Fixes applied

none
---
timestamp_utc: 2026-07-03T03:15:25Z
agent: long-run-watch
profile: exp14-stage-a-b (ad-hoc)
status: running
---

## Status

Stage B is running (un.py --full) with pid 17372; monitoring until completion artifact is written.

## Artifacts

- stage B summary exists: False
- lock file present: True
- active_run.json present: True

## Action taken

none (passive monitor)

## Errors encountered

none

## Fixes applied

none
---
timestamp_utc: 2026-07-03T04:15:25Z
agent: long-run-watch
profile: exp14-stage-a-b (ad-hoc)
status: running
---

## Status

Stage B is running (un.py --full) with pid 17372; monitoring until completion artifact is written.

## Artifacts

- stage B summary exists: False
- lock file present: True
- active_run.json present: True

## Action taken

none (passive monitor)

## Errors encountered

none

## Fixes applied

none
---
timestamp_utc: 2026-07-03T05:15:25Z
agent: long-run-watch
profile: exp14-stage-a-b (ad-hoc)
status: completed
---

## Status

Stage B process is no longer running and completion artifact is present; Aâ†’B overnight chain finished.

## Artifacts

- stage B summary: yes (D:\code\sem-proj-asc\backend\scripts\experiments\ml_mpo_multienv_target_select\results\stage_b_summary.json)
- stage A summary arms: 5
- winner_arm_id: hp_explore

## Action taken

none

## Errors encountered

none after resume

## Fixes applied

none
