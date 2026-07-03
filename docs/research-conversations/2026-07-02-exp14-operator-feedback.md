# Exp 14 — operator feedback (bugs & miscommunications)

**Date:** 2026-07-02  
**Experiment:** `ml_mpo_multienv_target_select` (Exp 14)  
**Session focus:** reward landscape, hparam screen, checkpoint resume, console output  
**Related:** [pipeline Phase 2 doc](../experiments/pipeline/2-run/14-mpo-multienv-target-select.md), [Phase 1 build Q&A](./2026-07-02-exp14-phase1-build-action-space.md)

---

## Summary

Operator ran warmup previews and attempted the 5-arm hparam screen while clarifying reward design, grid axes, and training continuation. Several gaps between **documented protocol**, **agent explanations**, and **actual code** caused confusion. Some issues were fixed in-session; others remain open.

---

## Bugs (code / runtime)

| ID | Severity | Symptom | Root cause | Status |
|----|----------|---------|------------|--------|
| **B-01** | High | Pipeline doc and agent described shaped reward `α·score_gain + β·… − ε·torque`; only torque (`ε=0.01`) is wired | `_exp14_reward_fork.py` defines `ALPHA`–`DELTA` but `_patched_compute_reward` always calls canonical `compute_reward` with toggles; shaping terms never implemented | **Open** — doc/agent overstated implementation |
| **B-02** | Medium | `set_reward_credit_mode("sparse")` appears to do nothing observable | `reward_credit_mode()` is never read outside tests; sparse behavior comes from `RewardKernel` setting `picture_taken=False` on non-shutter steps | **Open** — dead API / misleading name |
| **B-03** | High | `--full` originally rebuilt a fresh agent; screen’s 20 train episodes were lost | No checkpoint save/load existed before this session | **Fixed** — `_exp14_checkpoints.py`, save per screen arm, resume on `--full` |
| **B-04** | Medium | `stage_b_summary.json` `best_checkpoint` was eval score metadata, not model weights | Naming implied a loadable checkpoint | **Fixed** — real `.pt` checkpoints + `checkpoint_path` in summaries |
| **B-05** | High | Screen run crashed with `OSError: [Errno 22] Invalid argument` in tqdm | Background command piped stdout through PowerShell `Tee-Object`; tqdm/Rich break on non-TTY handles | **Partial** — see B-06; avoid piping |
| **B-06** | Medium | Simulation info panel showed `ΓöîΓöÇ…` instead of `╭─` box drawing | UTF-8 Rich panels through a pipe / wrong console code page | **Fixed** — `simulation_info.py` falls back to plain ASCII when not a UTF-8 TTY |
| **B-07** | Low | `warmup_preview.json` did not record which reward fork was active | `reward_mode` not written to preview payload | **Fixed** — `reward_mode` added to preview JSON |
| **B-08** | Low | Screen arm table in pipeline doc lists only MPO axes (LR, batch, entropy) | Reward shaping not in original 5-arm design | **Partial** — code updated (`hp_conservative` / `hp_explore`); pipeline doc not updated |

---

## Miscommunications (doc ↔ code ↔ operator expectations)

### M-01 — “Reward landscape” vs mission score

**What operator heard:** Two related but distinct quantities were not always separated clearly.

| Quantity | Formula (current code) | Typical warmup scale |
|----------|------------------------|----------------------|
| **Mission score** (verdict KPI) | `Σ (quality × coverage)` at budget-eligible shutters, `k=1` | ~3.8 / ep |
| **RL return** (training signal) | Sparse `+100 × cov × qual × (1−cloud)` at shutters + tiny torque + budget penalty | ~415 / ep |

**Gap:** Stating “optimize mission score” while MPO actually maximizes return at ~100× scale invites false confidence that return trends track EO performance (H14c).

**Recommendation:** Always pair return and `mission_score` in operator-facing summaries; note `k_capture=100` vs score `k=1`.

---

### M-02 — Designed reward shaping presented as implemented

**Pipeline doc (Phase 0):**

```text
reward = α·score_gain + β·successful_capture_bonus − γ·missed_opportunity − δ·instability − ε·torque_penalty
```

**Actual fork:** capture credit + optional torque + optional budget-exhausted penalty only.

**Operator impact:** Asked whether gridsearch included “score-like” reward (torque off). Answer required code inspection; should have been visible in arm table and README.

---

### M-03 — Hparam grid did not include reward variants (until requested)

**Expectation:** At least one screen arm with torque off / capture-only to test score-aligned training.

**Reality (initial build):** All 5 arms shared `exp14_sparse` with `ε=0.01` torque.

**After fix:**

| Arm | Reward mode |
|-----|-------------|
| `hp_default`, `hp_mid_batch`, `hp_aggressive` | `exp14_sparse` |
| `hp_conservative` | `exp14_sparse_no_torque` |
| `hp_explore` | `exp14_capture_only` |

**Remaining gap:** Even `exp14_capture_only` is not identical to mission score (`k=100`, no budget penalty in capture-only mode).

---

### M-04 — “Torque off should change warmup return a lot”

**Operator observation:** `hp_conservative` warmup return ≈ 415 vs `hp_default` ≈ 414.

**Explanation missed upfront:** Warmup uses the **scripted baseline**, not the learned policy. Torque penalty is ~`-0.01 × (τ/τ_max)²` per step → **~1 point** over the episode vs **~400** from capture spikes. Mission score is identical.

**Lesson:** Reward-mode comparisons on warmup preview only validate fork wiring, not learning behavior.

---

### M-05 — Screen winner vs final verdict metric

**Pipeline doc inconsistency:**

- Stage A winner: **train return at ep 20** (tie-break eval return, entropy) — line 203  
- Checkpoint / verdict: **best eval `score_mean`** — lines 159, 205  

**Operator impact:** Best screen arm by return may not be best by mission score; Stage B continues that arm’s weights regardless.

**Recommendation:** Log both rankings in `screen_summary.json`; document explicitly that Stage A optimizes learning plumbing, Stage B/verdict optimizes score.

---

### M-06 — “Continue training” vs curriculum semantics

**Operator request:** After screen, continue the winner — “20 episodes are 20 episodes” (don’t retrain from scratch).

**Clarification needed (was not stated early):**

- **Weights** carry forward (now via `screen_final.pt` → `--full`).  
- **Stage B** still runs 10 **new** env draws × (5 warmup + 30 train); screen fixed env `(mission_seed=7, cloud_seed=7)` ≠ train env 0.  
- Episode counters in summary: `screen_train_episodes_completed` + `stage_b_train_episodes_completed` = `total_train_episodes_completed`.

**Not the same as:** skipping Stage B warmup or treating screen env as env 0 of the curriculum.

---

### M-07 — Console / progress display

**Operator report:** Direct `python run.py --export-warmup-preview` showed correct Rich panels; piped/background screen showed mojibake and tqdm crashes.

**Cause:** Agent suggested `2>&1 | Tee-Object` for logging. PowerShell pipe ≠ interactive UTF-8 terminal.

**Operator guidance:**

```powershell
# Good — interactive terminal
python run.py --screen --show-progress

# Bad — breaks tqdm/Rich on Windows
python run.py --screen --show-progress 2>&1 | Tee-Object -FilePath results\screen_run.log
```

Durable KPIs: `results/arm_kpis/*.json`, `results/screen_summary.json`, `results/checkpoints/`.

---

### M-08 — Agent background run aborted

Screen was started in a background shell and terminated before `hp_default` completed. No `screen_summary.json`, no new checkpoints from that run. Prior `results/arm_kpis/hp_default.json` is from an **earlier** run (pre–reward-mode / pre–checkpoint changes).

**Action:** Re-run full screen in foreground when ready.

---

## Fixes applied this session

1. Three reward fork modes in `_exp14_reward_fork.py`.  
2. `reward_mode` on `ScreenArmSpec`; conservative / explore arms use alternate rewards.  
3. Checkpoint save after each screen arm; resume on `python run.py --full` (default).  
4. `--from-scratch` flag to skip resume.  
5. `reward_mode` in `warmup_preview.json`.  
6. Plain-text simulation info when stdout is piped or non–UTF-8.  
7. `stderr` UTF-8 reconfigure in `run.py`.

---

## Open follow-ups

| Priority | Item |
|----------|------|
| P0 | Update pipeline doc arm table with `reward_mode` column and actual reward implementation (not α–δ formula unless implemented). |
| P0 | Complete 5-arm screen; verify checkpoints under `results/checkpoints/{arm_id}/screen_final.pt`. |
| P1 | Implement or delete α–δ shaping constants; remove or wire `reward_credit_mode`. |
| P1 | Add `mission_score` to screen winner tie-break or secondary ranking table. |
| P2 | Optional `k_capture=1` arm to align RL return scale with mission score. |
| P2 | File logging in `append_log` (e.g. `results/exp14.log`) so operators need not pipe stdout. |
| P2 | Harden tqdm for piped stdout on Windows (or detect pipe and disable step bars). |

---

## Operator commands (current)

```powershell
conda activate auto-sat
cd D:\code\sem-proj-asc\backend\scripts\experiments\ml_mpo_multienv_target_select

# Stage A — 5 arms, saves KPIs + checkpoints
python run.py --screen --show-progress

# Stage B — resume winner weights (default)
python run.py --full --show-progress

# Preview reward fork for one arm
python run.py --export-warmup-preview --arm hp_explore --reward-plot-only
```

---

## Evidence paths

| Artifact | Path |
|----------|------|
| Warmup preview (conservative) | `results/warmup_preview.json` |
| Prior screen arm KPI | `results/arm_kpis/hp_default.json` |
| Piped-run crash | `results/run_error.json` |
| Reward plot | `results/artifacts/warmup_preview/episodes/warmup_ep_0_rank1_latent_applied.png` |
| Checkpoints (after screen) | `results/checkpoints/{arm_id}/screen_final.pt` |
