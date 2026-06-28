from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal

import numpy as np

# Filled when camera optics were not run (e.g. kinematic-only trajectory helper).
OBSERVATION_LINE_NOT_COMPUTED = np.int8(-99)

# Shared observation codes used by camera classifications.
OBSERVATION_SPACE = np.int8(0)
OBSERVATION_EARTH = np.int8(1)
OBSERVATION_CLOUD = np.int8(2)
OBSERVATION_TARGET = np.int8(3)

# Keep this scalar import-safe (available before camera_optics import can recurse).
DEFAULT_CAMERA_OBSERVATION_LINE_N_BINS = 100

from simulation.camera_optics import pinhole_full_fov_rad

from .UNIT_REGISTRY import UREG as ureg
from .SATELLITE import FOCAL_LENGTH, SENSOR_HEIGHT


@dataclass(frozen=True)
class GeodeticLonLat:
    """Surface geodetic endpoint (pint lat/lon quantities)."""

    lat: Any
    lon: Any


@dataclass(frozen=True)
class Cloud:
    """Cloud patch as a vertical slab along an orbit-disk arc (converted to disk φ at sim time)."""

    base_altitude: Any
    top_altitude: Any
    start_location: GeodeticLonLat
    end_location: GeodeticLonLat

@dataclass(frozen=True)
class Location:
    location: Any
    parent_body: Any


@dataclass(frozen=True)
class BodyLocation(Location):
    belongs_to_body: bool

@dataclass(frozen=True)
class FieldOfViewCone:
    opening_angle: Any
    body_location: Any = None


@dataclass(frozen=True)
class SimulationConstants:
    theta_center: Any
    sat_motion_span_scale: float
    contact_margin_angle: Any
    simulation_timestep: Any
    controller_update_interval: Any
    sat_z_offset: Any
    field_of_view_cone: Any
    cone_length: Any
    z_axis_length: Any
    clouds: tuple[Cloud, ...]
    export_speed_multiplier: float
    # Bins along the vertical FOV; observation line codes and cloud_blocked_fraction share this grid.
    camera_observation_line_n_bins: int
    # Sensor/camera kernel backend: "python" for baseline, "accelerated" for vectorized kernels.
    camera_kernel_backend: Literal["python", "accelerated"]
    # Canonical episode step cap for gym/training rollouts.
    max_episode_steps: int


class RenderMode(str, Enum):
    HEADLESS = "headless"
    INTERACTIVE = "interactive"
    EXPORT = "export"


BuiltinTorquePolicy = Literal["baseline", "random", "coast"]
TorqueCommandSource = Literal["builtin", "external"]
ObcPointingMode = Literal["none", "nadir", "target"]

BASELINE_TORQUE_POLICIES: frozenset[str] = frozenset({"baseline", "random", "coast"})


def control_stack_display_label(
    *,
    torque_command_source: str,
    builtin_torque_policy: str | None = None,
    torque_policy_label: str | None = None,
    attitude_controller_enabled: bool = False,
    obc_pointing_mode: ObcPointingMode = "none",
) -> str:
    """Human-readable control stack for metadata / render telemetry."""
    if str(torque_command_source).lower() == "external":
        label = str(torque_policy_label or "external_policy")
    else:
        label = f"builtin:{builtin_torque_policy or 'coast'}"
    pointing = str(obc_pointing_mode).lower()
    if pointing == "nadir":
        label = f"{label} · obc_nadir"
    elif pointing == "target":
        label = f"{label} · obc_target"
    if attitude_controller_enabled:
        label = f"{label} · attitude_controller"
    return label


@dataclass(frozen=True)
class SimulationConfig:
    """Simulation run options.

    Torque command path (high level):
    - ``torque_command_source="builtin"``: stepper baseline loop (``builtin_torque_policy``).
    - ``torque_command_source="external"``: caller/policy supplies torque each step
      (``torque_policy_label`` names the policy, e.g. ``delayed_max_torque``).

    Low level (reaction wheel plant):
    - ``attitude_controller_enabled``: ``AttitudeSafetyController`` arbitrates external
      requests before the wheel (taper / safe mode).
    """

    render_mode: RenderMode = RenderMode.INTERACTIVE
    torque_command_source: TorqueCommandSource = "builtin"
    builtin_torque_policy: BuiltinTorquePolicy = "random"
    torque_policy_label: str | None = None
    controller_seed: int | None = None
    attitude_controller_enabled: bool = False
    # OBC body pointing: overrides agent torque with nadir or ground-target tracking PD.
    obc_pointing_mode: ObcPointingMode = "none"


def training_episode_simulation_config(
    *,
    torque_policy_label: str | None = None,
) -> SimulationConfig:
    """Headless external-policy config for MPO warmup/train/eval episodes."""
    return SimulationConfig(
        render_mode=RenderMode.HEADLESS,
        torque_command_source="external",
        torque_policy_label=torque_policy_label,
        attitude_controller_enabled=True,
    )


SIMULATION = SimulationConstants(
    theta_center=90.0 * ureg.deg,
    sat_motion_span_scale=0.7,  # JUSTIFICATION: fly central 70% of LOS-padded [start,end]; attitude-safety reach is tighter than horizon margins, so this trims dead compute with margin for all targets.
    contact_margin_angle=0.05 * ureg.deg,
    simulation_timestep=0.4 * ureg.s,
    controller_update_interval=1 * ureg.s,
    sat_z_offset=0.0 * ureg.deg,
    field_of_view_cone=FieldOfViewCone(
        # In the current 2D renderer, the sensor reduces to a 1D footprint line.
        # That in-plane opening is the sensor vertical FOV.
        opening_angle=pinhole_full_fov_rad(
            sensor_dim=SENSOR_HEIGHT, focal_length=FOCAL_LENGTH
        ),
    ),
    cone_length=20000.0 * ureg.km,
    z_axis_length=180.0 * ureg.km,
    clouds=(
        Cloud(
            base_altitude=4.0 * ureg.km,
            top_altitude=20.0 * ureg.km,
            start_location=GeodeticLonLat(lat=89.99 * ureg.deg, lon=0.0 * ureg.deg),
            end_location=GeodeticLonLat(lat=90.0 * ureg.deg, lon=0.0 * ureg.deg),
        ),
    ),
    export_speed_multiplier=30.0,
    camera_observation_line_n_bins=DEFAULT_CAMERA_OBSERVATION_LINE_N_BINS,
    camera_kernel_backend="accelerated",
    max_episode_steps=1000,
)

