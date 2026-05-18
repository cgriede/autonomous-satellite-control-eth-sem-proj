from dataclasses import dataclass
from typing import Any

from .UNIT_REGISTRY import UREG as ureg
from utils.flight_geometry.line_of_sight import minimum_contact_angle


@dataclass(frozen=True)
class ObservationTargetArea:
    lat_min: Any
    lat_max: Any
    label: str = "target_area"


SATELLITE_ALTITUDE_LOWER_BOUND = 510 * ureg.km
SATELLITE_ALTITUDE_UPPER_BOUND = 570 * ureg.km

LON_GLOBAL = 0.0 * ureg.deg
# 2D polar-orbit convention: longitude is fixed to 0 and the target spans latitude.
OBSERVATION_TARGET_STRIPE_START_LAT = 89.65 * ureg.deg
OBSERVATION_TARGET_STRIPE_END_LAT = 90.0 * ureg.deg

# Latitude-band target area used by the camera and reward code.
OBSERVATION_TARGET_AREAS: tuple[ObservationTargetArea, ...] = (
    ObservationTargetArea(
        lat_min=OBSERVATION_TARGET_STRIPE_START_LAT,
        lat_max=OBSERVATION_TARGET_STRIPE_END_LAT,
        label="primary_stripe",
    ),
)


def primary_observation_target_area() -> ObservationTargetArea:
    return OBSERVATION_TARGET_AREAS[0]


def mission_target_window_deg(
    *,
    orbit_height: Any,
    margin_deg: float = 0.0,
    observer_height: Any = 0.0 * ureg.km,
    area: ObservationTargetArea | None = None,
) -> tuple[float, float]:
    target_area = primary_observation_target_area() if area is None else area
    lat_min_deg = float(target_area.lat_min.to(ureg.deg).magnitude)
    lat_max_deg = float(target_area.lat_max.to(ureg.deg).magnitude)
    contact_half_angle_deg = float(
        minimum_contact_angle(observer_height=observer_height, orbit_height=orbit_height)
        .to(ureg.deg)
        .magnitude
    )
    margin = float(margin_deg)
    return lat_max_deg - contact_half_angle_deg - margin, lat_min_deg + contact_half_angle_deg + margin
