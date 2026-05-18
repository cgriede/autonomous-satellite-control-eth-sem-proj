from dataclasses import dataclass

from .UNIT_REGISTRY import UREG as ureg


@dataclass(frozen=True)
class ObservationTarget:
    angle: object
    label: str = "target"


@dataclass(frozen=True)
class ObservationTargetArea:
    lat_min: object
    lat_max: object
    lon_min: object
    lon_max: object
    label: str = "target_area"
    # Short-lived compatibility bridge while camera kernels still consume in-plane angle.
    legacy_orbital_angle: object = 90.0 * ureg.deg


SATELLITE_ALTITUDE_LOWER_BOUND = 510 * ureg.km
SATELLITE_ALTITUDE_UPPER_BOUND = 570 * ureg.km

# 2D simulation / z=0 plane: target as a circular-arc "stripe" on the Earth disk.
# Endpoints are geodetic (lat, lon); `OBSERVATION_TARGET_STRIPE_PLANE_Z_M` documents the
# equatorial slice used by `SimulationStepper` ground traces (no literal z in 2D kinematics).
OBSERVATION_TARGET_STRIPE_PLANE_Z_M = 0.0 * ureg.m
OBSERVATION_TARGET_STRIPE_START_LAT = 0.0 * ureg.deg
OBSERVATION_TARGET_STRIPE_START_LON = 85.0 * ureg.deg
OBSERVATION_TARGET_STRIPE_END_LAT = 0.0 * ureg.deg
OBSERVATION_TARGET_STRIPE_END_LON = 95.0 * ureg.deg

# Legacy bbox form: thin equatorial band consistent with the stripe (for tests / adapters).
OBSERVATION_TARGET_AREAS: tuple[ObservationTargetArea, ...] = (
    ObservationTargetArea(
        lat_min=-0.5 * ureg.deg,
        lat_max=0.5 * ureg.deg,
        lon_min=OBSERVATION_TARGET_STRIPE_START_LON,
        lon_max=OBSERVATION_TARGET_STRIPE_END_LON,
        label="primary_stripe",
        legacy_orbital_angle=90.0 * ureg.deg,
    ),
)

# Compatibility adapter for existing in-plane camera target call sites.
OBSERVATION_TARGETS: tuple[ObservationTarget, ...] = (
    ObservationTarget(
        angle=OBSERVATION_TARGET_AREAS[0].legacy_orbital_angle,
        label=OBSERVATION_TARGET_AREAS[0].label,
    ),
)

