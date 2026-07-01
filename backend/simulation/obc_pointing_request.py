"""Nadir-relative pointing command resolution for OBC vector mode."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from environment_definition.constants.ATTITUDE_SAFETY import OFF_NADIR_HARD_LIMIT_DEG
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from simulation.attitude_controller import (
    body_boresight_off_nadir_rad,
    body_pointing_torque_nm,
    default_nadir_pointing_gains,
    nadir_target_angle_rad,
    target_boresight_angle_rad,
    target_boresight_rate_rad_s,
)


def wrap_pi(angle_rad: float) -> float:
    return float(((angle_rad + math.pi) % (2.0 * math.pi)) - math.pi)


def max_safe_rad() -> float:
    """Shared off-nadir command/safety limit [rad] (45° hard limit)."""
    return float(OFF_NADIR_HARD_LIMIT_DEG.to(ureg.rad).magnitude)


def u_to_fn(*, u: float, max_safe_rad_val: float | None = None) -> float:
    """Map normalized command u ∈ [-1, 1] to nadir-relative offset f_n [rad]."""
    limit = float(max_safe_rad_val if max_safe_rad_val is not None else max_safe_rad())
    return float(np.clip(u, -1.0, 1.0) * limit)


def fn_to_theta_req(*, theta_nadir_rad: float, fn_rad: float) -> float:
    return wrap_pi(float(theta_nadir_rad) + float(fn_rad))


def u_to_theta_req(
    *,
    u: float,
    theta_orbit_rad: float,
    max_safe_rad_val: float | None = None,
) -> float:
    theta_nadir = nadir_target_angle_rad(float(theta_orbit_rad))
    fn = u_to_fn(u=u, max_safe_rad_val=max_safe_rad_val)
    return fn_to_theta_req(theta_nadir_rad=theta_nadir, fn_rad=fn)


def theta_target_to_u(
    *,
    theta_target_rad: float,
    theta_orbit_rad: float,
    max_safe_rad_val: float | None = None,
) -> float:
    """Convert absolute θ_target to normalized u ∈ [-1, 1]."""
    limit = float(max_safe_rad_val if max_safe_rad_val is not None else max_safe_rad())
    if limit <= 0.0:
        raise ValueError("max_safe_rad must be positive")
    theta_nadir = nadir_target_angle_rad(float(theta_orbit_rad))
    fn = wrap_pi(float(theta_target_rad) - theta_nadir)
    return float(np.clip(fn / limit, -1.0, 1.0))


def is_outside_safe_bounds(
    *,
    theta_req_rad: float,
    sat_pos_xy_km: np.ndarray,
    max_safe_rad_val: float | None = None,
) -> bool:
    limit = float(max_safe_rad_val if max_safe_rad_val is not None else max_safe_rad())
    off = body_boresight_off_nadir_rad(
        body_z_angle_rad=float(theta_req_rad),
        sat_pos_xy_km=np.asarray(sat_pos_xy_km, dtype=float),
    )
    return off >= limit - 1e-9


def baseline_theta_target_rad(
    policy: Any,
    state: Any,
    *,
    sat_pos_xy_km: np.ndarray,
) -> float:
    """Mirror ``SequentialTargetBaselinePolicy`` PD target angle selection."""
    if str(getattr(policy, "pointing_phase", "nadir")) == "nadir":
        return nadir_target_angle_rad(float(state.theta_orbit_rad))
    anchor = np.asarray(policy.active_anchor(), dtype=float)
    return float(target_boresight_angle_rad(sat_pos_xy_km, anchor))


def baseline_pointing_u(
    policy: Any,
    state: Any,
    *,
    sat_pos_xy_km: np.ndarray,
    max_safe_rad_val: float | None = None,
) -> float:
    theta_target = baseline_theta_target_rad(policy, state, sat_pos_xy_km=sat_pos_xy_km)
    return theta_target_to_u(
        theta_target_rad=theta_target,
        theta_orbit_rad=float(state.theta_orbit_rad),
        max_safe_rad_val=max_safe_rad_val,
    )


def baseline_omega_target_rad_s(
    policy: Any,
    state: Any,
    *,
    sat_pos_xy_km: np.ndarray,
    omega_orbit_rad_s: float,
) -> float:
    """Mirror baseline PD feedforward: nadir hold uses orbit rate, engage uses target rate."""
    if str(getattr(policy, "pointing_phase", "nadir")) == "nadir":
        return float(omega_orbit_rad_s)
    anchor = np.asarray(policy.active_anchor(), dtype=float)
    return float(
        target_boresight_rate_rad_s(
            sat_pos_xy_km=np.asarray(sat_pos_xy_km, dtype=float),
            omega_orbit_rad_s=float(omega_orbit_rad_s),
            ground_target_xy_km=anchor,
        )
    )


@dataclass
class ObcPointingDiagnostics:
    hold_last_count: int = 0
    last_u: float = 0.0
    last_theta_req_rad: float = 0.0
    last_theta_used_rad: float = 0.0
    last_off_nadir_rad: float = 0.0

    @property
    def reference_clamp_count(self) -> int:
        """Deprecated alias retained for experiment KPI compatibility."""
        return self.hold_last_count


@dataclass
class ObcPointingResolver:
    """Hold-last-valid OBC: u → f_n → θ_req → PD → τ."""

    tau_max_nm: float
    sat_inertia: Any
    max_safe_rad_val: float = field(default_factory=max_safe_rad)
    diagnostics: ObcPointingDiagnostics = field(default_factory=ObcPointingDiagnostics)
    _last_valid_theta_req_rad: float | None = field(default=None, repr=False)
    _gains: Any = field(default=None, repr=False)

    def reset_episode(self, *, theta_orbit_rad: float) -> None:
        self.diagnostics = ObcPointingDiagnostics()
        self._last_valid_theta_req_rad = nadir_target_angle_rad(float(theta_orbit_rad))

    def _ensure_gains(self) -> Any:
        if self._gains is None:
            self._gains = default_nadir_pointing_gains(
                tau_max_nm=self.tau_max_nm,
                sat_inertia=self.sat_inertia,
            )
        return self._gains

    def resolve_u_to_torque_nm(
        self,
        *,
        u: float,
        theta_orbit_rad: float,
        sat_pos_xy_km: np.ndarray,
        body_z_rad: float,
        omega_sat_rad_s: float,
        omega_orbit_rad_s: float,
        omega_target_rad_s: float | None = None,
    ) -> float:
        u_clipped = float(np.clip(u, -1.0, 1.0))
        self.diagnostics.last_u = u_clipped
        theta_req = u_to_theta_req(
            u=u_clipped,
            theta_orbit_rad=float(theta_orbit_rad),
            max_safe_rad_val=self.max_safe_rad_val,
        )
        self.diagnostics.last_theta_req_rad = theta_req

        sat_xy = np.asarray(sat_pos_xy_km, dtype=float)
        if self._last_valid_theta_req_rad is None:
            self._last_valid_theta_req_rad = nadir_target_angle_rad(float(theta_orbit_rad))

        if is_outside_safe_bounds(
            theta_req_rad=theta_req,
            sat_pos_xy_km=sat_xy,
            max_safe_rad_val=self.max_safe_rad_val,
        ):
            theta_used = float(self._last_valid_theta_req_rad)
            self.diagnostics.hold_last_count += 1
        else:
            theta_used = float(theta_req)
            self._last_valid_theta_req_rad = theta_used

        self.diagnostics.last_theta_used_rad = theta_used
        self.diagnostics.last_off_nadir_rad = body_boresight_off_nadir_rad(
            body_z_angle_rad=theta_used,
            sat_pos_xy_km=sat_xy,
        )

        omega_ff = (
            float(omega_target_rad_s)
            if omega_target_rad_s is not None
            else float(omega_orbit_rad_s)
        )
        return float(
            body_pointing_torque_nm(
                body_z_rad=float(body_z_rad),
                omega_sat_rad_s=float(omega_sat_rad_s),
                theta_target_rad=theta_used,
                omega_target_rad_s=omega_ff,
                tau_max_nm=self.tau_max_nm,
                gains=self._ensure_gains(),
            )
        )


__all__ = [
    "ObcPointingDiagnostics",
    "ObcPointingResolver",
    "baseline_omega_target_rad_s",
    "baseline_pointing_u",
    "baseline_theta_target_rad",
    "fn_to_theta_req",
    "is_outside_safe_bounds",
    "max_safe_rad",
    "theta_target_to_u",
    "u_to_fn",
    "u_to_theta_req",
    "wrap_pi",
]
