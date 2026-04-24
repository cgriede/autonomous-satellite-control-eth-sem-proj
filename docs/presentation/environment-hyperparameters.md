<!--
  Slideshow-style: blank line, then a line with only --- between slides.
  Compatible with Marp / similar Markdown-to-slide tools.
-->

# Environment & hyperparameters

Mission and simulation settings that define randomness, geometry, and runtime behavior.

---

# Mission profile (M1 random altitude)

- **Altitude sampling:** uniform between `SATELLITE_ALTITUDE_LOWER_BOUND` and `SATELLITE_ALTITUDE_UPPER_BOUND` (see `environment_definition/constants/MISSION.py`).
- **Current bounds:** 510 km–570 km (module load time samples once per process).
- **Derived:** circular orbit speed from sampled altitude via `circular_orbital_speed_from_altitude` (`utils/leo_adapter/orbit_geometry.py`).
- **Narrative goal (code comment):** maximize time with camera facing observer; Switzerland map center used in viz (`SIMULATION.switzerland_map`).

---

# Simulation constants (`SIMULATION`)

Source: `environment_definition/constants/SIMULATION.py`.

- **Animation:** `num_frames` = 2000, `animation_interval` = 30 ms, `default_speed_multiplier` = 30, `export_speed_multiplier` = 30.
- **Geometry / motion:** `theta_center` = 90°, `sat_motion_span_scale` = 1.05, `contact_margin_angle` = 0.05°, `sat_z_offset` = 0°.
- **Default body spin:** `default_body_spin_rate` = 3°/s.
- **FOV cone:** length 20 000 km; opening from pinhole vertical FOV (`pinhole_full_fov_rad` with `SENSOR_HEIGHT`, `FOCAL_LENGTH`); `z_axis_length` = 180 km.
- **Cloud strip (degrees along orbit):** height 15 km, `start_location` 89.99° → `end_location` 90.2° (first cloud tuple).
- **Camera stats:** `camera_pixel_ray_samples` = 96, `camera_observation_line_n_bins` = 100.

---

# Gym environment (`SatelliteAttitudeControlEnv`)

Source: `environment_definition/attitude_control_env.py`.

- **Integration step:** `dt` = 0.1 s (pint).
- **Episode:** `max_episode_steps` = 500.
- **Initial state (reset):** θ ~ U(−π/4, π/4), ω_s ~ U(−0.5, 0.5), ω_w = 0, `target_theta` ~ U(−π/3, π/3).
- **Wheel limit used in env:** `omega_w_max` = 150 rad/s (float; saturation / termination).

---

# Traceability

| Concept | Primary code |
|--------|----------------|
| Mission sampling | `mission_profiles/mission_1_random_fl.py`, `constants/MISSION.py` |
| Sim / clouds / map | `constants/SIMULATION.py` |
| RL env dynamics & reward | `attitude_control_env.py` |
