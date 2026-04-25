from __future__ import annotations

from typing import Any

from .attitude_dynamics import AttitudeState2D, propagate_reaction_wheel_attitude_2d
from .reaction_wheel import ReactionWheel


class DynamicsKernel:
    @staticmethod
    def propagate(
        *,
        state: AttitudeState2D,
        wheel_torque_cmd_nm: float,
        reaction_wheel: ReactionWheel,
        sat_inertia: Any,
        wheel_inertia: Any,
        dt: Any,
        ureg: Any,
    ) -> tuple[AttitudeState2D, Any]:
        wheel_torque_cmd = (-float(wheel_torque_cmd_nm)) * ureg.N * ureg.m
        tau_applied = reaction_wheel.compute_applied_torque(state=state, tau_cmd=wheel_torque_cmd)
        next_state = propagate_reaction_wheel_attitude_2d(
            state=state,
            wheel_torque=tau_applied,
            sat_inertia=sat_inertia,
            wheel_inertia=wheel_inertia,
            dt=dt,
        )
        return next_state, tau_applied
