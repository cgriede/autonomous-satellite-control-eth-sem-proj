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
- **Episode orbit θ-extent (canonical rollouts):** `episode_theta_offsets_deg_for_target_areas(...)` in `MISSION.py` maps the union of `target_areas` latitude bounds (plus contact margin) to orbit-plane θ start/end via `mission_target_window_deg`. Symmetric `los_theta_offsets_deg` remains for diagnostics. `EnvironmentSetup.resolve()` uses the target-union window.
- **Distance reward (primary camera):** requires `OBSERVATION_TARGET` bins on the primary observation line (`picture_taken` = `target_visible`); outer distance gate applies only after that. Distance uses min geodesic range over all configured target areas.
- **Stripe-derived θ bounds (diagnostic):** `mission_target_latitude_bounds_deg` / `mission_target_window_deg` expand the polar stripe by contact angle + margin in latitude, then map λ→θ offset; **north saturation at 90° N makes this asymmetric**, so it must not drive episode length alone.
- **Subsatellite latitude / longitude:** authoritative values come from **`ecef2geodetic`** applied to satellite positions mapped disk→ECEF (`utils/geometry/orbit_disk_wgs84.py`). The legacy polar meridian closure remains as an approximate diagnostic only (`subsatellite_latitude_deg_polar_meridian`).
- **Renderer:** main orbit view uses orbit-plane disk XY consistent with `camera_2d` / `SimulationStateSeries` footprint km fields; observer LOS anchor derives from stripe midpoint LLA projected onto the mean rendering sphere (`stripe_mid_observer_disk_xy_km_on_sphere`).
- **Derived:** circular orbit speed from sampled altitude via `circular_orbital_speed_from_altitude` (`utils/leo_adapter/orbit_geometry.py`).
- **Deferred terrain occlusion:** DEM-backed backends / optional HORAYZON–Embree paths are explicitly deferred (`backend/simulation/deferred_horayzon.py`).

---

# Pole-meridian track coordinates (orbit disk)

Source: `utils/geometry/orbit_disk_polar_meridian.py`, `utils/geometry/polar_meridian_track.py`.

- **Track offset** `δ` [deg]: along-track angle from north pole in the simulation orbit-disk model (`δ = λ − 90°` on the ascending leg; past the pole latitude mirrors as `λ = 90° − δ` with `δ > 0`).
- **Meridian longitude rule:** `δ ≤ 0` → `λ = LON_GLOBAL` (default `0°`); `δ > 0` → `λ = LON_GLOBAL + 180°` (anti-meridian, e.g. `180°` when `LON_GLOBAL = 0°`).
- **Disk polar angle** `φ` [deg]: `φ = SIMULATION.theta_center + δ` (default `theta_center = 90°`); authoritative for `camera_2d` cloud arcs and stripe overlap, via `φ = atan2(z, x)` on WGS84 surface points.
- **Examples:** `δ = 0` → north pole; `δ = −1°` → `89°N, 0°E`; `δ = +1°` → `89°N, 180°W`.
- **Not** the renderer north-polar azimuthal map (`geodesic_helpers.polar_azimuthal_plane_xy_km_to_lon_lat_deg`).
- **Clouds:** `SIMULATION.Cloud` uses `base_altitude`, `top_altitude`, and `GeodeticLonLat` endpoints (`start_location`, `end_location`). Rainforest sampling (`s01_utils/cloud_formation.py`): integer-km start on formation path, extent 1–100 km, base 4–12 km, thickness 1–16 km, `top = min(base + thickness, 20 km)`. Simulation converts LLA → disk φ via `orbit_disk_polar_meridian` at kernel init.
- **S01 baseline overflight clouds (notebook 07, `s01_utils/baseline_overflight.py`):** seeded clouds along the 50-target meridian corridor (first target leading edge → last target trailing edge), `cloud_seed = 0`. Bounds: `cloud_number_bounds = (15, 30)`, `cloud_range_bounds = 1–80 km`, `cloud_base_altitude_bounds = 4–12 km`, `cloud_thickness_bounds = 1–16 km`, `max_top_altitude = 20 km`. Default seed yields 27 cloud patches that partially/fully occlude some captures (reduces per-bin target coverage and adds `camera_cloud_blocked_fraction`).
- **S01 baseline engage gate:** `SequentialTargetBaselinePolicy` enters target engage only when the orbit-φ window is open **and** `target_pointing_safe_for_engage` is true — projected off-nadir at the target boresight plus braking distance stays below `OFF_NADIR_HARD_LIMIT_DEG` (45°). Source: `simulation/attitude_controller.py`, `s01_utils/baseline_overflight.py`.

---

# Simulation constants (`SIMULATION`)

Source: `environment_definition/constants/SIMULATION.py`.

- **Animation:** `num_frames` = 2000, `animation_interval` = 30 ms, `default_speed_multiplier` = 30, `export_speed_multiplier` = 30.
- **Geometry / motion:** `theta_center` = 90°, `sat_motion_span_scale` = 1.05, `contact_margin_angle` = 0.05°, `sat_z_offset` = 0°.
- **Default body spin:** `default_body_spin_rate` = 3°/s.
- **FOV cone:** length 20 000 km; opening from pinhole vertical FOV (`pinhole_full_fov_rad` with `SENSOR_HEIGHT`, `FOCAL_LENGTH`); `z_axis_length` = 180 km.
- **Cloud strip (latitude bounds on ``LON_GLOBAL`` projected to disk polar angles):** height 15 km, first cloud latitude sweep ≈ **89.99° → 90.2°** geodetic (`SIMULATION.clouds` tuple).
- **Camera stats:** `camera_pixel_ray_samples` = 96, `camera_observation_line_n_bins` = 100.
- **Camera kernel backend:** `camera_kernel_backend` = `"accelerated"` (default). Batches all strip pixel rays and all observation-line bins per timestep via NumPy (`simulation/camera_2d.py`). The `"python"` backend remains as a parity reference (per-ray Python loops).
- **Episode cap:** `max_episode_steps` = 1000 (canonical rollout cap shared by gym and MPO runtime).

---

# MPO training episodes (`EpisodeRunner`)

Source: `environment_definition/constants/SIMULATION.py` (`training_episode_simulation_config`), `autonomous_control/episode_runner.py`, `notebooks/s01/s01_utils/training_workflow.py`.

- **Torque path:** external policy (`torque_command_source="external"`); warmup uses sequential baseline overflight (`SequentialTargetBaselinePolicy`), train/eval use `MPOAgent.get_action`. Both request torque; `AttitudeSafetyController` arbitrates before the wheel.
- **Attitude safety:** `attitude_controller_enabled=True` — `AttitudeSafetyController` arbitrates every external torque command (off-nadir taper, safe-mode takeover) before the reaction-wheel plant.
- **Replay buffer:** stores the **policy request** `[torque_request_nm, shutter_gym]` (shape `(2,)`); applied torque after arbitration is in `SimulationStateSeries.wheel_torque_cmd_nm`.
- **Early stop on budget:** `TrainingWorkflowConfig.early_stop_on_budget_exhausted` (default `False`). When enabled, warmup/train episodes truncate once `TakePictureBudget.remaining == 0`; eval always runs the full configured horizon.

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
