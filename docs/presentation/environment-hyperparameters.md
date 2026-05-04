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
- **Primary target (polar stripe):** fixed meridian longitude `LON_GLOBAL` = `0°`; latitude band `[OBSERVATION_TARGET_STRIPE_START_LAT, OBSERVATION_TARGET_STRIPE_END_LAT]` (see `environment_definition/constants/MISSION.py`).
- **Episode orbit θ-extent (canonical rollouts):** `los_theta_offsets_deg(...)` in `environment_definition/constants/MISSION.py` — symmetric ±(`minimum_contact_angle` + `SIMULATION.contact_margin_angle`). Used by `simulation_runner`, training workers, and matches renderer LOS framing (`render_main`).
- **Stripe-derived θ bounds (diagnostic):** `mission_target_latitude_bounds_deg` / `mission_target_window_deg` expand the polar stripe by contact angle + margin in latitude, then map λ→θ offset; **north saturation at 90° N makes this asymmetric**, so it must not drive episode length alone.
- **Subsatellite latitude / longitude:** authoritative values come from **`ecef2geodetic`** applied to satellite positions mapped disk→ECEF (`utils/geometry/orbit_disk_wgs84.py`). The legacy polar meridian closure remains as an approximate diagnostic only (`subsatellite_latitude_deg_polar_meridian`).
- **Renderer:** main orbit view uses orbit-plane disk XY consistent with `camera_2d` / `SimulationStateSeries` footprint km fields; observer LOS anchor derives from stripe midpoint LLA projected onto the mean rendering sphere (`stripe_mid_observer_disk_xy_km_on_sphere`).
- **Derived:** circular orbit speed from sampled altitude via `circular_orbital_speed_from_altitude` (`utils/leo_adapter/orbit_geometry.py`).
- **Deferred terrain occlusion:** DEM-backed backends / optional HORAYZON–Embree paths are explicitly deferred (`backend/simulation/deferred_horayzon.py`).

---

# Simulation constants (`SIMULATION`)

Source: `environment_definition/constants/SIMULATION.py`.

- **Animation:** `num_frames` = 2000, `animation_interval` = 30 ms, `default_speed_multiplier` = 30, `export_speed_multiplier` = 30.
- **Geometry / motion:** `theta_center` = 90°, `sat_motion_span_scale` = 1.05, `contact_margin_angle` = 0.05°, `sat_z_offset` = 0°.
- **Default body spin:** `default_body_spin_rate` = 3°/s.
- **FOV cone:** length 20 000 km; opening from pinhole vertical FOV (`pinhole_full_fov_rad` with `SENSOR_HEIGHT`, `FOCAL_LENGTH`); `z_axis_length` = 180 km.
- **Cloud strip (latitude bounds on ``LON_GLOBAL`` projected to disk polar angles):** height 15 km, first cloud latitude sweep ≈ **89.99° → 90.2°** geodetic (`SIMULATION.clouds` tuple).
- **Camera stats:** `camera_pixel_ray_samples` = 96, `camera_observation_line_n_bins` = 100.
- **Episode cap:** `max_episode_steps` = 1000 (canonical rollout cap shared by gym and MPO runtime).

---

# Gym environment (`SatelliteAttitudeControlEnv`)

Source: `environment_definition/attitude_control_env.py`.

- **Integration step:** `dt` = 0.1 s (pint).
- **Episode:** `max_episode_steps` = 1000 (sourced from `SIMULATION.max_episode_steps`).
- **Initial state (reset):** θ ~ U(−π/4, π/4), ω_s ~ U(−0.5, 0.5), ω_w = 0, `target_theta` ~ U(−π/3, π/3).
- **Wheel limit used in env:** `omega_w_max` = 150 rad/s (float; saturation / termination).

---

# Episode artifact (`SimulationStateSeries`)

Source: `simulation/state_types.py`, populated by `SimulationStepper` / `run_simulation`.

- **`wheel_torque_cmd_nm`:** per-frame wheel torque **command** [N·m] (same scalar passed to `SimulationStepper.step(wheel_torque_cmd_nm=...)`; frame 0 is 0 before the first step). Render overlays use this series for the torque time-series panel (`render/_torque_plot.py`).

---

# Traceability

| Concept | Primary code |
|--------|----------------|
| Mission sampling | `mission_profiles/mission_1_random_fl.py`, `constants/MISSION.py` |
| Sim / clouds / map | `constants/SIMULATION.py` |
| RL env dynamics & reward | `attitude_control_env.py` |
| Episode rollout arrays | `simulation/state_types.py`, `simulation/stepper.py` |
