"""OBC fork: torque path (production safety) vs vector path (u → θ_ref → PD → τ)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from environment_definition.constants.ATTITUDE_SAFETY import OFF_NADIR_HARD_LIMIT_DEG
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from simulation.obc_pointing_request import ObcPointingDiagnostics, ObcPointingResolver

from _action_adapter_fork import AttitudeRequestMode

AttitudeRequestMode = AttitudeRequestMode  # re-export


@dataclass
class ObcAttitudeDiagnostics:
    """Experiment-facing diagnostics (aliases production resolver fields)."""

    hold_last_count: int = 0
    last_u: float = 0.0
    last_theta_req_rad: float = 0.0
    last_theta_used_rad: float = 0.0
    last_off_nadir_rad: float = 0.0

    @property
    def last_theta_clamped_rad(self) -> float:
        return self.last_theta_used_rad

    @property
    def reference_clamp_count(self) -> int:
        return self.hold_last_count

    @classmethod
    def from_resolver(cls, diag: ObcPointingDiagnostics) -> ObcAttitudeDiagnostics:
        return cls(
            hold_last_count=int(diag.hold_last_count),
            last_u=float(diag.last_u),
            last_theta_req_rad=float(diag.last_theta_req_rad),
            last_theta_used_rad=float(diag.last_theta_used_rad),
            last_off_nadir_rad=float(diag.last_off_nadir_rad),
        )


@dataclass
class ObcAttitudeRequestContext:
    mode: AttitudeRequestMode
    tau_max_nm: float
    sat_inertia: Any
    diagnostics: ObcAttitudeDiagnostics = field(default_factory=ObcAttitudeDiagnostics)
    _resolver: ObcPointingResolver | None = field(default=None, repr=False)
    _episode_reset_pending: bool = field(default=True, repr=False)

    @property
    def max_safe_rad(self) -> float:
        return float(OFF_NADIR_HARD_LIMIT_DEG.to(ureg.rad).magnitude)

    def _ensure_resolver(self) -> ObcPointingResolver:
        if self._resolver is None:
            self._resolver = ObcPointingResolver(
                tau_max_nm=float(self.tau_max_nm),
                sat_inertia=self.sat_inertia,
            )
        return self._resolver

    def reset_episode(self) -> None:
        self.diagnostics = ObcAttitudeDiagnostics()
        self._episode_reset_pending = True
        if self._resolver is not None:
            self._resolver._last_valid_theta_req_rad = None

    def reset_episode_for_step(self, *, theta_orbit_rad: float) -> None:
        if not self._episode_reset_pending:
            return
        resolver = self._ensure_resolver()
        resolver.reset_episode(theta_orbit_rad=float(theta_orbit_rad))
        self._episode_reset_pending = False
        self._sync_diagnostics()

    def _sync_diagnostics(self) -> None:
        if self._resolver is not None:
            self.diagnostics = ObcAttitudeDiagnostics.from_resolver(self._resolver.diagnostics)

    def resolve_torque_nm(
        self,
        *,
        dim0: float,
        stored_action: np.ndarray,
        stepper: Any,
        ctrl_state: Any,
        dt_s: float,
    ) -> tuple[float, bool]:
        """Map agent dim0 to wheel torque [N·m] and shutter command."""
        _ = dt_s
        shutter_gym = float(stored_action[1]) if len(stored_action) > 1 else -1.0
        from autonomous_control.action_adapter import shutter_cmd_from_gym

        take_picture = shutter_cmd_from_gym(shutter_gym)

        if self.mode == "torque":
            return float(dim0), take_picture

        self.reset_episode_for_step(theta_orbit_rad=float(ctrl_state.theta_orbit_rad))
        resolver = self._ensure_resolver()
        tau = resolver.resolve_u_to_torque_nm(
            u=float(dim0),
            theta_orbit_rad=float(ctrl_state.theta_orbit_rad),
            sat_pos_xy_km=np.asarray(ctrl_state.sat_pos_xy_km, dtype=float),
            body_z_rad=float(ctrl_state.body_z_angle_rad),
            omega_sat_rad_s=float(ctrl_state.omega_sat_rad_s),
            omega_orbit_rad_s=float(stepper._omega_orbit_rad_s),
        )
        self._sync_diagnostics()
        return float(tau), take_picture


def step_wheel_torque(
    stepper: Any,
    *,
    torque_nm: float,
    mode: AttitudeRequestMode,
) -> Any:
    """Step dynamics; vector mode bypasses torque-path AttitudeSafetyController."""
    if mode == "vector":
        safety = stepper._attitude_safety
        stepper._attitude_safety = None
        try:
            return stepper.step(wheel_torque_cmd_nm=float(torque_nm))
        finally:
            stepper._attitude_safety = safety
    return stepper.step(wheel_torque_cmd_nm=float(torque_nm))


def hard_limit_deg() -> float:
    return float(OFF_NADIR_HARD_LIMIT_DEG.to(ureg.deg).magnitude)


__all__ = [
    "ObcAttitudeDiagnostics",
    "ObcAttitudeRequestContext",
    "step_wheel_torque",
    "hard_limit_deg",
]
