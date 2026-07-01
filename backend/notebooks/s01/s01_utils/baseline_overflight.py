"""S01 baseline overflight: sequential dummy pointing policy + capture evaluation."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np

from typing import Any

from environment_definition.constants.MISSION import LON_GLOBAL, ObservationTargetArea
from environment_definition.constants.SATELLITE import MAX_PRIMARY_CAPTURES_PER_ORBIT
from environment_definition.constants.SIMULATION import (
    AttitudeRequestMode,
    Cloud,
    GeodeticLonLat,
    OBSERVATION_TARGET,
    SimulationConfig,
    training_episode_simulation_config,
)
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from environment_definition.mission_profiles.s01_multiple_targets_fwd_fish import build_setup
from environment_definition.constants.ATTITUDE_SAFETY import OFF_NADIR_HARD_LIMIT_DEG
from environment_definition.constants.SATELLITE import REACTION_WHEEL_MAX_TORQUE
from simulation.attitude_controller import (
    NadirPointingGains,
    body_pointing_torque_nm,
    default_nadir_pointing_gains,
    nadir_pointing_torque_nm,
    target_boresight_angle_rad,
    target_boresight_rate_rad_s,
    target_pointing_safe_for_engage,
)
from simulation.obc_pointing_request import baseline_omega_target_rad_s
from simulation.state_types import SimulationStateSeries, SimulationTimestepState
from simulation.stepper_factory import build_stepper
from simulation.take_picture import TakePictureBudget, TakePictureConfig
from utils.geometry.mission_stripe_disk import (
    target_areas_disk_phi_bounds_deg,
    target_areas_midpoint_disk_xy_km_on_sphere,
    target_areas_track_offset_ranges_deg,
)
from utils.geometry.orbit_disk_polar_meridian import track_offset_deg_from_disk_xy_km
from utils.geometry.orbit_disk_wgs84 import disk_xy_km_to_geodetic_deg
from utils.geometry.polar_meridian_track import (
    MeridianTargetSegment,
    build_target_grid_polar_meridian,
    lat_deg_from_track_offset_deg,
)

from s01_utils.cloud_formation import cloud_formation_generator
from s01_utils.take_picture_verification import CaptureResult, evaluate_capture_schedule

BASELINE_N_TARGETS = 50
BASELINE_TARGET_SIZE_KM = 15
BASELINE_SPACING_KM = 40
BASELINE_ANCHOR_LAT_DEG = 80.0
BASELINE_MISSION_SEED = 0
BASELINE_LEAD_MARGIN_DEG = 20.0
DEFAULT_TRACKING_THRESHOLD_DEG = 15.0
MIN_CAPTURE_QUALITY = 0.25


# Baseline cloud formation: rainforest-style clouds seeded along the target-grid corridor
# (same canonical generator as notebook 02). Bounds are pint-backed (km).
BASELINE_CLOUD_SEED = 0
BASELINE_CLOUD_NUMBER_BOUNDS = (15, 30)
BASELINE_CLOUD_RANGE_BOUNDS = (1, 80) * ureg.km
BASELINE_CLOUD_BASE_ALTITUDE_BOUNDS = (4, 12) * ureg.km
BASELINE_CLOUD_THICKNESS_BOUNDS = (1, 16) * ureg.km
BASELINE_CLOUD_MAX_TOP_ALTITUDE = 20 * ureg.km


def target_area_view_anchor_disk_xy_km(
    area: ObservationTargetArea,
    *,
    earth_radius_km: float,
) -> tuple[float, float]:
    """Disk (x, z) anchor [km] for a single target area midpoint."""
    xy = target_areas_midpoint_disk_xy_km_on_sphere(
        (area,),
        earth_radius_km=float(earth_radius_km),
    )
    return (float(xy[0]), float(xy[1]))


def _target_leading_phi_lo_deg(area: ObservationTargetArea) -> float:
    phi_lo, phi_hi = target_areas_disk_phi_bounds_deg((area,))[0]
    return float(min(phi_lo, phi_hi))


def _target_trailing_phi_hi_deg(area: ObservationTargetArea) -> float:
    phi_lo, phi_hi = target_areas_disk_phi_bounds_deg((area,))[0]
    return float(max(phi_lo, phi_hi))


def _nadir_ground_xy_km(sat_pos_xy_km: np.ndarray, *, earth_radius_km: float) -> tuple[float, float]:
    sat = np.asarray(sat_pos_xy_km, dtype=float).reshape(2)
    norm = float(np.linalg.norm(sat))
    if norm <= 0.0:
        return (0.0, float(earth_radius_km))
    scale = float(earth_radius_km) / norm
    return (float(sat[0] * scale), float(sat[1] * scale))


def build_baseline_target_segments(
    *, n_targets: int = BASELINE_N_TARGETS
) -> list[MeridianTargetSegment]:
    return build_target_grid_polar_meridian(
        anchor_lat=BASELINE_ANCHOR_LAT_DEG * ureg.deg,
        anchor_lon=LON_GLOBAL,
        n_targets=int(n_targets),
        target_size=BASELINE_TARGET_SIZE_KM * ureg.km,
        spacing=BASELINE_SPACING_KM * ureg.km,
    )


def build_baseline_target_areas(*, n_targets: int = BASELINE_N_TARGETS) -> tuple[ObservationTargetArea, ...]:
    segments = build_baseline_target_segments(n_targets=n_targets)
    return tuple(s.to_observation_target_area() for s in segments)


def build_baseline_clouds(
    segments: list[MeridianTargetSegment],
    *,
    seed: int = BASELINE_CLOUD_SEED,
) -> tuple[Cloud, ...]:
    """Seeded clouds along the target-grid corridor (first leading edge -> last trailing edge)."""
    if not segments:
        return ()
    first, last = segments[0], segments[-1]
    formation_start = GeodeticLonLat(
        lat=lat_deg_from_track_offset_deg(first.track_offset_lo_deg) * ureg.deg,
        lon=first.endpoint_lon_deg(which="min") * ureg.deg,
    )
    formation_end = GeodeticLonLat(
        lat=lat_deg_from_track_offset_deg(last.track_offset_hi_deg) * ureg.deg,
        lon=last.endpoint_lon_deg(which="max") * ureg.deg,
    )
    clouds = cloud_formation_generator(
        formation_start=formation_start,
        formation_end=formation_end,
        cloud_number_bounds=BASELINE_CLOUD_NUMBER_BOUNDS,
        cloud_range_bounds=BASELINE_CLOUD_RANGE_BOUNDS,
        cloud_base_altitude_bounds=BASELINE_CLOUD_BASE_ALTITUDE_BOUNDS,
        cloud_thickness_bounds=BASELINE_CLOUD_THICKNESS_BOUNDS,
        max_top_altitude=BASELINE_CLOUD_MAX_TOP_ALTITUDE,
        rng=np.random.default_rng(int(seed)),
    )
    return tuple(clouds)


def build_baseline_overflight_setup(
    *,
    seed: int = BASELINE_MISSION_SEED,
    n_targets: int = BASELINE_N_TARGETS,
    cloud_seed: int = BASELINE_CLOUD_SEED,
):
    """Full s01 overflight: 50-target grid with seeded clouds over the target corridor."""
    segments = build_baseline_target_segments(n_targets=n_targets)
    target_areas = tuple(s.to_observation_target_area() for s in segments)
    clouds = build_baseline_clouds(segments, seed=cloud_seed)
    return replace(
        build_setup(seed=seed, include_cameras=True),
        target_areas=target_areas,
        clouds=clouds,
    )


def baseline_simulation_config() -> SimulationConfig:
    """Deprecated: baseline overflight uses ``training_episode_simulation_config``."""
    raise RuntimeError(
        "baseline_simulation_config() is removed. "
        "Use training_episode_simulation_config(torque_policy_label='sequential_target_baseline')."
    )


@dataclass(frozen=True)
class BaselinePolicyObservation:
    active_target_index: int
    pointing_phase: str
    target_boresight_angles_rad: np.ndarray
    body_z_angle_rad: float
    target_visible_in_strip: bool
    sat_subpoint_lat_deg: float
    sat_track_offset_deg: float
    camera_image_quality: float


@dataclass(frozen=True)
class BaselinePolicyAction:
    torque_request_nm: float
    take_picture: bool


@dataclass
class SequentialTargetBaselinePolicy:
    """
    Scripted baseline: nadir coast until the orbit-φ window opens **and** target bearing
    is within attitude-safety reach, then target engage.

    Emits PD torque requests (same helpers as AttitudePointingController) plus shutter
    commands on the training stack — policy requests only; safety applies torque.

    ``capture_targets`` lists which target indices this episode images, in order.
    """

    target_anchors: tuple[tuple[float, float], ...]
    target_areas: tuple[ObservationTargetArea, ...]
    target_leading_phi_lo_deg: tuple[float, ...]
    target_trailing_phi_hi_deg: tuple[float, ...]
    target_track_offset_ranges_deg: tuple[tuple[float, float], ...] | None = None
    lead_margin_deg: float = BASELINE_LEAD_MARGIN_DEG
    tracking_threshold_deg: float = DEFAULT_TRACKING_THRESHOLD_DEG
    pointing_phase: str = "nadir"
    active_target_index: int = 0
    capture_targets: tuple[int, ...] | None = None
    _capture_i: int = 0
    cmd_steps: list[int] | None = None
    _shuttered: set[int] | None = None
    _pointing_gains: NadirPointingGains | None = None
    _phi_window_skipped: set[int] | None = None

    def __post_init__(self) -> None:
        if self.cmd_steps is None:
            self.cmd_steps = []
        if self._shuttered is None:
            self._shuttered = set()
        if self._phi_window_skipped is None:
            self._phi_window_skipped = set()
        if self.target_track_offset_ranges_deg is None:
            self.target_track_offset_ranges_deg = target_areas_track_offset_ranges_deg(
                self.target_areas
            )
        if self.capture_targets is None:
            self.capture_targets = tuple(range(self.n_targets))
        self.active_target_index = (
            int(self.capture_targets[0]) if self.capture_targets else self.n_targets
        )

    @property
    def n_targets(self) -> int:
        return len(self.target_anchors)

    def active_anchor(self) -> tuple[float, float]:
        idx = min(max(0, self.active_target_index), self.n_targets - 1)
        return self.target_anchors[idx]

    def in_phi_engage_window(self, theta_orbit_rad: float) -> bool:
        if self.active_target_index >= self.n_targets:
            return False
        phi_lo = float(self.target_leading_phi_lo_deg[self.active_target_index])
        phi_hi = float(self.target_trailing_phi_hi_deg[self.active_target_index])
        theta_deg = float(np.rad2deg(theta_orbit_rad))
        engage_lo = phi_lo - float(self.lead_margin_deg)
        return engage_lo <= theta_deg <= phi_hi

    def should_engage(self, theta_orbit_rad: float) -> bool:
        """Orbit-φ window only (legacy name). Prefer ``can_engage`` for full gating."""
        return self.in_phi_engage_window(theta_orbit_rad)

    def can_engage(
        self,
        state: SimulationTimestepState,
        *,
        sat_pos_xy_km: np.ndarray,
        sat_inertia: Any,
        tau_max_nm: float,
    ) -> bool:
        if not self.in_phi_engage_window(float(state.theta_orbit_rad)):
            return False
        idx = int(self.active_target_index)
        if idx >= self.n_targets:
            return False
        anchor = np.asarray(self.target_anchors[idx], dtype=float)
        omega_sat_q = float(state.omega_sat_rad_s) * ureg.rad / ureg.s
        tau_max_q = (
            float(tau_max_nm) * ureg.N * ureg.m
            if tau_max_nm is not None
            else REACTION_WHEEL_MAX_TORQUE
        )
        return target_pointing_safe_for_engage(
            sat_pos_xy_km=np.asarray(sat_pos_xy_km, dtype=float),
            ground_target_xy_km=anchor,
            omega_sat=omega_sat_q,
            tau_max=tau_max_q,
            sat_inertia=sat_inertia,
            off_nadir_limit=OFF_NADIR_HARD_LIMIT_DEG,
        )

    def update_pointing_phase(
        self,
        state: SimulationTimestepState,
        *,
        sat_pos_xy_km: np.ndarray,
        sat_inertia: Any,
        tau_max_nm: float,
    ) -> None:
        idx = int(self.active_target_index)
        track_offset_deg = track_offset_deg_from_disk_xy_km(np.asarray(sat_pos_xy_km, dtype=float))
        if (
            idx < self.n_targets
            and idx not in self._shuttered
            and self._capture_i < len(self.capture_targets)
            and self._active_target_needs_phi_window()
        ):
            phi_hi = float(self.target_trailing_phi_hi_deg[idx])
            theta_deg = float(np.rad2deg(float(state.theta_orbit_rad)))
            if theta_deg > phi_hi and idx not in self._phi_window_skipped:
                self._phi_window_skipped.add(idx)
                self._skip_missed_capture_target(
                    _step_idx=int(state.step_idx),
                    _reason="phi_window_missed",
                )
                idx = int(self.active_target_index)
        if self.pointing_phase == "nadir" and not self._flown_over_previous_capture(
            float(track_offset_deg)
        ):
            return
        if self.pointing_phase == "nadir" and self._active_target_needs_phi_window():
            if not self.in_phi_engage_window(float(state.theta_orbit_rad)):
                return
            if not self._safe_to_point_at_active(
                state,
                sat_pos_xy_km=sat_pos_xy_km,
                sat_inertia=sat_inertia,
                tau_max_nm=tau_max_nm,
            ):
                return
        self._try_enter_engage(
            state,
            sat_pos_xy_km=sat_pos_xy_km,
            sat_inertia=sat_inertia,
            tau_max_nm=tau_max_nm,
            track_offset_deg=float(track_offset_deg),
        )

    def _gains(self, *, sat_inertia: Any, tau_max_nm: float) -> NadirPointingGains:
        if self._pointing_gains is None:
            self._pointing_gains = default_nadir_pointing_gains(
                tau_max_nm=float(tau_max_nm),
                sat_inertia=sat_inertia,
            )
        return self._pointing_gains

    def compute_torque_request_nm(
        self,
        state: SimulationTimestepState,
        *,
        sat_pos_xy_km: np.ndarray,
        omega_orbit_rad_s: float,
        sat_inertia: Any,
        tau_max_nm: float,
    ) -> float:
        """PD torque request mirroring AttitudePointingController for nadir / target engage."""
        gains = self._gains(sat_inertia=sat_inertia, tau_max_nm=tau_max_nm)
        body_z = float(state.body_z_angle_rad)
        omega_sat = float(state.omega_sat_rad_s)
        if self.pointing_phase == "nadir":
            return nadir_pointing_torque_nm(
                body_z_rad=body_z,
                omega_sat_rad_s=omega_sat,
                theta_orbit_rad=float(state.theta_orbit_rad),
                omega_orbit_rad_s=float(omega_orbit_rad_s),
                omega_cmd_rad_s=0.0,
                tau_max_nm=float(tau_max_nm),
                gains=gains,
            )
        anchor = np.asarray(self.active_anchor(), dtype=float)
        theta_target = target_boresight_angle_rad(sat_pos_xy_km, anchor)
        omega_target = target_boresight_rate_rad_s(
            sat_pos_xy_km=sat_pos_xy_km,
            omega_orbit_rad_s=float(omega_orbit_rad_s),
            ground_target_xy_km=anchor,
        )
        return body_pointing_torque_nm(
            body_z_rad=body_z,
            omega_sat_rad_s=omega_sat,
            theta_target_rad=theta_target,
            omega_target_rad_s=omega_target,
            tau_max_nm=float(tau_max_nm),
            gains=gains,
            omega_cmd_rad_s=0.0,
        )

    def observe(
        self,
        state: SimulationTimestepState,
        *,
        sat_pos_xy_km: np.ndarray,
    ) -> BaselinePolicyObservation:
        bearings = np.array(
            [
                target_boresight_angle_rad(sat_pos_xy_km, np.asarray(anchor, dtype=float))
                for anchor in self.target_anchors
            ],
            dtype=float,
        )
        codes = np.asarray(state.camera_observation_line_codes, dtype=np.int8)
        visible = bool(np.any(codes == np.int8(OBSERVATION_TARGET)))
        _lon, lat = disk_xy_km_to_geodetic_deg(np.asarray(sat_pos_xy_km, dtype=float))
        track_offset = track_offset_deg_from_disk_xy_km(np.asarray(sat_pos_xy_km, dtype=float))
        return BaselinePolicyObservation(
            active_target_index=int(self.active_target_index),
            pointing_phase=str(self.pointing_phase),
            target_boresight_angles_rad=bearings,
            body_z_angle_rad=float(state.body_z_angle_rad),
            target_visible_in_strip=visible,
            sat_subpoint_lat_deg=float(lat),
            sat_track_offset_deg=float(track_offset),
            camera_image_quality=float(state.primary_camera_image_quality),
        )

    def _target_track_range_deg(self, target_idx: int) -> tuple[float, float]:
        lo, hi = self.target_track_offset_ranges_deg[int(target_idx)]
        return float(lo), float(hi)

    def _active_target_track_overlap(self, track_offset_deg: float) -> bool:
        idx = int(self.active_target_index)
        if idx >= self.n_targets:
            return False
        lo, hi = self._target_track_range_deg(idx)
        return lo <= float(track_offset_deg) <= hi

    def _flown_over_target(self, target_idx: int, track_offset_deg: float) -> bool:
        if target_idx < 0 or target_idx >= self.n_targets:
            return True
        _lo, hi = self._target_track_range_deg(int(target_idx))
        return float(track_offset_deg) > hi

    def _flown_over_previous_capture(self, track_offset_deg: float) -> bool:
        """True once the prior scheduled target is captured or its trailing edge is passed."""
        if self._capture_i <= 0 or not self.capture_targets:
            return True
        prev_idx = int(self.capture_targets[self._capture_i - 1])
        if prev_idx in self._shuttered:
            return True
        return self._flown_over_target(prev_idx, track_offset_deg)

    def _active_target_needs_phi_window(self) -> bool:
        """Only the first scheduled target waits for orbit-φ; later targets slew on flyover."""
        return int(self._capture_i) == 0

    def _safe_to_point_at_active(
        self,
        state: SimulationTimestepState,
        *,
        sat_pos_xy_km: np.ndarray,
        sat_inertia: Any,
        tau_max_nm: float,
    ) -> bool:
        idx = int(self.active_target_index)
        if idx >= self.n_targets:
            return False
        anchor = np.asarray(self.target_anchors[idx], dtype=float)
        omega_sat_q = float(state.omega_sat_rad_s) * ureg.rad / ureg.s
        tau_max_q = (
            float(tau_max_nm) * ureg.N * ureg.m
            if tau_max_nm is not None
            else REACTION_WHEEL_MAX_TORQUE
        )
        return target_pointing_safe_for_engage(
            sat_pos_xy_km=np.asarray(sat_pos_xy_km, dtype=float),
            ground_target_xy_km=anchor,
            omega_sat=omega_sat_q,
            tau_max=tau_max_q,
            sat_inertia=sat_inertia,
            off_nadir_limit=OFF_NADIR_HARD_LIMIT_DEG,
        )

    def _try_enter_engage(
        self,
        state: SimulationTimestepState,
        *,
        sat_pos_xy_km: np.ndarray,
        sat_inertia: Any,
        tau_max_nm: float,
        track_offset_deg: float,
    ) -> bool:
        if self.pointing_phase != "nadir":
            return False
        if int(self.active_target_index) >= self.n_targets:
            return False
        if not self._flown_over_previous_capture(track_offset_deg):
            return False
        if self._flown_over_target(int(self.active_target_index), track_offset_deg):
            return False
        if self._active_target_needs_phi_window() and not self.in_phi_engage_window(
            float(state.theta_orbit_rad)
        ):
            return False
        if not self._safe_to_point_at_active(
            state,
            sat_pos_xy_km=sat_pos_xy_km,
            sat_inertia=sat_inertia,
            tau_max_nm=tau_max_nm,
        ):
            return False
        self.pointing_phase = "engage"
        return True

    def _past_trailing_edge(self, track_offset_deg: float) -> bool:
        return self._flown_over_target(int(self.active_target_index), track_offset_deg)

    def _skip_missed_capture_target(self, *, _step_idx: int, _reason: str) -> None:
        """Advance strided schedule when the current target cannot be shuttered in its window."""
        self.pointing_phase = "nadir"
        self._capture_i += 1
        if self._capture_i < len(self.capture_targets):
            self.active_target_index = int(self.capture_targets[self._capture_i])
        else:
            self.active_target_index = self.n_targets

    def act(
        self,
        obs: BaselinePolicyObservation,
        *,
        step_idx: int,
        state: SimulationTimestepState,
        sat_pos_xy_km: np.ndarray,
        omega_orbit_rad_s: float,
        sat_inertia: Any,
        tau_max_nm: float,
        skip_torque_request: bool = False,
    ) -> BaselinePolicyAction:
        if skip_torque_request:
            torque_request_nm = 0.0
        else:
            torque_request_nm = self.compute_torque_request_nm(
                state,
                sat_pos_xy_km=sat_pos_xy_km,
                omega_orbit_rad_s=omega_orbit_rad_s,
                sat_inertia=sat_inertia,
                tau_max_nm=tau_max_nm,
            )
        take_picture = False
        idx = int(obs.active_target_index)
        if obs.pointing_phase == "engage":
            if idx >= self.n_targets or idx in self._shuttered:
                pass
            else:
                threshold_rad = float(np.deg2rad(self.tracking_threshold_deg))
                bearing = float(obs.target_boresight_angles_rad[idx])
                tracking_err = abs(float(obs.body_z_angle_rad) - bearing)
                quality = float(obs.camera_image_quality)
                track_offset = float(obs.sat_track_offset_deg)
                in_band = self._active_target_track_overlap(track_offset)
                past_trailing = self._past_trailing_edge(track_offset)
                locked = tracking_err <= threshold_rad
                quality_ok = np.isfinite(quality) and quality >= MIN_CAPTURE_QUALITY
                if in_band or past_trailing:
                    should_shutter = locked or quality_ok or past_trailing
                else:
                    should_shutter = False
                if should_shutter:
                    self._shuttered.add(idx)
                    self.cmd_steps.append(int(step_idx))
                    self._capture_i += 1
                    next_idx = (
                        int(self.capture_targets[self._capture_i])
                        if self._capture_i < len(self.capture_targets)
                        else self.n_targets
                    )
                    self.active_target_index = next_idx
                    if next_idx < self.n_targets and (
                        past_trailing
                        or self._flown_over_target(idx, track_offset)
                    ):
                        if self._safe_to_point_at_active(
                            state,
                            sat_pos_xy_km=sat_pos_xy_km,
                            sat_inertia=sat_inertia,
                            tau_max_nm=tau_max_nm,
                        ):
                            self.pointing_phase = "engage"
                        else:
                            self.pointing_phase = "nadir"
                    else:
                        self.pointing_phase = "nadir"
                    take_picture = True
        return BaselinePolicyAction(
            torque_request_nm=float(torque_request_nm),
            take_picture=take_picture,
        )


@dataclass(frozen=True)
class BaselineOverflightRollout:
    series: SimulationStateSeries
    policy: SequentialTargetBaselinePolicy
    cmd_steps: tuple[int, ...]
    n_safety_events: int
    attitude_request_mode: AttitudeRequestMode = "torque"


@dataclass(frozen=True)
class BaselineCaptureKPIs:
    n_targets: int
    n_shutter_cmds: int
    n_captures_taken: int
    total_latent_capture_reward: float
    total_applied_capture_reward: float
    mean_quality: float
    budget_exhausted_at_target: int | None
    capture_results: tuple[CaptureResult, ...]

    @property
    def total_capture_reward(self) -> float:
        """Backward-compatible alias for applied capture credit (MPO-comparable)."""
        return self.total_applied_capture_reward


def warmup_capture_targets(
    warmup_episode_idx: int,
    *,
    n_targets: int,
    targets_per_episode: int = 10,
) -> tuple[int, ...]:
    """Cross-corridor strided indices for one warmup episode.

    With 50 targets and 10/ep over 5 chunks (stride = n_chunks = 5):
    ep0 → 0,5,10,…,45; ep1 → 1,6,11,…; ep4 → 4,9,14,…,49; ep5 wraps to ep0.
    """
    if n_targets <= 0:
        raise ValueError("n_targets must be > 0.")
    if targets_per_episode <= 0:
        raise ValueError("targets_per_episode must be > 0.")
    per = min(int(targets_per_episode), int(n_targets))
    n_chunks = max(1, (int(n_targets) + per - 1) // per)
    offset = int(warmup_episode_idx) % n_chunks
    return tuple(offset + k * n_chunks for k in range(per) if offset + k * n_chunks < n_targets)


def build_overflight_policy(
    setup,
    *,
    earth_radius_km: float,
    capture_targets: tuple[int, ...] | None = None,
) -> SequentialTargetBaselinePolicy:
    """Build ``SequentialTargetBaselinePolicy`` from a mission setup."""
    return _build_policy_from_setup(
        setup,
        earth_radius_km=earth_radius_km,
        capture_targets=capture_targets,
    )


def _build_policy_from_setup(
    setup,
    *,
    earth_radius_km: float,
    capture_targets: tuple[int, ...] | None = None,
) -> SequentialTargetBaselinePolicy:
    areas = tuple(setup.target_areas)
    anchors = tuple(
        target_area_view_anchor_disk_xy_km(area, earth_radius_km=earth_radius_km) for area in areas
    )
    leading_phi = tuple(_target_leading_phi_lo_deg(area) for area in areas)
    trailing_phi = tuple(_target_trailing_phi_hi_deg(area) for area in areas)
    return SequentialTargetBaselinePolicy(
        target_anchors=anchors,
        target_areas=areas,
        target_leading_phi_lo_deg=leading_phi,
        target_trailing_phi_hi_deg=trailing_phi,
        capture_targets=capture_targets,
    )


def run_baseline_overflight_rollout(
    setup,
    *,
    simulation_config: SimulationConfig | None = None,
    show_progress: bool = True,
    capture_targets: tuple[int, ...] | None = None,
    warmup_episode_idx: int = 0,
    targets_per_episode: int | None = None,
    attitude_request_mode: AttitudeRequestMode = "torque",
) -> BaselineOverflightRollout:
    from autonomous_control.baseline_overflight_step import (
        apply_baseline_shutter_if_requested,
        baseline_overflight_controller_tick_for_mode,
    )
    from tqdm import tqdm

    mode = str(attitude_request_mode).lower()
    if mode not in ("torque", "vector"):
        raise ValueError(f"Unsupported attitude_request_mode: {attitude_request_mode!r}")
    sim_cfg = simulation_config or training_episode_simulation_config(
        torque_policy_label="sequential_target_baseline",
        attitude_request_mode=mode,  # type: ignore[arg-type]
    )
    resolved = setup.resolve(require_camera=True)
    earth_radius_km = float(resolved.earth_radius.to(ureg.km).magnitude)
    sat_inertia = resolved.satellite.moment_of_inertia_2d
    tau_max_nm = float(
        resolved.satellite.reaction_wheel_max_torque.to(ureg.N * ureg.m).magnitude
    )
    if capture_targets is None:
        n_targets = len(setup.target_areas or ())
        per = (
            int(targets_per_episode)
            if targets_per_episode is not None
            else int(MAX_PRIMARY_CAPTURES_PER_ORBIT)
        )
        capture_targets = warmup_capture_targets(
            int(warmup_episode_idx),
            n_targets=n_targets,
            targets_per_episode=per,
        )
    policy = build_overflight_policy(
        setup,
        earth_radius_km=earth_radius_km,
        capture_targets=capture_targets,
    )
    stepper = build_stepper(resolved, simulation_config=sim_cfg)
    if mode == "vector":
        ctrl0 = stepper.current_timestep_state()
        stepper.reset_vector_pointing_episode(theta_orbit_rad=float(ctrl0.theta_orbit_rad))
    omega_orbit_rad_s = float(stepper._omega_orbit_rad_s)
    budget = TakePictureBudget.from_config(TakePictureConfig())
    total_steps = max(0, int(stepper._t_s.shape[0]) - 1)
    n_frames = int(stepper._t_s.shape[0])
    view_anchors = np.full((n_frames, 2), np.nan, dtype=float)
    active_target_idx = np.full(n_frames, -1, dtype=np.int32)
    take_picture_cmd = np.zeros(n_frames, dtype=bool)
    stored_action = np.array([0.0, -1.0], dtype=np.float32)
    take_picture_this_step = False
    iterator = tqdm(
        total=total_steps,
        desc=f"baseline overflight ({mode})",
        disable=not show_progress,
    )
    try:
        while not stepper.done:
            state = stepper.current_timestep_state()
            sat_xy = np.asarray(state.sat_pos_xy_km, dtype=float)
            k = int(state.step_idx)
            take_picture_this_step = False
            if stepper.should_update_controller():
                _action, stored_action, take_picture_this_step = (
                    baseline_overflight_controller_tick_for_mode(
                        attitude_request_mode=mode,  # type: ignore[arg-type]
                        policy=policy,
                        stepper=stepper,
                        state=state,
                        sat_pos_xy_km=sat_xy,
                        omega_orbit_rad_s=omega_orbit_rad_s,
                        sat_inertia=sat_inertia,
                        tau_max_nm=tau_max_nm,
                        budget=budget,
                    )
                )
            if policy.pointing_phase == "engage":
                ax, ay = policy.active_anchor()
                view_anchors[k] = (ax, ay)
                active_target_idx[k] = int(policy.active_target_index)
            else:
                view_anchors[k] = _nadir_ground_xy_km(sat_xy, earth_radius_km=earth_radius_km)
                active_target_idx[k] = -1
            if mode == "vector":
                pointing_u = float(stored_action[0])
                omega_target = baseline_omega_target_rad_s(
                    policy,
                    state,
                    sat_pos_xy_km=sat_xy,
                    omega_orbit_rad_s=omega_orbit_rad_s,
                )
                wheel_nm = stepper.resolve_vector_u_to_torque_nm(
                    u=pointing_u,
                    theta_orbit_rad=float(state.theta_orbit_rad),
                    sat_pos_xy_km=sat_xy,
                    body_z_rad=float(state.body_z_angle_rad),
                    omega_sat_rad_s=float(state.omega_sat_rad_s),
                    omega_target_rad_s=omega_target,
                )
            else:
                pointing_u = None
                wheel_nm = float(stored_action[0]) * tau_max_nm
            stepper.step(wheel_torque_cmd_nm=wheel_nm, agent_pointing_cmd_u=pointing_u)
            cmd_step = apply_baseline_shutter_if_requested(
                stepper=stepper,
                take_picture_cmd=take_picture_this_step,
                budget=budget,
            )
            if cmd_step is not None:
                take_picture_cmd[cmd_step] = True
            if iterator.n < total_steps:
                iterator.update(1)
    finally:
        iterator.close()
    series = replace(
        stepper.finalize_series(),
        baseline_view_anchor_xy_km=view_anchors,
        baseline_active_target_idx=active_target_idx,
        baseline_take_picture_cmd=take_picture_cmd,
    )
    return BaselineOverflightRollout(
        series=series,
        policy=policy,
        cmd_steps=tuple(policy.cmd_steps),
        n_safety_events=len(stepper.attitude_safety_events),
        attitude_request_mode=mode,  # type: ignore[arg-type]
    )


def evaluate_baseline_capture_results(
    series: SimulationStateSeries,
    cmd_steps: tuple[int, ...],
    *,
    max_pictures: int = MAX_PRIMARY_CAPTURES_PER_ORBIT,
    n_targets: int = BASELINE_N_TARGETS,
) -> BaselineCaptureKPIs:
    results = tuple(
        evaluate_capture_schedule(
            series,
            cmd_steps=cmd_steps,
            max_pictures=max_pictures,
        )
    )
    taken = [r for r in results if r.picture_taken]
    budget_exhausted_at: int | None = None
    taken_count = 0
    for i, r in enumerate(results):
        if r.picture_taken:
            taken_count += 1
        if taken_count >= max_pictures and not r.picture_taken:
            budget_exhausted_at = i
            break
    qualities = [r.quality for r in taken if np.isfinite(r.quality)]
    return BaselineCaptureKPIs(
        n_targets=int(n_targets),
        n_shutter_cmds=len(cmd_steps),
        n_captures_taken=len(taken),
        total_latent_capture_reward=float(sum(r.latent_reward for r in taken)),
        total_applied_capture_reward=float(sum(r.capture_reward for r in taken)),
        mean_quality=float(np.mean(qualities)) if qualities else 0.0,
        budget_exhausted_at_target=budget_exhausted_at,
        capture_results=results,
    )


def build_baseline_instant_reward_trace(
    series: SimulationStateSeries,
    capture_results: tuple[CaptureResult, ...],
) -> np.ndarray:
    """Per-step capture reward (zero except at shutter steps with credit)."""
    n = int(series.t_s.shape[0])
    per_frame = np.zeros(n, dtype=float)
    for cap in capture_results:
        if cap.capture_step is None:
            continue
        k = int(cap.capture_step)
        if 0 <= k < n:
            per_frame[k] += float(cap.capture_reward)
    return per_frame


def build_baseline_latent_reward_trace(
    series: SimulationStateSeries,
    capture_results: tuple[CaptureResult, ...],
) -> np.ndarray:
    """Cumulative capture (latent) reward for video — visible independent of distance reward."""
    n = int(series.t_s.shape[0])
    per_frame = np.zeros(n, dtype=float)
    for cap in capture_results:
        if cap.capture_step is None:
            continue
        k = int(cap.capture_step)
        if 0 <= k < n:
            per_frame[k] += float(cap.latent_reward)
    return np.cumsum(per_frame)


def build_baseline_reward_trace(
    series: SimulationStateSeries,
    capture_results: tuple[CaptureResult, ...],
) -> np.ndarray:
    """Alias: latent cumulative capture reward for baseline video overlay."""
    return build_baseline_latent_reward_trace(series, capture_results)


def print_baseline_setup_summary(setup) -> None:
    resolved = setup.resolve(require_camera=True)
    n_clouds = len(setup.clouds or ())
    n_targets = len(setup.target_areas or ())
    alt_km = float(resolved.altitude.to(ureg.km).magnitude)
    orbit = setup.orbit
    start_deg = orbit.start_angle_deg if orbit is not None else "auto"
    end_deg = orbit.end_angle_deg if orbit is not None else "auto"
    print("Baseline overflight setup")
    print(f"  targets:           {n_targets}")
    print(f"  clouds:            {n_clouds} (seeded over target corridor)")
    print(f"  lead margin:       {BASELINE_LEAD_MARGIN_DEG:.1f}° before target engage")
    print(f"  altitude:          {alt_km:.1f} km")
    print(f"  orbit window:      {start_deg}° .. {end_deg}° (auto if unset)")
    print(f"  capture budget:    {MAX_PRIMARY_CAPTURES_PER_ORBIT}/orbit")


def print_baseline_capture_kpis(
    kpis: BaselineCaptureKPIs,
    *,
    rollout: BaselineOverflightRollout | None = None,
    title: str | None = None,
) -> None:
    if title:
        print(title)
    else:
        print("Baseline capture KPIs")
    print(f"  shutter commands:  {kpis.n_shutter_cmds} / {kpis.n_targets} targets")
    print(f"  captures taken:    {kpis.n_captures_taken} / {MAX_PRIMARY_CAPTURES_PER_ORBIT} budget")
    print(f"  latent capture:    {kpis.total_latent_capture_reward:.2f}  (k * cov * quality * (1 - cloud))")
    print(
        f"  applied capture:   {kpis.total_applied_capture_reward:.2f}  "
        f"(latent scaled by cov; 0 if not visible / not taken / repeat target)"
    )
    print(f"  mean quality:      {kpis.mean_quality:.4f}")
    if kpis.budget_exhausted_at_target is not None:
        print(f"  budget exhausted at shutter index: {kpis.budget_exhausted_at_target}")
    if rollout is not None:
        print(f"  attitude safety events: {rollout.n_safety_events}")
        mean_sim = float(np.mean(rollout.series.simulation_reward))
        print(f"  mean sim reward:   {mean_sim:.3f}")
    print(
        "\n  cmd  cap  taken  visible  cov    quality  cloud   latent  applied  budget_left"
    )
    for r in kpis.capture_results[:15]:
        cap = "—" if r.capture_step is None else f"{r.capture_step:3d}"
        print(
            f"  {r.cmd_step:3d}  {cap}  "
            f"{'yes' if r.picture_taken else ' no'}     "
            f"{'yes' if r.target_visible else ' no'}      "
            f"{r.target_coverage:5.3f}  {r.quality:7.4f}  {r.cloud_frac:5.3f}  "
            f"{r.latent_reward:7.2f}  {r.capture_reward:7.2f}  {r.budget_remaining:3d}"
        )
    if len(kpis.capture_results) > 15:
        print(f"  ... ({len(kpis.capture_results) - 15} more shutter commands)")


def print_baseline_mode_comparison(
    *,
    torque: tuple[BaselineOverflightRollout, BaselineCaptureKPIs],
    vector: tuple[BaselineOverflightRollout, BaselineCaptureKPIs],
) -> None:
    """Side-by-side summary for torque vs vector baseline rollouts."""
    t_roll, t_kpi = torque
    v_roll, v_kpi = vector
    rows = [
        ("attitude mode", t_roll.attitude_request_mode, v_roll.attitude_request_mode),
        ("shutter cmds", t_kpi.n_shutter_cmds, v_kpi.n_shutter_cmds),
        ("captures taken", t_kpi.n_captures_taken, v_kpi.n_captures_taken),
        (
            "applied capture",
            f"{t_kpi.total_applied_capture_reward:.2f}",
            f"{v_kpi.total_applied_capture_reward:.2f}",
        ),
        ("mean quality", f"{t_kpi.mean_quality:.4f}", f"{v_kpi.mean_quality:.4f}"),
        ("safety events", t_roll.n_safety_events, v_roll.n_safety_events),
        (
            "mean sim reward",
            f"{float(np.mean(t_roll.series.simulation_reward)):.3f}",
            f"{float(np.mean(v_roll.series.simulation_reward)):.3f}",
        ),
    ]
    if t_roll.policy.capture_targets == v_roll.policy.capture_targets:
        rows.insert(
            1,
            (
                "capture schedule",
                list(t_roll.policy.capture_targets),
                list(v_roll.policy.capture_targets),
            ),
        )
    cmd_match = t_roll.cmd_steps == v_roll.cmd_steps
    rows.append(
        (
            "cmd_steps match",
            "yes" if cmd_match else "no",
            "yes" if cmd_match else "no",
        )
    )
    print("Baseline torque vs vector comparison")
    print(f"  {'metric':<18}  {'torque':>12}  {'vector':>12}")
    for label, t_val, v_val in rows:
        print(f"  {label:<18}  {str(t_val):>12}  {str(v_val):>12}")


def export_baseline_overflight_video(
    series: SimulationStateSeries,
    reward_trace: np.ndarray,
    out_path: Path | str,
    *,
    shutter_cmd_steps: tuple[int, ...] = (),
    width: int = 680,
) -> Path:
    """Export proof MP4 with cumulative latent reward and take-picture telemetry markers."""
    from utils.notebook.video import export_and_play_saved_video

    meta = replace(
        series.metadata,
        baseline_shutter_cmd_steps=tuple(int(s) for s in shutter_cmd_steps) or None,
    )
    augmented = replace(
        series,
        simulation_reward=np.asarray(reward_trace, dtype=float),
        metadata=meta,
    )
    path = export_and_play_saved_video(
        simulation_series=augmented,
        out_path=Path(out_path),
        width=width,
    )
    print(f"artifact={path}")
    return path
