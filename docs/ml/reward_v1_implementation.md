# Autonomous control reward v1 — implementation notes

**Version:** 0.2  
**Date:** 2026-04-30

## Distance-band reward definition

Let \(d = |r_t - r_{sat}|\), with optimal range \(d_{op}\), in-band threshold \(d_{th}\), and
outer viewing gate \(d_{view}\).

Piecewise primary objective term:

- If \(d > d_{view}\): \(R_1 = 0\)
- Else if \(d > d_{th}\): \(R_1 = 0\)
- Else if \(d \le d_{th}\) and target not visible (or no picture): \(R_1 = -100\)
- Else (in-band and visible):
  - \(d_{eff} = \max(d, d_{op})\)
  - \(\text{scalar} = \frac{d_{th} - d_{eff}}{d_{th} - d_{op}}\)
  - \(R_1 = -100 + 100 \cdot \text{scalar}\)

This guarantees \(R_1 = 0\) at \(d = d_{op}\) and \(R_1 = -100\) at \(d = d_{th}\).

## Project deltas

1. **Outer viewing gate** (`CAMERA_VIEWING_DISTANCE_THRESHOLD` in `backend/environment_definition/constants/AUTONOMOUS_CONTROL_REWARD.py`): if \(|r_t - r_{sat}|\) is **greater** than this threshold, reward is **0** (distance-band term, no-picture penalty, and energy are suppressed). This matches “far away, analyze clouds / do not punish idle behavior.”

2. **Distance proxy:** \(|r_t - r_{sat}|\) is modeled as a single **slant / ground-range** length quantity in Pint (typically kilometers in config, converted to meters inside `reward_v1_distance_band_reward`). Callers should use the same geometric definition as the mission sim (e.g. 2D planar distance in the simulation plane vs geodesic — keep one convention end-to-end).

3. **Band handling:** If distance \(d < d_{op}\), the distance-band term clamps to \(d_{\mathrm{eff}} = d_{op}\), so the primary objective stays at \(0\) (best distance score).

4. **Energy penalty:** Subtract \(k_E \cdot E\) with \(k_E =\) `REWARD_ENERGY_LINEAR_COEFFICIENT` and  
   \(E = (\Delta H)^2 / (2 I_w)\), \(\Delta H = |I_w \omega_{after} - I_w \omega_{before}|\), \(E\) in joules. Applied only when **inside** the viewing gate.

## Code map

- Constants: `backend/environment_definition/constants/AUTONOMOUS_CONTROL_REWARD.py`
- Reward API: `backend/autonomous_control/reward.py`
- Action adapter / dummy policy: `backend/autonomous_control/action_adapter.py`, `backend/autonomous_control/controller_agent.py`
