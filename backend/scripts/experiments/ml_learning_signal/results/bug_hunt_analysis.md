# Analysis — bug_hunt (Branch B)

Source: probes + code trace + shared baseline (`a1_fundamental.json` train returns `[0, 0, 0]`)

## 1 Verdict

**Bug found (wiring). strong_lead: false.**

Train episodes are not failing because the shutter never fires. On-policy train ep0 fired **10 shutter commands in 37 steps** but earned **0 capture reward** (`positive_reward_steps=0`). Warmup baseline fires the same budget with **~145 return** because timing is correct.

## 2 Best train returns (production path, seed 7)

| Episode | Return |
|---------|--------|
| ep1 | 0.0 |
| ep2 | 0.0 |
| ep3 | 0.0 |

Reference run `nb-s01-08-2026-06-27_12-19-52` (1 train ep, `early_stop_on_budget_exhausted=false`) got **3.73** — sparse lucky capture, not reproducible on current 3-ep slice.

## 3 Confirmed wiring bugs

### Bug A — replay store cadence (primary)

**File:** `backend/autonomous_control/episode_runner.py` ~668–670

`agent.store((obs, stored_action.copy(), reward, next_obs, done))` runs **every simulation step**, but `stored_action` is only refreshed on controller ticks (~every 2 steps). Non-controller steps duplicate the prior action (including shutter dim) against unrelated step rewards, diluting the **14 / 9675 (0.14%)** positive capture transitions preloaded from warmup.

**Minimal production fix:** gate `agent.store` on a `controller_updated_this_step` flag set inside the `should_update_controller()` block.

### Bug B — early-stop default footgun

**File:** `backend/autonomous_control/episode_runner.py` ~266–268

When `early_stop_on_budget_exhausted is None`, it defaults to **True** for train/warmup, despite `TrainingWorkflowConfig.early_stop_on_budget_exhausted=False`. Direct `run_serial` callers (probes, tests) truncate at **step 37** after budget exhaustion with **0 return**. Training workflow passes `False` explicitly — production notebook path is OK; API default is misleading.

**Minimal production fix:** default to `False` to match workflow config, or require explicit bool (no silent True).

## 4 Ruled out

| Candidate | Evidence |
|-----------|----------|
| Shutter never fires | `n_shutter_cmds=10`, `p_shutter_fire≈0.77` |
| action_dim=1 drops shutter | env is 2-D; cmds recorded |
| Threshold 0.5 blocks all exploration | 77% of samples exceed threshold |
| Reward not wired on shutter | same `apply_shutter_capture` path as warmup; failed captures get 0 credit |

## 5 Fork runs (B1–B3)

| Run | Intervention | strong_lead | Notes |
|-----|--------------|-------------|-------|
| B1 | threshold 0.5→0.35 | false | interrupted; threshold not limiting |
| B2 | controller-only store | false | interrupted ~16% ep1 |
| B3 | combined | not run | budget spent on B1/B2 |

## 6 Promote recommendation

1. Fix **Bug A** in `episode_runner.py` (store only on controller ticks).
2. Fix **Bug B** default for API consistency.
3. Re-run `run_baseline.py` / bug-hunt slice; expect nonzero returns only if capture timing also improves (may still need >3 episodes).
