from dataclasses import dataclass

from .UNIT_REGISTRY import UREG as ureg


@dataclass(frozen=True)
class ObservationTarget:
    angle: object
    label: str = "target"


SATELLITE_ALTITUDE_LOWER_BOUND = 510 * ureg.km
SATELLITE_ALTITUDE_UPPER_BOUND = 570 * ureg.km

# Current 2D mission uses a single angular target in the orbital plane.
OBSERVATION_TARGETS: tuple[ObservationTarget, ...] = (
    ObservationTarget(angle=90.0 * ureg.deg, label="primary"),
)
