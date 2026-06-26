<!--
  Slideshow-style: blank line, then a line with only --- between slides.
-->

# Technical constants

Subsystem parameters: camera, bus, reaction wheel, and timing (design or simulated).

---

# Camera & optics

Source: `environment_definition/constants/SATELLITE.py`.

- **Resolution:** `N_PIXELS_X` = 9344, `N_PIXELS_Y` = 7000.
- **Pixel pitch:** `PIXEL_SIZE` = 3.2 µm.
- **Focal length:** `FOCAL_LENGTH` = 1067 mm.
- **Sensor size:** `SENSOR_WIDTH` / `SENSOR_HEIGHT` from pixels × pitch.
- **Reference altitude (design note):** `CAMERA_ALTITUDE` = 500 km (nominal; mission uses sampled altitude in M1).
- **Full vertical FOV:** computed in `SIMULATION.field_of_view_cone.opening_angle` via `pinhole_full_fov_rad(SENSOR_HEIGHT, FOCAL_LENGTH)`.
- **Exposure (motion blur):** `CAMERA_EXPOSURE_TIME` = 100 µs (primary default; per-camera `CameraImage.exposure_time` in sim).
- **Max captures per orbit (arbitrary OBC budget):** `MAX_PRIMARY_CAPTURES_PER_ORBIT` = 10 (memory + downlink; `AUTONOMOUS_CONTROL_REWARD.MAX_PICTURES_PER_EPISODE` aliases this).

---

# Primary-camera image quality (motion smear)

Source: `simulation/image_quality.py`, wired in `simulation/stepper.py` during primary camera evaluation.

- **Smear (dimensionless px in GSD units):** `smear_px = (|v_bore_ground| · t_exp) / GSD`
  - `v_bore_ground` [m/s]: analytic magnitude of `d(bore_ground_xy)/dt` on the orbit disk.
  - `t_exp` [s] from `CAMERA_EXPOSURE_TIME`, `GSD` [m] from per-frame `camera_gsd_m`.
- **Analytic bore ground speed:** WGS84 ray hit matching `camera_2d` / `orbit_disk_wgs84.disk_ray_earth_hit_xy_km`.
  - Satellite disk velocity: `v_sat = R_orbit · ω_orbit · (−sin θ, cos θ)`.
  - Boresight rate: `b̂̇` from body rate `ω_body` on the disk unit vector.
  - Ray parameter `t` from oblate-spheroid quadratic; `ṫ` from implicit differentiation; `ḣ = v_sat + ṫ b̂ + t b̂̇` mapped to disk xy [m/s].
- **Diagnostics:** `slant_range` [km], `elevation` [deg] at bore (local radial vs tangent in disk).
- **Normalized quality:** `quality = ref / (blur_m + ref)` clipped to [0, 1]; `blur_m = |v_bore| · t_exp` [m]; `ref = IMAGE_QUALITY_SMEAR_REFERENCE_M` (0.30 m → quality 0.5 at 0.30 m blur). Nadir orbit (~0.7 m blur) → ~0.3; target track (~0.04 m) → ~0.9. `smear_px = blur_m / GSD` for telemetry only.
- **Episode fields:** `SimulationStateSeries.camera_image_smear_px`, `camera_image_quality` (primary only).

---

# Satellite bus & RW

Source: `environment_definition/constants/SATELLITE.py` (and `attitude_control_env.py` for control-env overrides).

- **Mass:** `SATELLITE_MASS` = 250 kg.
- **Inertia (3D):** Ixx = 16.6, Iyy = 21.7, Izz = 31.2 kg·m²; **2D env uses** `MOMENT_OF_INERTIA_2D` = Izz.
- **Star tracker:** `STAR_TRACKER_MAX_MANEUVER_RATE` = 3°/s.
- **Reaction wheel (generic Rocket Lab–style labels in code):** `REACTION_WHEEL_MAX_TORQUE` = 0.1 N·m, `REACTION_WHEEL_MAX_MOMENTUM` = 0.4 N·m·s.
- **Gym env torque cap:** `tau_max` = 0.02 N·m in `SatelliteAttitudeControlEnv` (differs from catalog `REACTION_WHEEL_MAX_TORQUE` — document both).

---

# Attitude safety (movement constraints)

Source: `environment_definition/constants/ATTITUDE_SAFETY.py`, `simulation/attitude_controller.py`, `simulation/stepper.py`.

- **Torque path:** agent `τ_cmd` → `AttitudeSafetyController.arbitrate()` → `ReactionWheel.compute_applied_torque()` → `propagate_reaction_wheel_attitude_2d()`.
- **OBC controller type:** `AttitudeSafetyController` — arbitrates policy torque requests (pass-through, taper, or safe-mode takeover). Safe-mode recovery uses **PD body pointing + orbit-rate feedforward** (`body_pointing_torque_nm` / `nadir_pointing_torque_nm`).
- **Notebook 07 baseline:** `SequentialTargetBaselinePolicy` emits PD torque **requests** (same helpers as `AttitudePointingController`) on `training_episode_simulation_config`; no `set_obc_pointing_mode` engage path in rollout/warmup.
- **Off-nadir hard limit:** `OFF_NADIR_HARD_LIMIT_DEG` = 45°.
- **Nadir recovery tolerance:** `NADIR_RECOVERY_TOLERANCE_DEG` = 1.0°.
- **Decel band (cruise → settle handoff):** `SAFE_MODE_DECEL_START_DEG` = 5.0° off-nadir.
- **Stopped threshold:** `SAFE_MODE_OMEGA_STOP` = 0.1°/s (|ω_sat − ω_orbit| for phase transitions).
- **Safe-mode cruise rate:** `SAFE_MODE_CRUISE_RATE_DEG_S` = 0.35°/s (added as slew command on top of orbit feedforward during CRUISE).
- **Post-recovery lockout:** `SAFE_MODE_LOCKOUT_S` = 10 s (agent torque rejected; OBC nadir hold continues).
- **Nadir target:** instantaneous `θ* = θ_orbit + π` with feedforward `ω_orbit`.
- **Safe-mode intervals (agent cut throughout):** BRAKE → CRUISE → SETTLE → LOCKOUT.
  - **BRAKE:** `ω_cmd = 0`; advance when |ω_sat − ω_orbit| ≤ `SAFE_MODE_OMEGA_STOP`.
  - **CRUISE:** `ω_cmd = ±SAFE_MODE_CRUISE_RATE` toward nadir when |θ_error| > tolerance; advance when off-nadir ≤ `SAFE_MODE_DECEL_START_DEG`.
  - **SETTLE:** `ω_cmd = 0`; advance when |θ_error| ≤ tolerance and |ω_sat − ω_orbit| ≤ `SAFE_MODE_OMEGA_STOP`.
  - **LOCKOUT:** hold nadir for `SAFE_MODE_LOCKOUT_S`, then exit safe mode.
- **Normal-mode taper:** linear scale 1 at `θ_arm`, 0 at `θ_hard`; `θ_arm = θ_hard − ω²/(2τ/I_sat)` (kinematic braking distance at max torque).
- **Safe-mode entry:** when off-nadir ≥ hard limit, or predicted violation `(off_nadir + θ_brake) ≥ θ_hard`.

---

# OBC pointing PD gains (safe mode & `AttitudePointingController`)

Source: `simulation/attitude_controller.py` (`default_nadir_pointing_gains`, `body_pointing_torque_nm`).

- **Control law:** `τ = K_p · e_θ + K_d · (ω_des − ω_sat)`, clipped to ±`τ_max`; `e_θ = wrap(θ* − θ_body)`.
- **Feedforward:** `ω_des = ω_target + ω_cmd`; `ω_target = ω_orbit` for nadir; ground-target track uses analytic boresight rate.
- **Gain tuning:** `K_p = τ_max / SAFE_MODE_DECEL_START` [N·m/rad]; `K_d = 2 √(K_p · I_sat)` [N·m·s/rad] (critically damped-style from inertia).
- **τ_max source:** `REACTION_WHEEL_MAX_TORQUE` in sim stepper (0.1 N·m); gym env may use a lower cap (see bus & RW slide).

---

# Reaction wheel — low-level safety gate

Source: `simulation/reaction_wheel.py`, `simulation/dynamics_kernel.py`, `simulation/stepper.py`.

- **Controller type:** directional **torque cutoff gate** (not PD/PID). Last line of defense before dynamics integration.
- **Rate limit:** `max_manouver_rate` = `STAR_TRACKER_MAX_MANEUVER_RATE` (3°/s) — applied to |ω_sat|, not wheel speed.
- **Rule:** if |ω_sat| ≤ limit → `τ_applied = τ_cmd`; else block commands that would increase |ω_sat| (`τ_cmd` opposite sign to ω_sat → 0), allow decelerating torques only.
- **Sign convention:** dynamics `α_sat = −τ_wheel / I_sat`; decelerating torque has the same sign as ω_sat.
- **Wheel inertia (sim stepper):** `omega_w_max` = 150 rad/s; `I_w` = `REACTION_WHEEL_MAX_MOMENTUM` / ω_max (0.4 N·m·s / 150 rad/s).
- **Coupled propagation:** `τ_wheel` accelerates wheel at `α_wheel = τ_wheel / I_w`; there is no explicit wheel-speed or momentum clamp in `ReactionWheel` (wheel inertia is set from `REACTION_WHEEL_MAX_MOMENTUM` and `omega_w_max` for dynamics scaling).

---

# Latency & inference (TBD)

If the stack assigns **per-module inference time** or pipeline budgets (onboard ML, guidance cycle), record:

- Budget (ms), where enforced (sim vs real), and coupling to `dt`.

---

# Traceability

| Topic | Primary code |
|--------|----------------|
| Camera & inertia catalog | `constants/SATELLITE.py` |
| Primary image smear / quality | `simulation/image_quality.py` |
| Attitude safety constants | `constants/ATTITUDE_SAFETY.py` |
| OBC safety / pointing PD | `simulation/attitude_controller.py` |
| RW torque gate & dynamics | `simulation/reaction_wheel.py`, `simulation/attitude_dynamics.py`, `simulation/dynamics_kernel.py` |
| Sim torque path wiring | `simulation/stepper.py` |
| Env-specific torque / ω limits | `environment_definition/attitude_control_env.py` |
