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
- **Shutter waste penalty** (nb08 default on): when `enable_shutter_waste_penalty`, accepted shutter with applied capture credit below `shutter_waste_reward_epsilon` → `shutter_waste_penalty = −k_shutter_waste` (`REWARD_SHUTTER_WASTE_PENALTY = 5.0`, tunable starting guess).
- **Budget-exhausted shutter penalty** (nb08 default **on**, Exp 7 promoted): when `enable_budget_exhausted_shutter_penalty`, agent shutter command while `capture_budget_remaining ≤ 0` → add `−k_shutter_waste` at that step in `simulation/stepper.py::apply_shutter_capture` (distinct from shutter-waste term above; does not change applied capture credit on valid budgeted shutters). Source: `autonomous_control/reward.py` (`budget_exhausted_shutter_command_penalty`).
- **Torque effort penalty** (nb08 default on): see slide *Control-effort vs wheel-energy penalty* below.
- **Passive-policy fallback:** penalty-only dense terms can yield a “do nothing” optimum; if post-change training shows near-zero torque/shutter activity, add potential-based pointing shaping (`Φ = −min bearing to nearest unseen target`) before MPO hyperparameter tuning.

---

# Control-effort vs wheel-energy penalty

Two distinct dense penalties on reaction-wheel actuation exist in `autonomous_control/reward.py`. **Notebook 08 enables torque effort, not energy** (`enable_torque_effort=True`, `enable_energy=False` in `training_workflow.py`).

**Torque effort (control regularizer, nb08 default)**

- Toggle: `RewardConfig.enable_torque_effort`
- Formula (every control step):  
  `torque_effort_penalty = −k_torque_effort × (τ_cmd / τ_max)²`
- Signal: **agent-requested** wheel torque `wheel_torque_agent_cmd_nm` (normalized action × `REACTION_WHEEL_MAX_TORQUE`), **before** attitude-safety arbitration; not the post-limit torque applied to dynamics.
- Units: dimensionless squared normalized command; coefficient `k_torque_effort` is **not** J⁻¹ (`REWARD_TORQUE_EFFORT_COEFFICIENT = 0.1`, tunable starting guess).
- Gating: none — applies on every step when enabled.
- Role: LQR-style **control-effort** shaping to discourage policy torque saturation (±τ_max stick inputs) and give a direct gradient on the torque action dimension. This is **not** a physical energy or power accounting term.

**Wheel-energy penalty (physical proxy, off in nb08)**

- Toggle: `RewardConfig.enable_energy`
- Formula: `energy_reward = −k_energy × E` with  
  `E = (ΔH)² / (2 I_w)` [J], `ΔH = |I_w ω_after − I_w ω_before|`, `H = I_w ω` (`energy_from_wheel_momentum_change`).
- Signal: **actual** wheel speed change after propagation (`omega_before`, `omega_after` on the wheel).
- Units: joules × `REWARD_ENERGY_LINEAR_COEFFICIENT` (`k_energy = 10.0`; chosen so typical step energies do not dwarf ±100 capture credit).
- Gating: when `enable_outer_gate`, only inside `CAMERA_VIEWING_DISTANCE_THRESHOLD` (same gate as legacy distance band).
- Role: penalize kinetic-energy proxy associated with **momentum transferred to the wheel**, not commanded torque magnitude.

**Why nb08 uses torque effort instead of energy**

| Aspect | Torque effort | Wheel energy |
|--------|---------------|--------------|
| Penalizes | Commanded τ (policy output) | Observed Δω_w after dynamics |
| Saturation at ±τ_max | Full penalty at max command | Weak if wheel already saturated (small ΔH) |
| RL credit assignment | Direct on action | Indirect via wheel state / inertia |
| Physical interpretation | Control cost regularizer | Joule-scale momentum-change proxy |

For **reporting:** describe torque effort as a normalized **actuation regularizer** added for learning stability (anti-saturation), not as mission electrical or mechanical energy minimization. A future experiment can enable `enable_energy` (or a `τ·ω·Δt` work integral) if the objective should track physical wheel cost instead.

Sources: `autonomous_control/reward.py` (`torque_effort_penalty`, `energy_reward`), `simulation/stepper.py` (`wheel_torque_agent_cmd_nm`), `environment_definition/constants/AUTONOMOUS_CONTROL_REWARD.py`.

**Episode end conditions:**

- **Terminated:** |ω_w| > `omega_w_max` (wheel saturation).
- **Truncated:** step count ≥ `max_episode_steps`.

---

# Observations & actions

- **Controller observation (notebook 08):** selected `SimulationTimestepState` keys — attitude scalars (`body_z_angle_rad`, `omega_sat_rad_s`), orbit angle (`theta_orbit_rad`), primary + secondary camera observation-line code arrays — plus **mission scalars** from `ControllerEpisodeContext`:
  - `capture_budget_remaining` — pictures left this episode (dimensionless count).
  - `target_already_imaged_i` — binary mask per mission target (1 if target index *i* already captured this episode, else 0); source `TakePictureBudget.captured_target_indices`.
  - `target_bearing_error_rad_i` — signed pointing error toward mission target *i* [rad], one per `len(target_areas)`; `wrap_pi(θ_boresight,i − body_z_angle_rad)`; 0 when aligned over target *i*.
- Source: `S01_TRAINING_FEATURE_CONFIG` in `notebooks/s01/s01_utils/training_workflow.py`, `autonomous_control/controller_observation.py`.
- **MPO action (2-D, gym space `[-1, 1]²`):** policy outputs `[torque_norm, shutter_gym]`; replay buffer stores the same normalized vector via `to_gym_action_array`.
  - **Torque:** `torque_norm ∈ [-1, 1]` → `wheel_torque_cmd = torque_norm × τ_max` [N·m] (`REACTION_WHEEL_MAX_TORQUE`).
  - **Shutter:** continuous `shutter_gym ∈ [-1, 1]` → map to `[0, 1]` via `0.5 × (shutter_gym + 1)`; boolean cmd when mapped value **>** `0.5` (`DEFAULT_SHUTTER_THRESHOLD`).
  - Source: `autonomous_control/action_adapter.py`, `autonomous_control/training_runtime.py` (`make_attitude_control_env`).
- **Warmup:** notebook-07 `SequentialTargetBaselinePolicy`; buffer stores `[torque_norm, shutter_gym]` with `shutter_gym = +1` on capture steps, `-1` otherwise. Same sim config and safety stack as train/eval.

---

# Training loop policies (notebook 08)

Source: `autonomous_control/episode_runner.py`, `notebooks/s01/s01_utils/training_workflow.py`.

- **`RewardConfig` plumbing:** `MPOConfig.reward` is passed via `SimulationOverrides(reward_config=...)` on the s01 mission setup so `SimulationStepper` and `RewardKernel` share the same flags.
- **Training reward (nb08 default):** capture credit on applied shutters plus dense penalties — `enable_shutter_waste_penalty=True`, `enable_torque_effort=True`; distance band off (`enable_distance_reward=False`). Warmup fingerprint includes `reward_config` snapshot (`notebook_warmup_bundle_cache.py`); rebuild cache when reward or obs layout changes.
- **Post-run diagnostics:** `summary_metrics.json` → `action_diagnostics` (torque histogram stats, fraction of shutters with reward > ε, mean |ω| at shutter). Required before coefficient tuning.
- **Capture on shutter:** `TakePictureBudget` per episode; `apply_shutter_capture` recomputes step reward with quality/coverage/novelty at the resolved capture frame (parity with notebook 06 `take_picture_verification`).
- **Early stop toggle:** `TrainingWorkflowConfig.early_stop_on_budget_exhausted` (default `False` for A/B). When `True`, warmup/train truncate when `budget.remaining == 0`; **`eval` always runs full horizon** (`early_stop_on_budget_exhausted=False`).
- **`updates_per_step`:** default `1`; how many `MPOAgent.train()` calls run each time the learning gate opens. Each call samples **batch_size = 256** transitions uniformly from the full replay buffer (not the current episode only).
- **`train_every_n_steps`:** default `1`; open the learning gate every **N controller stores** in train mode — **not** every simulation integration step. Replay `store()` still runs on every controller tick (~0.8 s, ~2 sim steps); only backprop is throttled. Example: ~968 stores per full episode at default `1`; `train_every_n_steps=50` ⇒ ~19 gradient updates per episode. Throughput knob; does not change mission physics.
- **Rollout vs learning:** `get_action` is inference-only (`torch.no_grad()`). Calling `train()` inside the rollout loop is an `episode_runner.py` design choice, not an MPO requirement.
- **`collect_states`:** default `False`; skips per-step observation copies in the RL hot path.

---

# Networks & optimization

- MPO policy/critic implementation lives in `autonomous_control/controller_agent.py` (`MPOAgent`).
- Main training/eval orchestration lives in `scripts/train_sat_agent.py` and `scripts/eval_sat_agent.py`.

---

# Vision 1D-CNN encoder (MPO)

Source: `autonomous_control/mpo_config.py` (`MPOConfig.num_cnn_layers`), `autonomous_control/CNN_1d.py` (`cnn_vision_conv_stack`).

- **`num_cnn_layers`:** selectable depth **1**, **2** (default), or **3** for each camera observation-line encoder.
- **Kernel size by depth:** 1 layer → **k=3**, 2 layers → **k=5** (each layer), 3 layers → **k=7** (each layer).
- **Channels / stride:** `(16)`, `(16, 32)`, or `(16, 32, 64)` with stride **2** per layer; output embedding **`cnn_embedding_dim` = 32**; code embedding **`code_embed_dim` = 8**.

---

# Action interface — attitude request mode

Source: `autonomous_control/action_adapter.py`, `TrainingWorkflowConfig.attitude_request_mode`, `simulation/obc_pointing_request.py`.

| Config | Default | dim0 semantics |
|--------|---------|----------------|
| `attitude_request_mode="torque"` | **yes** | RW torque fraction → `AttitudeSafetyController` |
| `attitude_request_mode="vector"` | no | `u ∈ [-1,1]` → `f_n = max_safe·u` → hold-last OBC PD → τ |

Set on **`TrainingWorkflowConfig`** (notebook 08 / all pipeline runners). Vector mode disables torque-effort reward penalty automatically.

---

# Traceability

| Topic | Primary code |
|--------|----------------|
| Reward & step | `simulation/reward_kernel.py`, `autonomous_control/reward.py`, `simulation/episode_capture.py` |
| Control-effort vs energy | `autonomous_control/reward.py` (`torque_effort_penalty`, `energy_reward`); constants `AUTONOMOUS_CONTROL_REWARD.py` |
| MPO trainer | `autonomous_control/controller_agent.py`, `autonomous_control/episode_runner.py` |
| Notebook 08 workflow | `notebooks/s01/s01_utils/training_workflow.py` |
