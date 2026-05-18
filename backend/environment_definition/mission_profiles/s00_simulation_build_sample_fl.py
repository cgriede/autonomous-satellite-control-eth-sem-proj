"""
This mission (M1) is specified as follows:
- Satellite altitude is sampled within configured bounds.
- Satellite should maximize time where camera faces observer directly.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from environment_definition.constants import (
    EARTH_GRAVITATIONAL_PARAMETER,
    EARTH_RADIUS,
    MOMENT_OF_INERTIA_2D,
    REACTION_WHEEL_MAX_MOMENTUM,
    REACTION_WHEEL_MAX_TORQUE,
    RENDER,
    SATELLITE_ALTITUDE_LOWER_BOUND,
    SATELLITE_ALTITUDE_UPPER_BOUND,
    SATELLITE_MASS,
    SIMULATION,
    STAR_TRACKER_MAX_MANEUVER_RATE,
)
from utils.leo_adapter.orbit_geometry import circular_orbital_speed_from_altitude
from environment_definition.runtime_types import Mission, MissionScenario, Satellite

_LOWER_MAG = SATELLITE_ALTITUDE_LOWER_BOUND.magnitude
_UPPER_MAG = SATELLITE_ALTITUDE_UPPER_BOUND.to(SATELLITE_ALTITUDE_LOWER_BOUND.units).magnitude


def sample_satellite_altitude(
    *,
    seed: int | None = None,
    rng: np.random.Generator | None = None,
) -> Any:
    """Runtime-seeded altitude sampler; avoids hidden import-time randomness."""
    if rng is None:
        rng = np.random.default_rng(seed)
    sampled = float(rng.uniform(_LOWER_MAG, _UPPER_MAG))
    return sampled * SATELLITE_ALTITUDE_LOWER_BOUND.units


# Deterministic module default for compatibility with existing imports.
SATELLITE_ALTITUDE = sample_satellite_altitude(seed=0)

SATELLITE_ORBIT_SPEED = circular_orbital_speed_from_altitude(SATELLITE_ALTITUDE)

SATELLITE = Satellite(
    mass=SATELLITE_MASS,
    star_tracker_max_maneuver_rate=STAR_TRACKER_MAX_MANEUVER_RATE,
    moment_of_inertia_2d=MOMENT_OF_INERTIA_2D,
    reaction_wheel_max_torque=REACTION_WHEEL_MAX_TORQUE,
    reaction_wheel_max_momentum=REACTION_WHEEL_MAX_MOMENTUM,
)

MISSION_PROFILE = Mission(
    altitude_lower_bound=SATELLITE_ALTITUDE_LOWER_BOUND,
    altitude_upper_bound=SATELLITE_ALTITUDE_UPPER_BOUND,
    sampled_altitude=SATELLITE_ALTITUDE,
    orbit_speed=SATELLITE_ORBIT_SPEED,
)

MISSION_SCENARIO = MissionScenario(
    earth_radius=EARTH_RADIUS,
    earth_gravitational_parameter=EARTH_GRAVITATIONAL_PARAMETER,
    simulation=SIMULATION,
    render=RENDER,
)

if __name__ == "__main__":
    print(f"Sampling satellite altitude from {SATELLITE_ALTITUDE_LOWER_BOUND} to {SATELLITE_ALTITUDE_UPPER_BOUND}")
    print(SATELLITE_ALTITUDE)
    print(f"Satellite orbit speed: {SATELLITE_ORBIT_SPEED}")