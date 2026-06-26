"""Shared baseline overflight controller tick (nb07 rollout + warmup episodes)."""

from __future__ import annotations

from typing import Any

import numpy as np

from simulation.state_types import SimulationTimestepState
from simulation.stepper import SimulationStepper
from simulation.take_picture import TakePictureBudget


def baseline_policy_action_to_gym_vector(
    action: Any,
    *,
    torque_request_nm: float | None = None,
) -> np.ndarray:
    """Map baseline policy action to MPO-compatible 2D gym vector."""
    tau = float(
        torque_request_nm if torque_request_nm is not None else action.torque_request_nm
    )
    shutter_gym = 1.0 if bool(action.take_picture) else -1.0
    return np.array([tau, shutter_gym], dtype=np.float32)


def baseline_overflight_controller_tick(
    *,
    policy: Any,
    stepper: SimulationStepper,
    state: SimulationTimestepState,
    sat_pos_xy_km: np.ndarray,
    omega_orbit_rad_s: float,
    sat_inertia: Any,
    tau_max_nm: float,
    budget: TakePictureBudget | None,
) -> tuple[Any, np.ndarray, bool]:
    """
    One controller update: phase machine, torque request, optional shutter.

    Returns ``(policy_action, gym_vector shape (2,), take_picture_cmd)``.
    """
    policy.update_pointing_phase(float(state.theta_orbit_rad))
    obs = policy.observe(state, sat_pos_xy_km=sat_pos_xy_km)
    action = policy.act(
        obs,
        step_idx=int(state.step_idx),
        state=state,
        sat_pos_xy_km=sat_pos_xy_km,
        omega_orbit_rad_s=float(omega_orbit_rad_s),
        sat_inertia=sat_inertia,
        tau_max_nm=float(tau_max_nm),
    )
    gym_vector = baseline_policy_action_to_gym_vector(action)
    take_picture_cmd = bool(action.take_picture)
    return action, gym_vector, take_picture_cmd


def apply_baseline_shutter_if_requested(
    *,
    stepper: SimulationStepper,
    take_picture_cmd: bool,
    budget: TakePictureBudget | None,
) -> int | None:
    """Apply shutter capture at the current step index after ``stepper.step``."""
    if not take_picture_cmd or budget is None:
        return None
    cmd_step = int(stepper.current_index)
    stepper.apply_shutter_capture(cmd_step, budget)
    return cmd_step
