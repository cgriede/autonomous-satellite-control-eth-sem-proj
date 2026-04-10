from dataclasses import dataclass

from simulation.camera_optics import pinhole_full_fov_rad

from .UNIT_REGISTRY import UREG as ureg
from .SATELLITE import FOCAL_LENGTH, SENSOR_HEIGHT


@dataclass(frozen=True)
class Cloud:
    height: object
    start_location: object
    end_location: object

@dataclass(frozen=True)
class Location:
    location: object
    parent_body: object


@dataclass(frozen=True)
class BodyLocation(Location):
    belongs_to_body: bool

@dataclass(frozen=True)
class FieldOfViewCone:
    opening_angle: object
    body_location: object = None


@dataclass(frozen=True)
class SwitzerlandMap:
    lat_center_deg: float
    lon_center_deg: float


@dataclass(frozen=True)
class SimulationConstants:
    theta_center: object
    sat_motion_span_scale: float
    contact_margin_angle: object
    num_frames: int
    sat_z_offset: object
    animation_interval: object
    default_speed_multiplier: float
    default_body_spin_rate: object
    field_of_view_cone: FieldOfViewCone
    cone_length: object
    z_axis_length: object
    switzerland_map: SwitzerlandMap
    clouds: tuple[Cloud, ...]
    export_speed_multiplier: float
    # Rays sampled along the sensor column for camera strip cloud-blocked stats (see simulation.camera_2d).
    camera_pixel_ray_samples: int


SIMULATION = SimulationConstants(
    theta_center=90.0 * ureg.deg,
    sat_motion_span_scale=1.05,
    contact_margin_angle=0.05 * ureg.deg,
    num_frames=2000, #simulation total time / dt
    sat_z_offset=0.0 * ureg.deg,
    animation_interval=30.0 * ureg.ms,
    default_speed_multiplier=30.0,
    default_body_spin_rate=3.0 * ureg.deg / ureg.s,
    field_of_view_cone=FieldOfViewCone(
        # In the current 2D renderer, the sensor reduces to a 1D footprint line.
        # That in-plane opening is the sensor vertical FOV.
        opening_angle=pinhole_full_fov_rad(
            sensor_dim=SENSOR_HEIGHT, focal_length=FOCAL_LENGTH
        ),
    ),
    cone_length=20000.0 * ureg.km,
    z_axis_length=180.0 * ureg.km,
    switzerland_map=SwitzerlandMap(
        lat_center_deg=46.80,
        lon_center_deg=8.20,
    ),
    clouds=(
        Cloud(
            height=15.0 * ureg.km,
            start_location=89.99 * ureg.deg,
            end_location=90.2 * ureg.deg,
        ),
    ),
    export_speed_multiplier=30.0,
    camera_pixel_ray_samples=96,
)
