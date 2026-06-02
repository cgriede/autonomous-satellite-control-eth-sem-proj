"""Attitude safety controller: off-nadir taper, safe-mode takeover, deterministic recovery."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

import numpy as np

from environment_definition.constants.ATTITUDE_SAFETY import (
    NADIR_RECOVERY_TOLERANCE_DEG,
    OFF_NADIR_HARD_LIMIT_DEG,
    SAFE_MODE_CRUISE_RATE_DEG_S,
    SAFE_MODE_DECEL_START_DEG,
    SAFE_MODE_LOCKOUT_S,
    SAFE_MODE_OMEGA_STOP,
)
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from simulation.attitude_dynamics import AttitudeState2D, wrap_angle_to_pi
from utils.units.require_compatible_unit import require_compatible_units


class SafeModePhase(Enum):
    """Predefined recovery sequence (agent torque rejected)."""

    BRAKE = auto()
    SPIN_UP = auto()
    COAST = auto()
    DECEL = auto()
    LOCKOUT = auto()


@dataclass(frozen=True)
class AttitudeSafetyConfig:
    off_nadir_hard_limit: Any = OFF_NADIR_HARD_LIMIT_DEG
    safe_mode_cruise_rate: Any = SAFE_MODE_CRUISE_RATE_DEG_S
    lockout_s: Any = SAFE_MODE_LOCKOUT_S
    nadir_recovery_tolerance: Any = NADIR_RECOVERY_TOLERANCE_DEG
    decel_start: Any = SAFE_MODE_DECEL_START_DEG
    omega_stop: Any = SAFE_MODE_OMEGA_STOP
    tau_max: Any | None = None


@dataclass
class ArbitrateResult:
    tau_out_nm: float
    events: list[str] = field(default_factory=list)
    off_nadir_rad: float = 0.0
    agent_cmd_nm: float = 0.0


def braking_distance_rad(
    *,
    omega_sat: Any,
    tau_max: Any,
    sat_inertia: Any,
) -> float:
    """Kinematic braking angle θ = ω²/(2α), α = τ/I."""
    require_compatible_units(omega_sat, "radian/second", "omega_sat")
    require_compatible_units(tau_max, "newton*meter", "tau_max")
    require_compatible_units(sat_inertia, "kilogram*meter**2", "sat_inertia")
    omega = abs(float(omega_sat.to(ureg.rad / ureg.s).magnitude))
    tau = float(tau_max.to(ureg.N * ureg.m).magnitude)
    inertia = float(sat_inertia.to(ureg.kg * ureg.m**2).magnitude)
    if tau <= 0.0 or inertia <= 0.0:
        return 0.0
    alpha = tau / inertia
    if alpha <= 0.0:
        return 0.0
    return float(omega * omega / (2.0 * alpha))


def torque_taper_scale(*, off_nadir_rad: float, arm_rad: float, hard_rad: float) -> float:
    """Linear scale 1 at arm, 0 at hard."""
    return float(np.clip((hard_rad - off_nadir_rad) / max(hard_rad - arm_rad, 1e-12), 0.0, 1.0))


def safe_mode_activation_angle_rad(
    *,
    off_nadir_limit: Any,
    omega_sat: Any,
    tau_max: Any,
    sat_inertia: Any,
) -> float:
    """θ_arm = θ_hard − θ_brake(|ω|)."""
    hard = float(off_nadir_limit.to(ureg.rad).magnitude)
    brake = braking_distance_rad(omega_sat=omega_sat, tau_max=tau_max, sat_inertia=sat_inertia)
    return max(0.0, hard - brake)


def nadir_target_angle_rad(theta_orbit_rad: float) -> float:
    return float(wrap_angle_to_pi((theta_orbit_rad + math.pi) * ureg.rad).to(ureg.rad).magnitude)


def _wrap_pi(angle_rad: float) -> float:
    return float(((angle_rad + math.pi) % (2.0 * math.pi)) - math.pi)


def _off_nadir_from_state(
    *,
    body_z_angle_rad: float,
    sat_pos_xy_km: np.ndarray,
) -> float:
    sat = np.asarray(sat_pos_xy_km, dtype=float).reshape(2)
    bore = np.array([math.cos(body_z_angle_rad), math.sin(body_z_angle_rad)], dtype=float)
    sat_norm = float(np.linalg.norm(sat))
    if sat_norm <= 0.0:
        return 0.0
    nadir = -sat / sat_norm
    bore_norm = float(np.linalg.norm(bore))
    if bore_norm <= 0.0:
        return 0.0
    bore = bore / bore_norm
    dot = float(np.clip(np.dot(bore, nadir), -1.0, 1.0))
    return float(math.acos(dot))


@dataclass
class AttitudeSafetyController:
    """
    Torque path: agent request -> arbitrate() -> reaction wheel.

    Normal: pass-through | tapered | (not safe mode).
    Safe mode: ignore agent; run BRAKE -> SPIN_UP -> COAST -> DECEL -> LOCKOUT.
    """

    config: AttitudeSafetyConfig
    sat_inertia: Any
    tau_max_nm: float
    _phase: SafeModePhase | None = None
    _lockout_elapsed_s: float = 0.0
    _safe_mode_entered: bool = False

    def reset_episode(self) -> None:
        self._phase = None
        self._lockout_elapsed_s = 0.0
        self._safe_mode_entered = False

    def _tau_max_q(self) -> Any:
        if self.config.tau_max is not None:
            return self.config.tau_max
        return float(self.tau_max_nm) * ureg.N * ureg.m

    def _enter_safe_mode(self, events: list[str]) -> None:
        self._phase = SafeModePhase.BRAKE
        self._safe_mode_entered = True
        events.append("SAFE_MODE_TAKEOVER")
        events.append("SAFE_MODE_PHASE_BRAKE")

    def arbitrate(
        self,
        *,
        tau_cmd_nm: float,
        state: AttitudeState2D,
        sat_pos_xy_km: np.ndarray,
        theta_orbit_rad: float,
        dt_s: float,
    ) -> ArbitrateResult:
        body_z = float(state.theta.to(ureg.rad).magnitude)
        omega_sat = float(state.omega_sat.to(ureg.rad / ureg.s).magnitude)
        off_nadir = _off_nadir_from_state(body_z_angle_rad=body_z, sat_pos_xy_km=sat_pos_xy_km)
        events: list[str] = []
        agent_cmd = float(tau_cmd_nm)

        if self._phase is not None:
            tau_out, events = self._safe_mode_torque(
                body_z=body_z,
                omega_sat=omega_sat,
                theta_orbit_rad=theta_orbit_rad,
                off_nadir=off_nadir,
                dt_s=dt_s,
                events=events,
            )
            return ArbitrateResult(
                tau_out_nm=tau_out,
                events=events,
                off_nadir_rad=off_nadir,
                agent_cmd_nm=agent_cmd,
            )

        hard = float(self.config.off_nadir_hard_limit.to(ureg.rad).magnitude)
        brake = braking_distance_rad(
            omega_sat=state.omega_sat,
            tau_max=self._tau_max_q(),
            sat_inertia=self.sat_inertia,
        )
        arm = max(0.0, hard - brake)

        predict_violation = (off_nadir + brake) >= hard - 1e-9
        if predict_violation or off_nadir >= hard:
            self._enter_safe_mode(events)
            tau_out, events = self._safe_mode_torque(
                body_z=body_z,
                omega_sat=omega_sat,
                theta_orbit_rad=theta_orbit_rad,
                off_nadir=off_nadir,
                dt_s=dt_s,
                events=events,
            )
            return ArbitrateResult(
                tau_out_nm=tau_out,
                events=events,
                off_nadir_rad=off_nadir,
                agent_cmd_nm=agent_cmd,
            )

        if off_nadir >= arm:
            scale = torque_taper_scale(off_nadir_rad=off_nadir, arm_rad=arm, hard_rad=hard)
            tau_out = agent_cmd * scale
            if abs(agent_cmd) > 1e-9 and scale < 0.999:
                events.append("SAFETY_WARNING")
            return ArbitrateResult(
                tau_out_nm=tau_out,
                events=events,
                off_nadir_rad=off_nadir,
                agent_cmd_nm=agent_cmd,
            )

        return ArbitrateResult(
            tau_out_nm=agent_cmd,
            events=events,
            off_nadir_rad=off_nadir,
            agent_cmd_nm=agent_cmd,
        )

    def _torque_toward_nadir(self, error_rad: float, magnitude_scale: float = 1.0) -> float:
        """Positive cmd_nm increases body_z; use sign(error) to reduce pointing error."""
        if abs(error_rad) < 1e-9:
            return 0.0
        sign = 1.0 if error_rad > 0.0 else -1.0
        return sign * float(self.tau_max_nm) * magnitude_scale

    def _safe_mode_torque(
        self,
        *,
        body_z: float,
        omega_sat: float,
        theta_orbit_rad: float,
        off_nadir: float,
        dt_s: float,
        events: list[str],
    ) -> tuple[float, list[str]]:
        target = nadir_target_angle_rad(theta_orbit_rad)
        error = _wrap_pi(target - body_z)
        cruise = float(self.config.safe_mode_cruise_rate.to(ureg.rad / ureg.s).magnitude)
        nadir_tol = float(self.config.nadir_recovery_tolerance.to(ureg.rad).magnitude)
        decel_start = float(self.config.decel_start.to(ureg.rad).magnitude)
        omega_stop = float(self.config.omega_stop.to(ureg.rad / ureg.s).magnitude)
        tau_lim = float(self.tau_max_nm)
        cruise_band = max(cruise * 0.2, omega_stop)

        if self._phase == SafeModePhase.LOCKOUT:
            events.append("LOCKOUT_ACTIVE")
            self._lockout_elapsed_s += dt_s
            if self._lockout_elapsed_s >= float(self.config.lockout_s.to(ureg.s).magnitude):
                self._phase = None
                self._lockout_elapsed_s = 0.0
                events.append("SAFE_MODE_EXIT")
            return 0.0, events

        if self._phase == SafeModePhase.BRAKE:
            events.append("SAFE_MODE_PHASE_BRAKE")
            if abs(omega_sat) <= omega_stop:
                self._phase = SafeModePhase.SPIN_UP
                events.append("SAFE_MODE_PHASE_SPIN_UP")
                return self._torque_toward_nadir(error, 1.0), events
            return (-math.copysign(tau_lim, omega_sat) if abs(omega_sat) > 1e-12 else 0.0), events

        if self._phase in (SafeModePhase.SPIN_UP, SafeModePhase.COAST):
            events.append(
                "SAFE_MODE_PHASE_COAST"
                if self._phase == SafeModePhase.COAST
                else "SAFE_MODE_PHASE_SPIN_UP"
            )
            if off_nadir <= decel_start:
                self._phase = SafeModePhase.DECEL
                events.append("SAFE_MODE_PHASE_DECEL")
                return self._torque_toward_nadir(error, 0.5), events
            if off_nadir > decel_start:
                return self._torque_toward_nadir(error, 1.0), events
            desired_omega = math.copysign(cruise, error)
            if omega_sat * desired_omega < 0.0 or abs(omega_sat) < abs(desired_omega) - cruise_band:
                return self._torque_toward_nadir(error, 1.0), events
            if abs(omega_sat) > abs(desired_omega) + cruise_band:
                return -math.copysign(tau_lim, omega_sat - desired_omega), events
            self._phase = SafeModePhase.COAST
            return 0.0, events

        if self._phase == SafeModePhase.DECEL:
            events.append("SAFE_MODE_PHASE_DECEL")
            if abs(omega_sat) > omega_stop:
                return (-math.copysign(tau_lim, omega_sat) if abs(omega_sat) > 1e-12 else 0.0), events
            if abs(error) <= nadir_tol and off_nadir <= decel_start:
                self._phase = SafeModePhase.LOCKOUT
                self._lockout_elapsed_s = 0.0
                events.append("SAFE_MODE_PHASE_LOCKOUT")
                return 0.0, events
            return self._torque_toward_nadir(error, 0.5), events

        return 0.0, events

    @property
    def in_safe_mode(self) -> bool:
        return self._phase is not None

    @property
    def safe_mode_entered(self) -> bool:
        return self._safe_mode_entered
