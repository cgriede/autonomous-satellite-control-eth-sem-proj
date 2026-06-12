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

Source: `environment_definition/constants/ATTITUDE_SAFETY.py`, `simulation/attitude_controller.py`.

- **Off-nadir hard limit:** `OFF_NADIR_HARD_LIMIT_DEG` = 45°.
- **Safe-mode cruise rate:** `SAFE_MODE_CRUISE_RATE_DEG_S` = 0.35°/s.
- **Post-recovery lockout:** `SAFE_MODE_LOCKOUT_S` = 10 s (agent torque rejected; OBC nadir hold continues).
- **Nadir mode:** instantaneous target `θ* = θ_orbit + π` with orbit-rate feedforward `ω_orbit` (`nadir_pointing_torque_nm`).
- **Safe-mode intervals:** BRAKE → CRUISE → SETTLE → LOCKOUT (agent cut throughout).
- **Dynamic taper arm:** `θ_arm = θ_hard − ω²/(2τ/I_sat)` (braking distance from current rate).

---

# Wheel model in 2D env

Source: `environment_definition/attitude_control_env.py`.

- **Saturation speed:** `omega_w_max` = 150 rad/s.
- **Wheel inertia:** `I_w` = `REACTION_WHEEL_MAX_MOMENTUM` / (ω_max as quantity).

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
| Env-specific torque / ω limits | `environment_definition/attitude_control_env.py` |
| RW dynamics | `simulation/reaction_wheel.py`, `simulation/attitude_dynamics.py` |
