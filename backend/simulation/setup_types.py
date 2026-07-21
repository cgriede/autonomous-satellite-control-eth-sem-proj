"""Configuration model for simulation setup: OrbitConfig, EnvironmentSetup, ResolvedSimulationSetup.

resolve() is the sole validation owner — no parallel validation paths elsewhere.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class SimulationSetupError(ValueError):
    """Raised by EnvironmentSetup.resolve() for invalid or incomplete configurations."""


@dataclass(frozen=True)
class OrbitConfig:
    altitude: Any | None = None
    theta_center: Any | None = None
    contact_margin: Any | None = None
    motion_span_scale: float | None = None
    sat_z_offset: Any | None = None
    # Orbit-plane θ offsets relative to ``theta_center`` [deg]. ``None`` → inferred at resolve()
    # from ``target_areas`` disk-φ bounds plus LOS contact half-angle and ``contact_margin``.
    start_angle_deg: float | None = None
    end_angle_deg: float | None = None


@dataclass(frozen=True)
class SimulationOverrides:
    camera_observation_line_n_bins: int | None = None
    camera_kernel_backend: str | None = None
    reward_config: Any | None = None  # RewardConfig | None
    # Secondary camera observation line bins (§J): resolved to 200 for dual-camera setups,
    # forced to 0 for single-camera setups regardless of this override value.
    secondary_camera_observation_line_n_bins: int | None = None


@dataclass(frozen=True)
class ResolvedSimulationSetup:
    """Fully-populated, validated simulation setup; no None on required fields."""

    satellite: Any
    earth_radius: Any
    earth_gravitational_parameter: Any
    altitude: Any
    theta_center_rad: float
    start_angle_deg: float
    end_angle_deg: float
    sat_motion_span_scale: float
    sat_z_offset_deg: float
    ureg: Any
    camera_observation_line_n_bins: int
    camera_kernel_backend: str
    cameras: tuple  # tuple[CameraMount, ...]
    clouds: tuple   # tuple[Cloud, ...]
    target_areas: tuple  # tuple[ObservationTargetArea, ...]
    reward_config: Any | None  # RewardConfig | None
    # Secondary observation line bins: 0 = no secondary camera (§J); never 200 for single-camera.
    secondary_camera_observation_line_n_bins: int = 0


@dataclass(frozen=True)
class EnvironmentSetup:
    """
    Declarative simulation setup config.

    cameras: explicit opt-in only — default (), never auto-inserted by resolve().
    Call resolve() to produce a fully-populated ResolvedSimulationSetup.
    """

    satellite: Any | None = None
    orbit: OrbitConfig | None = None
    cameras: tuple = ()
    clouds: tuple | None = None
    target_areas: tuple | None = None
    simulation_overrides: SimulationOverrides | None = None

    def resolve(self, *, require_camera: bool = False) -> ResolvedSimulationSetup:
        """Validate and fill payload-agnostic defaults from environment_definition.constants.

        Args:
            require_camera: When True, raises SimulationSetupError if cameras is empty.
                            v1 default is False; set True only once camera wiring into
                            SensorKernel is complete.

        Returns:
            ResolvedSimulationSetup — frozen, fully populated.

        Raises:
            SimulationSetupError: satellite or orbit.altitude missing, or require_camera
                                  with empty cameras.
        """
        from environment_definition.constants import (
            EARTH_GRAVITATIONAL_PARAMETER,
            EARTH_RADIUS,
            SIMULATION,
            UREG as ureg,
        )
        from environment_definition.constants.MISSION import (
            OBSERVATION_TARGET_AREAS,
            episode_theta_offsets_deg_for_target_areas,
        )

        if self.satellite is None:
            raise SimulationSetupError(
                "satellite must be set in EnvironmentSetup before calling resolve()."
            )

        orbit = self.orbit if self.orbit is not None else OrbitConfig()
        if orbit.altitude is None:
            raise SimulationSetupError(
                "orbit.altitude must be set in EnvironmentSetup before calling resolve()."
            )

        if require_camera and len(self.cameras) == 0:
            raise SimulationSetupError(
                "cameras is empty but require_camera=True. "
                "Add CameraMount(...) in build_setup()."
            )

        # Auto-fill payload-agnostic defaults from constants.
        clouds = self.clouds if self.clouds is not None else SIMULATION.clouds
        target_areas = (
            self.target_areas if self.target_areas is not None else OBSERVATION_TARGET_AREAS
        )

        theta_center = (
            orbit.theta_center if orbit.theta_center is not None else SIMULATION.theta_center
        )
        theta_center_rad = float(theta_center.to(ureg.rad).magnitude)

        contact_margin = (
            orbit.contact_margin
            if orbit.contact_margin is not None
            else SIMULATION.contact_margin_angle
        )
        margin_deg = float(contact_margin.to(ureg.deg).magnitude)
        inferred_start_deg, inferred_end_deg = episode_theta_offsets_deg_for_target_areas(
            tuple(target_areas),
            orbit_height=orbit.altitude,
            margin_deg=margin_deg,
            theta_center_deg=float(theta_center.to(ureg.deg).magnitude),
        )
        start_angle_deg = (
            float(orbit.start_angle_deg)
            if orbit.start_angle_deg is not None
            else inferred_start_deg
        )
        end_angle_deg = (
            float(orbit.end_angle_deg)
            if orbit.end_angle_deg is not None
            else inferred_end_deg
        )
        if start_angle_deg >= end_angle_deg:
            raise SimulationSetupError(
                f"start_angle_deg ({start_angle_deg}) must be < end_angle_deg ({end_angle_deg})."
            )

        sat_motion_span_scale = (
            orbit.motion_span_scale
            if orbit.motion_span_scale is not None
            else float(SIMULATION.sat_motion_span_scale)
        )

        sat_z_offset = (
            orbit.sat_z_offset if orbit.sat_z_offset is not None else SIMULATION.sat_z_offset
        )
        sat_z_offset_deg = float(sat_z_offset.to(ureg.deg).magnitude)

        overrides = (
            self.simulation_overrides
            if self.simulation_overrides is not None
            else SimulationOverrides()
        )
        camera_observation_line_n_bins = (
            overrides.camera_observation_line_n_bins
            if overrides.camera_observation_line_n_bins is not None
            else int(SIMULATION.camera_observation_line_n_bins)
        )
        camera_kernel_backend = (
            overrides.camera_kernel_backend
            if overrides.camera_kernel_backend is not None
            else str(SIMULATION.camera_kernel_backend)
        )

        # §J: secondary bins = 0 for single-camera setups regardless of override value.
        _has_secondary = len(self.cameras) >= 2
        if _has_secondary:
            _secondary_override = overrides.secondary_camera_observation_line_n_bins
            secondary_camera_observation_line_n_bins = int(_secondary_override) if _secondary_override is not None else 200
        else:
            secondary_camera_observation_line_n_bins = 0

        return ResolvedSimulationSetup(
            satellite=self.satellite,
            earth_radius=EARTH_RADIUS,
            earth_gravitational_parameter=EARTH_GRAVITATIONAL_PARAMETER,
            altitude=orbit.altitude,
            theta_center_rad=float(theta_center_rad),
            start_angle_deg=float(start_angle_deg),
            end_angle_deg=float(end_angle_deg),
            sat_motion_span_scale=float(sat_motion_span_scale),
            sat_z_offset_deg=float(sat_z_offset_deg),
            ureg=ureg,
            camera_observation_line_n_bins=int(camera_observation_line_n_bins),
            camera_kernel_backend=str(camera_kernel_backend),
            cameras=tuple(self.cameras),
            clouds=tuple(clouds),
            target_areas=tuple(target_areas),
            reward_config=overrides.reward_config,
            secondary_camera_observation_line_n_bins=secondary_camera_observation_line_n_bins,
        )
