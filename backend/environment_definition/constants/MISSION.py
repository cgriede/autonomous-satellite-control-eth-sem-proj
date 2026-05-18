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
# Polar episode slice (see docs/presentation): subsatellite meridian LON_GLOBAL; primary target is a
# latitude stripe. Canonical orbit-plane episode extent uses symmetric LOS θ offsets from
# ``los_theta_offsets_deg`` (aligned with the renderer). ``mission_target_window_deg`` maps expanded
# latitude bounds to θ offsets for diagnostics / stripe geometry and can be asymmetric when λ_high
# saturates at 90° N.
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


def primary_target_stripe_theta_offsets_deg() -> tuple[float, float]:
    """
    Legacy shim: θ offsets relative to ``SIMULATION.theta_center`` for polar-aligned narratives.

    Authoritative stripe polar angles on the orbit disk are ``primary_stripe_disk_phi_bounds_deg``
    (:mod:`utils.geometry.mission_stripe_disk`). When ``theta_center`` is fixed at ``90°``, this
    matches ``φ − θ_center`` from WGS84-projected stripe endpoints on ``LON_GLOBAL``.
    """
    from environment_definition.constants.SIMULATION import SIMULATION

    from utils.geometry.mission_stripe_disk import primary_stripe_disk_phi_bounds_deg

    phi_lo, phi_hi = primary_stripe_disk_phi_bounds_deg()
    tc_deg = float(SIMULATION.theta_center.to(ureg.deg).magnitude)
    return phi_lo - tc_deg, phi_hi - tc_deg


def mission_target_latitude_bounds_deg(
    *,
    orbit_height: Any,
    margin_deg: float = 0.0,
    observer_height: Any = 0.0 * ureg.km,
    area: ObservationTargetArea | None = None,
) -> tuple[float, float]:
    """Absolute geodetic latitude bounds (south extent, north extent) for the episode sweep."""
    target_area = primary_observation_target_area() if area is None else area
    lat_min_deg = float(target_area.lat_min.to(ureg.deg).magnitude)
    lat_max_deg = float(target_area.lat_max.to(ureg.deg).magnitude)
    contact_half_angle_deg = float(
        minimum_contact_angle(observer_height=observer_height, orbit_height=orbit_height)
        .to(ureg.deg)
        .magnitude
    )
    margin = float(margin_deg)
    lat_low = lat_min_deg - contact_half_angle_deg - margin
    lat_high = lat_max_deg + contact_half_angle_deg + margin
    lat_low = max(-90.0, lat_low)
    lat_high = min(90.0, lat_high)
    if lat_low > lat_high:
        lat_low, lat_high = lat_high, lat_low
    return lat_low, lat_high


def los_theta_offsets_deg(
    *,
    orbit_height: Any,
    margin_deg: float,
    observer_height: Any = 0.0 * ureg.km,
) -> tuple[float, float]:
    """
    Symmetric orbit-plane θ offsets (degrees) for `SimulationStepper` with ``theta_center = π/2``.

    Matches renderer LOS framing: ±(minimum_contact_half_angle + margin). Use this for canonical
    episode rollouts. Unlike :func:`mission_target_window_deg`, this stays symmetric at the pole.
    """
    half_deg = float(
        minimum_contact_angle(observer_height=observer_height, orbit_height=orbit_height)
        .to(ureg.deg)
        .magnitude
    )
    m = float(margin_deg)
    lo = -(half_deg + m)
    hi = half_deg + m
    return lo, hi


def mission_target_window_deg(
    *,
    orbit_height: Any,
    margin_deg: float = 0.0,
    observer_height: Any = 0.0 * ureg.km,
    area: ObservationTargetArea | None = None,
) -> tuple[float, float]:
    """
    Stripe-derived θ offsets (degrees) from expanded latitude bounds, for diagnostics:

        offset_deg ≈ λ_deg − 90°   with λ from ``mission_target_latitude_bounds_deg``.

    This transform can yield an **asymmetric** interval when ``lat_high`` saturates at 90° N.
    Canonical simulation episodes use :func:`los_theta_offsets_deg` instead (symmetric LOS).
    """
    lat_low, lat_high = mission_target_latitude_bounds_deg(
        orbit_height=orbit_height,
        margin_deg=margin_deg,
        observer_height=observer_height,
        area=area,
    )
    return lat_low - 90.0, lat_high - 90.0
