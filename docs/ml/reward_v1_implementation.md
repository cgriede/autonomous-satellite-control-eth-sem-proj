# Autonomous control reward v1 — implementation notes

**Version:** 0.1  
**Date:** 2026-04-22

## PDF baseline (slides)

- Primary objectives only; discrete penalties of **-100** for: no picture; picture without visible target; picture beyond resolution distance threshold.
- Inside the acceptable band,  
  \(R_1 = -100 \cdot |r_t - r_{sat}| \cdot \frac{1}{d_{th} - d_{op}}\)  
  with optimal ground range \(d_{op}\) and outer threshold \(d_{th}\).

## Project deltas

1. **Outer viewing gate** (`CAMERA_VIEWING_DISTANCE_THRESHOLD` in `backend/environment_definition/constants/AUTONOMOUS_CONTROL_REWARD.py`): if \(|r_t - r_{sat}|\) is **greater** than this threshold, reward is **0** (no slide penalties and **no** energy penalty). This matches “far away, analyze clouds / do not punish idle behavior.”

2. **Distance proxy:** \(|r_t - r_{sat}|\) is modeled as a single **slant / ground-range** length quantity in Pint (typically kilometers in config, converted to meters inside `reward_v1_slides`). Callers should use the same geometric definition as the mission sim (e.g. 2D planar distance in the simulation plane vs geodesic — keep one convention end-to-end).

3. **Band handling:** If distance \(d < d_{op}\), the slide linear term uses \(d_{\mathrm{eff}} = \max(d, d_{op})\) so the numerator does not drop below the “best resolution” reference.

4. **Energy penalty:** Subtract \(k_E \cdot E\) with \(k_E =\) `REWARD_ENERGY_LINEAR_COEFFICIENT` and  
   \(E = (\Delta H)^2 / (2 I_w)\), \(\Delta H = |I_w \omega_{after} - I_w \omega_{before}|\), \(E\) in joules. Applied only when **inside** the viewing gate (same step as slide reward).

## Code map

- Constants: `backend/environment_definition/constants/AUTONOMOUS_CONTROL_REWARD.py`
- Reward API: `backend/autonomous_control/reward.py`
- Action adapter / dummy policy: `backend/autonomous_control/action_adapter.py`, `backend/autonomous_control/controller_agent.py`
