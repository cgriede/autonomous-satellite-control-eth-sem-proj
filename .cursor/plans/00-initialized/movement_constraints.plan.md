# Movement constraints (notebook 03)

## Problem

Reaction-wheel rate cutoff does not enforce off-nadir envelope, taper, safe-mode recovery, or agent lockout.

## Outcome

`AttitudeSafetyController` + `DelayedMaxTorquePolicy` verification; required MP4 `movement_constraints_delayed_max.mp4`.

## Acceptance

1. Braking distance at 3°/s ≈ 24.6°; activation ≈ 20.4°.
2. Delayed max: 5 s coast → +τ_max → warnings → safe-mode takeover → envelope ≤ 45°.
3. Delayed half: same delay, 0.5 τ_max.
4. E2e determinism on safe-mode enter step.
5. Unit tests green.
6. MP4 gate: coast, violation ~5 s, takeover/recovery visible.

## Non-goals

Clouds, reward shaping, RL training, capture-image action.

## Gates

| Gate | Home |
|------|------|
| Unit | `test_attitude_controller.py` |
| E2E | `test_movement_constraints_sim_integration.py` |
| Human | `03-movement_constraints.ipynb` + artifacts MP4 |

## Human UX (4b)

Required: `backend/notebooks/s01/artifacts/movement_constraints_delayed_max.mp4` — coast, violation, takeover/recovery confirmed.
