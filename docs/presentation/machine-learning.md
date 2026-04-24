<!--
  Slideshow-style: blank line, then a line with only --- between slides.
-->

# Machine learning & objectives

Reward structure, losses (when added), and function approximators for control.

---

# Reward (attitude control env)

Source: `environment_definition/attitude_control_env.py` (`SatelliteAttitudeControlEnv.step`).

**Reward implementation:**

- Reward is computed via `canonical_reward(signals=..., cfg=RewardConfig)`.
- Signals include target visibility, distance-to-target proxy, and wheel-dynamics terms.

**Episode end conditions:**

- **Terminated:** |ω_w| > `omega_w_max` (wheel saturation).
- **Truncated:** step count ≥ `max_episode_steps`.

---

# Observations & actions

- **State (5-D):** `[angle_rel_nadir, omega_sat, alpha_sat, angle_to_target, omega_wheel]`.
- **Action:** commanded wheel torque (scalar), clipped to ±`tau_max`.

---

# Networks & optimization

- MPO policy/critic implementation lives in `autonomous_control/controller_agent.py` (`MPOAgent`).
- Main training/eval orchestration lives in `scripts/train_sat_agent.py` and `scripts/eval_sat_agent.py`.

---

# Traceability

| Topic | Primary code |
|--------|----------------|
| Reward & step | `environment_definition/attitude_control_env.py` |
| MPO trainer | `autonomous_control/controller_agent.py` |
