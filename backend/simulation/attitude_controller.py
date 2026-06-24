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


class SafeIntervalKind(Enum):
    """Predefined safe-mode recovery intervals (agent torque rejected)."""

    BRAKE = auto()
    CRUISE = auto()
    SETTLE = auto()
    LOCKOUT = auto()


@dataclass(frozen=True)
class SafeModeInterval:
    kind: SafeIntervalKind


DEFAULT_SAFE_MODE_SEQUENCE: tuple[SafeModeInterval, ...] = (
    SafeModeInterval(SafeIntervalKind.BRAKE),
    SafeModeInterval(SafeIntervalKind.CRUISE),
    SafeModeInterval(SafeIntervalKind.SETTLE),
    SafeModeInterval(SafeIntervalKind.LOCKOUT),
)


@dataclass(frozen=True)
class AttitudeSafetyConfig:
    off_nadir_hard_limit: Any = OFF_NADIR_HARD_LIMIT_DEG
    safe_mode_cruise_rate: Any = SAFE_MODE_CRUISE_RATE_DEG_S
    lockout_s: Any = SAFE_MODE_LOCKOUT_S
    nadir_recovery_tolerance: Any = NADIR_RECOVERY_TOLERANCE_DEG
    decel_start: Any = SAFE_MODE_DECEL_START_DEG
    omega_stop: Any = SAFE_MODE_OMEGA_STOP
    tau_max: Any | None = None
    safe_mode_sequence: tuple[SafeModeInterval, ...] = DEFAULT_SAFE_MODE_SEQUENCE


@dataclass
class ArbitrateResult:
    tau_out_nm: float
    events: list[str] = field(default_factory=list)
    off_nadir_rad: float = 0.0
    agent_cmd_nm: float = 0.0
    agent_applied: bool = True


@dataclass(frozen=True)
class NadirPointingGains:
    kp: float
    kd: float


def default_nadir_pointing_gains(*, tau_max_nm: float, sat_inertia: Any) -> NadirPointingGains:
    """Tune PD gains from torque limit, decel band, and satellite inertia."""
    decel_start_rad = float(SAFE_MODE_DECEL_START_DEG.to(ureg.rad).magnitude)
    inertia_kg_m2 = float(sat_inertia.to(ureg.kg * ureg.m**2).magnitude)
    kp = float(tau_max_nm) / max(decel_start_rad, 1e-6)
    kd = 2.0 * math.sqrt(max(kp * inertia_kg_m2, 0.0))
    return NadirPointingGains(kp=kp, kd=kd)


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


def target_boresight_angle_rad(
    sat_pos_xy_km: np.ndarray,
    ground_target_xy_km: np.ndarray,
) -> float:
    """In-plane boresight angle from satellite toward a fixed ground target."""
    sat = np.asarray(sat_pos_xy_km, dtype=float).reshape(2)
    tgt = np.asarray(ground_target_xy_km, dtype=float).reshape(2)
    vec = tgt - sat
    return float(math.atan2(vec[1], vec[0]))


def target_boresight_rate_rad_s(
    *,
    sat_pos_xy_km: np.ndarray,
    omega_orbit_rad_s: float,
    ground_target_xy_km: np.ndarray,
) -> float:
    """Time derivative of ``target_boresight_angle_rad`` for circular orbit motion."""
    sat = np.asarray(sat_pos_xy_km, dtype=float).reshape(2)
    tgt = np.asarray(ground_target_xy_km, dtype=float).reshape(2)
    vx = float(tgt[0] - sat[0])
    vy = float(tgt[1] - sat[1])
    r2 = vx * vx + vy * vy
    if r2 <= 1e-18:
        return 0.0
    orbit_r = float(np.linalg.norm(sat))
    if orbit_r <= 1e-9:
        return 0.0
    theta = math.atan2(sat[1], sat[0])
    dvx = orbit_r * float(omega_orbit_rad_s) * math.sin(theta)
    dvy = -orbit_r * float(omega_orbit_rad_s) * math.cos(theta)
    return float((vx * dvy - vy * dvx) / r2)


def _wrap_pi(angle_rad: float) -> float:
    return float(((angle_rad + math.pi) % (2.0 * math.pi)) - math.pi)


def body_pointing_torque_nm(
    *,
    body_z_rad: float,
    omega_sat_rad_s: float,
    theta_target_rad: float,
    omega_target_rad_s: float,
    tau_max_nm: float,
    gains: NadirPointingGains,
    omega_cmd_rad_s: float = 0.0,
) -> float:
    """
    PD body pointing with target-angle feedforward.

    ``omega_cmd_rad_s`` adds a slew rate toward the target on top of feedforward tracking.
    """
    error = _wrap_pi(theta_target_rad - body_z_rad)
    if abs(error) > 1e-9 and abs(omega_cmd_rad_s) > 0.0:
        cmd = abs(omega_cmd_rad_s) * (1.0 if error > 0.0 else -1.0)
    else:
        cmd = 0.0
    omega_des = float(omega_target_rad_s) + cmd
    tau = gains.kp * error + gains.kd * (omega_des - omega_sat_rad_s)
    return float(np.clip(tau, -tau_max_nm, tau_max_nm))


def nadir_pointing_torque_nm(
    *,
    body_z_rad: float,
    omega_sat_rad_s: float,
    theta_orbit_rad: float,
    omega_orbit_rad_s: float,
    omega_cmd_rad_s: float,
    tau_max_nm: float,
    gains: NadirPointingGains,
) -> float:
    """
    Instantaneous-nadir PD with orbit feedforward.

    ``omega_cmd_rad_s`` adds a slew rate toward nadir on top of orbit tracking.
    Use 0 for brake, settle, and lockout hold.
    """
    return body_pointing_torque_nm(
        body_z_rad=body_z_rad,
        omega_sat_rad_s=omega_sat_rad_s,
        theta_target_rad=nadir_target_angle_rad(theta_orbit_rad),
        omega_target_rad_s=float(omega_orbit_rad_s),
        tau_max_nm=tau_max_nm,
        gains=gains,
        omega_cmd_rad_s=omega_cmd_rad_s,
    )


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


def _interval_event_name(kind: SafeIntervalKind) -> str:
    return f"SAFE_MODE_INTERVAL_{kind.name}"


@dataclass
class AttitudePointingController:
    """
    OBC body pointing: nadir hold or ground-target track via the same PD stack as safe-mode nadir.

    Replaces agent torque each step when enabled on the stepper.
    """

    mode: str
    sat_inertia: Any
    tau_max_nm: float
    ground_target_xy_km: tuple[float, float] | None = None
    _nadir_gains: NadirPointingGains | None = None

    def reset_episode(self) -> None:
        self._nadir_gains = None

    def set_pointing_mode(self, mode: str) -> None:
        """Switch OBC pointing mode between ``nadir`` and ``target`` during an episode."""
        m = str(mode).lower()
        if m not in ("nadir", "target"):
            raise ValueError(f"Unsupported OBC pointing mode: {mode!r}")
        self.mode = m

    def set_ground_target_xy_km(self, xy: tuple[float, float]) -> None:
        """Update the OBC ground-target anchor (``obc_pointing_mode='target'`` only)."""
        if str(self.mode).lower() != "target":
            raise ValueError("set_ground_target_xy_km requires obc_pointing_mode='target'.")
        arr = np.asarray(xy, dtype=float).reshape(2)
        self.ground_target_xy_km = (float(arr[0]), float(arr[1]))

    def _gains(self) -> NadirPointingGains:
        if self._nadir_gains is None:
            self._nadir_gains = default_nadir_pointing_gains(
                tau_max_nm=float(self.tau_max_nm),
                sat_inertia=self.sat_inertia,
            )
        return self._nadir_gains

    def compute_torque_nm(
        self,
        *,
        body_z_rad: float,
        omega_sat_rad_s: float,
        sat_pos_xy_km: np.ndarray,
        theta_orbit_rad: float,
        omega_orbit_rad_s: float,
    ) -> float:
        mode = str(self.mode).lower()
        if mode == "nadir":
            theta_target = nadir_target_angle_rad(theta_orbit_rad)
            omega_target = float(omega_orbit_rad_s)
        elif mode == "target":
            if self.ground_target_xy_km is None:
                raise ValueError("ground_target_xy_km required for obc_pointing_mode='target'.")
            tgt = np.asarray(self.ground_target_xy_km, dtype=float)
            theta_target = target_boresight_angle_rad(sat_pos_xy_km, tgt)
            omega_target = target_boresight_rate_rad_s(
                sat_pos_xy_km=sat_pos_xy_km,
                omega_orbit_rad_s=omega_orbit_rad_s,
                ground_target_xy_km=tgt,
            )
        else:
            raise ValueError(f"Unsupported OBC pointing mode: {self.mode!r}")
        return body_pointing_torque_nm(
            body_z_rad=body_z_rad,
            omega_sat_rad_s=omega_sat_rad_s,
            theta_target_rad=theta_target,
            omega_target_rad_s=omega_target,
            tau_max_nm=float(self.tau_max_nm),
            gains=self._gains(),
            omega_cmd_rad_s=0.0,
        )


@dataclass
class AttitudeSafetyController:
    """
    Torque path: agent request -> arbitrate() -> reaction wheel.

    Normal: pass-through | tapered | (not safe mode).
    Safe mode: ignore agent; run BRAKE -> CRUISE -> SETTLE -> LOCKOUT via nadir mode.
    """

    config: AttitudeSafetyConfig
    sat_inertia: Any
    tau_max_nm: float
    _interval_idx: int | None = None
    _lockout_elapsed_s: float = 0.0
    _safe_mode_entered: bool = False
    _nadir_gains: NadirPointingGains | None = None

    def reset_episode(self) -> None:
        self._interval_idx = None
        self._lockout_elapsed_s = 0.0
        self._safe_mode_entered = False
        self._nadir_gains = None

    def _tau_max_q(self) -> Any:
        if self.config.tau_max is not None:
            return self.config.tau_max
        return float(self.tau_max_nm) * ureg.N * ureg.m

    def _gains(self) -> NadirPointingGains:
        if self._nadir_gains is None:
            self._nadir_gains = default_nadir_pointing_gains(
                tau_max_nm=float(self.tau_max_nm),
                sat_inertia=self.sat_inertia,
            )
        return self._nadir_gains

    def _enter_safe_mode(self, events: list[str]) -> None:
        self._interval_idx = 0
        self._lockout_elapsed_s = 0.0
        self._safe_mode_entered = True
        events.append("SAFE_MODE_TAKEOVER")
        events.append("AGENT_CUT")
        events.append(_interval_event_name(self.config.safe_mode_sequence[0].kind))

    def _nadir_error_rad(self, *, body_z: float, theta_orbit_rad: float) -> float:
        target = nadir_target_angle_rad(theta_orbit_rad)
        return _wrap_pi(target - body_z)

    def _safe_mode_torque(
        self,
        *,
        body_z: float,
        omega_sat: float,
        theta_orbit_rad: float,
        omega_orbit_rad_s: float,
        off_nadir: float,
        dt_s: float,
        events: list[str],
    ) -> tuple[float, list[str]]:
        if self._interval_idx is None:
            return 0.0, events

        sequence = self.config.safe_mode_sequence
        interval = sequence[self._interval_idx]
        kind = interval.kind
        events.append(_interval_event_name(kind))

        cruise = float(self.config.safe_mode_cruise_rate.to(ureg.rad / ureg.s).magnitude)
        nadir_tol = float(self.config.nadir_recovery_tolerance.to(ureg.rad).magnitude)
        decel_start = float(self.config.decel_start.to(ureg.rad).magnitude)
        omega_stop = float(self.config.omega_stop.to(ureg.rad / ureg.s).magnitude)
        error = self._nadir_error_rad(body_z=body_z, theta_orbit_rad=theta_orbit_rad)
        omega_rel = omega_sat - omega_orbit_rad_s

        if kind == SafeIntervalKind.BRAKE:
            omega_cmd = 0.0
        elif kind == SafeIntervalKind.CRUISE:
            omega_cmd = cruise if abs(error) > nadir_tol else 0.0
        else:
            omega_cmd = 0.0

        tau_out = nadir_pointing_torque_nm(
            body_z_rad=body_z,
            omega_sat_rad_s=omega_sat,
            theta_orbit_rad=theta_orbit_rad,
            omega_orbit_rad_s=omega_orbit_rad_s,
            omega_cmd_rad_s=omega_cmd,
            tau_max_nm=float(self.tau_max_nm),
            gains=self._gains(),
        )

        if kind == SafeIntervalKind.BRAKE and abs(omega_rel) <= omega_stop:
            self._interval_idx += 1
            events.append(_interval_event_name(sequence[self._interval_idx].kind))
        elif kind == SafeIntervalKind.CRUISE and off_nadir <= decel_start:
            self._interval_idx += 1
            events.append(_interval_event_name(sequence[self._interval_idx].kind))
        elif (
            kind == SafeIntervalKind.SETTLE
            and abs(error) <= nadir_tol
            and abs(omega_rel) <= omega_stop
        ):
            self._interval_idx += 1
            self._lockout_elapsed_s = 0.0
            events.append(_interval_event_name(sequence[self._interval_idx].kind))
        elif kind == SafeIntervalKind.LOCKOUT:
            events.append("LOCKOUT_ACTIVE")
            self._lockout_elapsed_s += dt_s
            if self._lockout_elapsed_s >= float(self.config.lockout_s.to(ureg.s).magnitude):
                self._interval_idx = None
                self._lockout_elapsed_s = 0.0
                events.append("SAFE_MODE_EXIT")

        return tau_out, events

    def arbitrate(
        self,
        *,
        tau_cmd_nm: float,
        state: AttitudeState2D,
        sat_pos_xy_km: np.ndarray,
        theta_orbit_rad: float,
        omega_orbit_rad_s: float,
        dt_s: float,
    ) -> ArbitrateResult:
        body_z = float(state.theta.to(ureg.rad).magnitude)
        omega_sat = float(state.omega_sat.to(ureg.rad / ureg.s).magnitude)
        off_nadir = _off_nadir_from_state(body_z_angle_rad=body_z, sat_pos_xy_km=sat_pos_xy_km)
        events: list[str] = []
        agent_cmd = float(tau_cmd_nm)

        if self._interval_idx is not None:
            tau_out, events = self._safe_mode_torque(
                body_z=body_z,
                omega_sat=omega_sat,
                theta_orbit_rad=theta_orbit_rad,
                omega_orbit_rad_s=omega_orbit_rad_s,
                off_nadir=off_nadir,
                dt_s=dt_s,
                events=events,
            )
            return ArbitrateResult(
                tau_out_nm=tau_out,
                events=events,
                off_nadir_rad=off_nadir,
                agent_cmd_nm=agent_cmd,
                agent_applied=False,
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
                omega_orbit_rad_s=omega_orbit_rad_s,
                off_nadir=off_nadir,
                dt_s=dt_s,
                events=events,
            )
            return ArbitrateResult(
                tau_out_nm=tau_out,
                events=events,
                off_nadir_rad=off_nadir,
                agent_cmd_nm=agent_cmd,
                agent_applied=False,
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
                agent_applied=True,
            )

        return ArbitrateResult(
            tau_out_nm=agent_cmd,
            events=events,
            off_nadir_rad=off_nadir,
            agent_cmd_nm=agent_cmd,
            agent_applied=True,
        )

    @property
    def in_safe_mode(self) -> bool:
        return self._interval_idx is not None

    @property
    def safe_mode_entered(self) -> bool:
        return self._safe_mode_entered

    @property
    def current_interval_kind(self) -> SafeIntervalKind | None:
        if self._interval_idx is None:
            return None
        return self.config.safe_mode_sequence[self._interval_idx].kind
