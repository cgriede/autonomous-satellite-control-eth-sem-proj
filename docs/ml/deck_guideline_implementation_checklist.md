# Autonomous Controller Deck Guideline Checklist

Source: `docs/Semester project - autonomous sat machine learning.pdf`

## Objective and ML framing

- Objective: maximize useful target observations quickly despite cloud uncertainty.
  - Status: **Partial**
  - Implemented path: RL loop exists in `backend/scripts/train_sat_agent.py` + `backend/autonomous_control/training_runtime.py`.
  - Gap: active cloud-aware decision loop is not yet wired into the Gym training environment.

## State space

- `r_sat(t)` deterministic orbital location
  - Status: **Missing in active Gym RL env**
  - Note: available in renderer simulation (`backend/simulation/run_simulation.py`), not in `SatelliteAttitude2D` training state.
- attitude orientation controllable
  - Status: **Implemented**
  - Path: `backend/environment_definition/environment.py`
- cloud location random
  - Status: **Partial**
  - Path: cloud geometry exists in renderer simulation, not in active RL training state.
- target location fixed
  - Status: **Implemented**
  - Path: target angle represented in env and angle-to-target is in observation.

## Action space

- torque via reaction wheel
  - Status: **Implemented**
  - Path: env action space + reaction wheel dynamics.
- passive observation always
  - Status: **Implicitly implemented**
  - Note: training env currently assumes continuous passive sensing.
- active observation/downlink action
  - Status: **Partial**
  - Path: `AutonomousControllerAction.active_observation` exists but is not used in Gym reward/transition path.

## Reward objectives (v1)

- no-picture / not-visible / beyond-threshold penalties
  - Status: **Partial**
  - Path: implemented in `backend/autonomous_control/reward.py`, not yet the active env reward.
- in-threshold distance scaling toward optimal
  - Status: **Partial**
  - Path: implemented in `backend/autonomous_control/reward.py`.
- secondary objective for avoiding random torque/energy waste
  - Status: **Implemented (proxy)**
  - Path: active env reward penalizes wheel speed and torque use.

## Latest verification-focused updates

- Added hardcoded 10s baseline torque sweep policy: `backend/autonomous_control/controller_baselines.py`.
- Added random baseline policy for comparisons: `backend/autonomous_control/controller_baselines.py`.
- Added controller mode switching to train/eval scripts (`mpo`, `baseline`, `random`).
- Updated training-state observation to include:
  - angle relative to nadir
  - angular velocity
  - angular acceleration
  - angle to target
  - wheel speed (additional safety-relevant term)
- Separated action mapping and safety gating explicitly:
  - mapping: `raw_policy_to_action`
  - safety gate: `apply_rate_safety_gate` (uses reaction wheel cutoff model)
