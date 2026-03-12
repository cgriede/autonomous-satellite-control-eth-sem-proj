from dataclasses import dataclass

from .UNIT_REGISTRY import UREG as ureg


@dataclass(frozen=True)
class SimulationConstants:
    theta_center: object
    start_angle: object
    end_angle: object
    sat_motion_span_scale: float
    contact_margin_angle: object
    num_frames: int
    sat_z_offset: object
    animation_interval: object
    default_speed_multiplier: float
    default_body_spin_rate: object
    cone_opening: object
    cone_length_scale: float
    z_axis_length: object
    cloud_altitude: object
    cloud_start_angle: object
    cloud_end_angle: object
    export_speed_multiplier: float


SIMULATION = SimulationConstants(
    theta_center=90.0 * ureg.deg,
    start_angle=-5.0 * ureg.deg,
    end_angle=5.0 * ureg.deg,
    sat_motion_span_scale=1.5,
    contact_margin_angle=2.0 * ureg.deg,
    num_frames=300,
    sat_z_offset=0.0 * ureg.deg,
    animation_interval=30.0 * ureg.ms,
    default_speed_multiplier=30.0,
    default_body_spin_rate=3.0 * ureg.arcminute / ureg.s,
    cone_opening=0.1 * ureg.deg,
    cone_length_scale=1.1,
    z_axis_length=180.0 * ureg.km,
    cloud_altitude=15.0 * ureg.km,
    cloud_start_angle=0.0 * ureg.deg,
    cloud_end_angle=0.5 * ureg.deg,
    export_speed_multiplier=30.0,
)
