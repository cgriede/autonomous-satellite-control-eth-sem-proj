from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal

import numpy as np

# Filled when camera optics were not run (e.g. kinematic-only trajectory helper).
OBSERVATION_LINE_NOT_COMPUTED = np.int8(-99)

# Shared observation codes used by camera and fixed-ground line classifications.
OBSERVATION_SPACE = np.int8(0)
OBSERVATION_EARTH = np.int8(1)
OBSERVATION_CLOUD = np.int8(2)
OBSERVATION_TARGET = np.int8(3)

# Fixed-ground only code: mark the bin corresponding to boresight cone hit on Earth.
FIXED_GROUND_CONE_HIT_EARTH = np.int8(4)

# Keep this scalar import-safe (available before camera_optics import can recurse).
DEFAULT_CAMERA_OBSERVATION_LINE_N_BINS = 100

from simulation.camera_optics import pinhole_full_fov_rad

from .UNIT_REGISTRY import UREG as ureg
from .SATELLITE import FOCAL_LENGTH, SENSOR_HEIGHT


@dataclass(frozen=True)
class Cloud:
    height: Any
    start_location: Any
    end_location: Any

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
    # Rays sampled along the sensor column for camera strip cloud-blocked stats (see simulation.camera_2d).
    camera_pixel_ray_samples: int
    # Bins along the vertical FOV for simulate_camera_observation_line_1d and SimulationStateSeries.
    camera_observation_line_n_bins: int
    # Sensor/camera kernel backend: "python" for baseline, "accelerated" for vectorized kernels.
    camera_kernel_backend: Literal["python", "accelerated"]
    # Canonical episode step cap for gym/training rollouts.
    max_episode_steps: int


class RenderMode(str, Enum):
    HEADLESS = "headless"
    INTERACTIVE = "interactive"
    EXPORT = "export"


_BASELINE_CONTROLLER_MODES: frozenset[str] = frozenset({"baseline", "random", "coast"})


@dataclass(frozen=True)
class SimulationConfig:
    render_mode: RenderMode = RenderMode.INTERACTIVE
    controller_mode: Literal["baseline", "random", "coast"] = "random"
    controller_seed: int | None = None


SIMULATION = SimulationConstants(
    theta_center=90.0 * ureg.deg,
    sat_motion_span_scale=1.05,
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
            height=15.0 * ureg.km,
            start_location=89.99 * ureg.deg,
            end_location=90.2 * ureg.deg,
        ),
    ),
    export_speed_multiplier=30.0,
    camera_pixel_ray_samples=96,
    camera_observation_line_n_bins=DEFAULT_CAMERA_OBSERVATION_LINE_N_BINS,
    camera_kernel_backend="accelerated",
    max_episode_steps=1000,
)

