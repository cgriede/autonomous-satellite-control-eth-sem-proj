<!--
  Slideshow-style: blank line, then a line with only --- between slides.
-->

# Machine learning & objectives

Reward structure, losses (when added), and function approximators for control.

---

# Reward (2D attitude env)

Source: `environment_definition/environment.py` (`SatelliteAttitude2D.step`).

**Pointing → pixels:** off-boresight angle \(\alpha\) maps to vertical pixel offset via pinhole:

- \(y = f \tan(\alpha)\), `pixel_offset_pixels` = \(y\) / `pixel_pitch`.
- Normalized by half sensor height: `pixel_offset_norm` = pixels / (0.5 × `N_PIXELS_Y`), clipped to [0, 1].

**Scalar reward (sign convention: maximize):**

- `reward` = −(`pixel_offset_norm_clipped`²) − 0.05·ω_w² − 0.01·`tau_applied_nm`²
- Additional term: −0.1·|ω_w| / `omega_w_max`

**Termination:** |ω_w| > `omega_w_max` (saturation). **Truncation:** step count ≥ `max_episode_steps`.

---

# Observations & actions

- **State:** [θ (rad), ω_s (rad/s), ω_w (rad/s)] — `observation_space` Box bounds include π, 5, and 1.1×`omega_w_max` on ω_w.
- **Action:** commanded wheel torque (scalar), clipped to ±`tau_max` (from env, tied to satellite torque budget in constants).

---

# Networks & losses (TBD)

Record here when implemented:

- Policy / value architecture (layers, activations, orthogonal init, etc.).
- Losses (e.g. clipped surrogate, value coeff, entropy coeff).
- Observation normalization and reward scaling used in training.

---

# Traceability

| Topic | Primary code |
|--------|----------------|
| Reward & step | `environment_definition/environment.py` |
| Future trainer | TBD |
