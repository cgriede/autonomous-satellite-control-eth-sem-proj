"""
This mission (M1) is specified as follows:
- Satellite is launched at a random altitude between upper
 and lower bound of possible sattelite altitide
- Satellite should maximize time where camera faces observer directly

"""

import numpy as np
from pathlib import Path
import sys

try:
    from backend.environment_definition.constants import (
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
    from backend.utils.orbit_propagator.circular_orbit_speed import circular_orbital_speed
    from backend.environment_definition.runtime_types import Environment, Mission, Satellite
except ModuleNotFoundError:
    repo_root = str(Path(__file__).resolve().parents[3])
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    from backend.environment_definition.constants import (
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
    from backend.utils.orbit_propagator.circular_orbit_speed import circular_orbital_speed
    from backend.environment_definition.runtime_types import Environment, Mission, Satellite

lower_mag = SATELLITE_ALTITUDE_LOWER_BOUND.magnitude
upper_mag = SATELLITE_ALTITUDE_UPPER_BOUND.to(SATELLITE_ALTITUDE_LOWER_BOUND.units).magnitude
SATELLITE_ALTITUDE = np.random.uniform(lower_mag, upper_mag) * SATELLITE_ALTITUDE_LOWER_BOUND.units

SATELLITE_ORBIT_SPEED = circular_orbital_speed(SATELLITE_ALTITUDE)

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

ENVIRONMENT = Environment(
    earth_radius=EARTH_RADIUS,
    earth_gravitational_parameter=EARTH_GRAVITATIONAL_PARAMETER,
    simulation=SIMULATION,
    render=RENDER,
)

if __name__ == "__main__":
    print(f"Sampling satellite altitude from {SATELLITE_ALTITUDE_LOWER_BOUND} to {SATELLITE_ALTITUDE_UPPER_BOUND}")
    print(SATELLITE_ALTITUDE)
    print(f"Satellite orbit speed: {SATELLITE_ORBIT_SPEED}")