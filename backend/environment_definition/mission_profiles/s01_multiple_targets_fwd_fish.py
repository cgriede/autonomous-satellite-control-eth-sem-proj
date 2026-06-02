"""
This mission (M1) is specified as follows:
- Satellite altitude is sampled within configured bounds.
- Satellite should maximize time where the camera covers the target stripe directly.
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
from environment_definition.constants.SIMULATION import Cloud, GeodeticLonLat
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from utils.leo_adapter.orbit_geometry import circular_orbital_speed_from_altitude
from environment_definition.runtime_types import Mission, MissionScenario, Satellite
from simulation.setup_types import OrbitConfig, SimulationOverrides, EnvironmentSetup

_LOWER_MAG = SATELLITE_ALTITUDE_LOWER_BOUND.magnitude
_UPPER_MAG = SATELLITE_ALTITUDE_UPPER_BOUND.to(SATELLITE_ALTITUDE_LOWER_BOUND.units).magnitude


# S01 cloud placement (§G): target stripe 89.65°–90.0° N.
# Cloud 1 partially occludes the observation stripe; cloud 2 adds wider scene coverage.
S01_CLOUDS = (
    Cloud(
        base_altitude=8.0 * ureg.km,
        top_altitude=18.0 * ureg.km,
        start_location=GeodeticLonLat(lat=89.70 * ureg.deg, lon=0.0 * ureg.deg),
        end_location=GeodeticLonLat(lat=90.05 * ureg.deg, lon=0.0 * ureg.deg),
    ),
    Cloud(
        base_altitude=6.0 * ureg.km,
        top_altitude=15.0 * ureg.km,
        start_location=GeodeticLonLat(lat=89.55 * ureg.deg, lon=0.0 * ureg.deg),
        end_location=GeodeticLonLat(lat=89.78 * ureg.deg, lon=0.0 * ureg.deg),
    ),
)


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

def build_setup(
    *,
    seed: int | None = None,
    include_cameras: bool = True,
) -> EnvironmentSetup:
    """Build a EnvironmentSetup for the s01 mission profile.

    Configures:
    - Exact nadir initial attitude via ``sat_z_offset=0°`` (§4.0).
    - S01_CLOUDS: two static cloud patches over the target stripe (§G).
    - Dual cameras when ``include_cameras=True``: nadir primary (0° tilt) and
      forward-looking secondary (25° prograde tilt, 70° FOV) (§A).
    - ``secondary_camera_observation_line_n_bins=200`` override for dual-camera setups (§J).

    Args:
        seed: Random seed for altitude sampling. None means unseeded (different each call).
        include_cameras: When True (default), includes the primary nadir camera and a
                         secondary forward-looking camera. When False, returns bus-only
                         setup (cameras=()) for payload-agnostic experiments.

    Returns:
        An unresolved EnvironmentSetup; call .resolve() before use.
    """
    from simulation.camera_image import CameraImage, CameraMount, DEFAULT_NADIR_CAMERA

    altitude = sample_satellite_altitude(seed=seed)

    cameras: tuple = ()
    overrides: SimulationOverrides | None = None
    if include_cameras:
        # Primary nadir camera using hardware constants.
        nadir_mount = CameraMount(camera=DEFAULT_NADIR_CAMERA, tilt_off_nadir=0 * ureg.deg)
        # Secondary forward-looking camera (GoPro 4K+ mental model; TBD from datasheet).
        # Tilt = 25° prograde (§A): along-track lookahead for forward-looking coverage.
        scnd_camera = CameraImage.from_fov(
            fov_y=70 * ureg.deg,
            pixel_size=1.55 * ureg.um,
            n_pixels_x=5312,
            n_pixels_y=2988,
        )
        scnd_mount = CameraMount(camera=scnd_camera, tilt_off_nadir=25 * ureg.deg)
        cameras = (nadir_mount, scnd_mount)
        overrides = SimulationOverrides(secondary_camera_observation_line_n_bins=200)

    return EnvironmentSetup(
        satellite=SATELLITE,
        # sat_z_offset=0° → exact nadir initial attitude (§4.0): body +Z points at Earth center at orbit start.
        orbit=OrbitConfig(altitude=altitude, sat_z_offset=0 * ureg.deg),
        cameras=cameras,
        clouds=S01_CLOUDS,
        simulation_overrides=overrides,
    )


if __name__ == "__main__":
    print(f"Sampling satellite altitude from {SATELLITE_ALTITUDE_LOWER_BOUND} to {SATELLITE_ALTITUDE_UPPER_BOUND}")
    print(SATELLITE_ALTITUDE)
    print(f"Satellite orbit speed: {SATELLITE_ORBIT_SPEED}")
