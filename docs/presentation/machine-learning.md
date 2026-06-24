<!--
  Slideshow-style: blank line, then a line with only --- between slides.
-->

# Machine learning & objectives

Reward structure, losses (when added), and function approximators for control.

---

# Reward (attitude control env)

Source: `environment_definition/attitude_control_env.py` (`SatelliteAttitudeControlEnv.step`).

**Reward implementation:**

- Reward is computed via `compute_reward(signals=..., cfg=RewardConfig)`.
- Signals include target visibility, distance-to-target proxy, area-intersection terms, and wheel-dynamics terms.
- Primary distance-band term is piecewise:
  - `0` if outside viewing gate or outside distance band.
  - `-100` if inside distance band but target is not visible (or no picture).
  - `-100 + 100 * scalar` if inside distance band and visible, with `scalar=1` at `d_op` and `scalar=0` at `d_th`.
- Geodetic area-target terms (simulation path):  
  - `area_intersection_reward = REWARD_AREA_INTERSECTION_WEIGHT * target_area_intersection_ratio`  
  - `area_novelty_reward = REWARD_AREA_NOVELTY_WEIGHT * target_area_novelty_ratio`
- **Take-picture capture term** (`autonomous_control/reward.py`, `simulation/take_picture.py`):
  - `MAX_PRIMARY_CAPTURES_PER_ORBIT = 10` in `SATELLITE.py` (arbitrary OBC memory / downlink budget per orbit; alias `MAX_PICTURES_PER_EPISODE`)
  - Motivation: agent cannot downlink unlimited HQ frames; credit is paid only on discrete shutter events within budget
  - When `RewardConfig.enable_image_quality_capture`:
    - **Latent** (every step, for policy diagnostics / critic shaping):  
      `latent_capture_reward = REWARD_IMAGE_QUALITY_CAPTURE_WEIGHT * coverage * quality * (1 - cloud_frac)`
    - **Applied** (MPO agent credit): same formula **only** when `picture_taken` and `capture_target_novel` at a budgeted shutter frame
    - `coverage` = primary-camera bins on the **dominant** target index at shutter time / total bins
    - `quality` = normalized primary `camera_image_quality` from canonical sim series
    - **Target novelty:** observation-line codes are indexed `T0`, `T1`, … (`OBSERVATION_TARGET` = 3 = T0, then 4 = T1, …). ASCII line uses `0`, `1`, … for T0, T1. Repeat shutter on an already-captured target index consumes budget but `capture_target_novel = false` → applied reward `0`.
  - Cloud-blocked fraction scales down both latent and applied credit; full block → zero

**Episode end conditions:**

- **Terminated:** |ω_w| > `omega_w_max` (wheel saturation).
- **Truncated:** step count ≥ `max_episode_steps`.

---

# Observations & actions

- **Controller observation (notebook 08):** selected `SimulationTimestepState` keys — attitude scalars, orbit angle, primary + secondary camera observation-line code arrays (see `S01_TRAINING_FEATURE_CONFIG` in `notebooks/s01/s01_utils/training_workflow.py`).
- **MPO action (2-D):** `[wheel_torque_cmd_nm, take_picture_signal]` — torque clipped to ±`tau_max`; shutter fires when `take_picture_signal > 0` (after `tanh` policy scaling). Source: `autonomous_control/action_adapter.py`, `autonomous_control/episode_runner.py`.
- **Warmup:** torque-only baseline/random policies; shutter dimension stored as `-1` (no capture).

---

# Training loop policies (notebook 08)

Source: `autonomous_control/episode_runner.py`, `notebooks/s01/s01_utils/training_workflow.py`.

- **`RewardConfig` plumbing:** `MPOConfig.reward` is passed via `SimulationOverrides(reward_config=...)` on the s01 mission setup so `SimulationStepper` and `RewardKernel` share the same flags.
- **Capture on shutter:** `TakePictureBudget` per episode; `apply_shutter_capture` recomputes step reward with quality/coverage/novelty at the resolved capture frame (parity with notebook 06 `take_picture_verification`).
- **Early stop:** `warmup` / `train` episodes end when `budget.remaining == 0`; **`eval` runs full horizon** (`early_stop_on_budget_exhausted=False`).
- **`train_every_n_steps`:** default `1`; MPO `train()` invoked every N simulation steps in train mode (throughput knob, no mission change).
- **`collect_states`:** default `False`; skips per-step observation copies in the RL hot path.

---

# Networks & optimization

- MPO policy/critic implementation lives in `autonomous_control/controller_agent.py` (`MPOAgent`).
- Main training/eval orchestration lives in `scripts/train_sat_agent.py` and `scripts/eval_sat_agent.py`.

---

# Traceability

| Topic | Primary code |
|--------|----------------|
| Reward & step | `simulation/reward_kernel.py`, `autonomous_control/reward.py`, `simulation/episode_capture.py` |
| MPO trainer | `autonomous_control/controller_agent.py`, `autonomous_control/episode_runner.py` |
| Notebook 08 workflow | `notebooks/s01/s01_utils/training_workflow.py` |
