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

---

# Satellite bus & RW

Source: `environment_definition/constants/SATELLITE.py` (and `attitude_control_env.py` for control-env overrides).

- **Mass:** `SATELLITE_MASS` = 250 kg.
- **Inertia (3D):** Ixx = 16.6, Iyy = 21.7, Izz = 31.2 kg·m²; **2D env uses** `MOMENT_OF_INERTIA_2D` = Izz.
- **Star tracker:** `STAR_TRACKER_MAX_MANEUVER_RATE` = 3°/s.
- **Reaction wheel (generic Rocket Lab–style labels in code):** `REACTION_WHEEL_MAX_TORQUE` = 0.1 N·m, `REACTION_WHEEL_MAX_MOMENTUM` = 0.4 N·m·s.
- **Gym env torque cap:** `tau_max` = 0.02 N·m in `SatelliteAttitudeControlEnv` (differs from catalog `REACTION_WHEEL_MAX_TORQUE` — document both).

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
| Env-specific torque / ω limits | `environment_definition/attitude_control_env.py` |
| RW dynamics | `simulation/reaction_wheel.py`, `simulation/attitude_dynamics.py` |
