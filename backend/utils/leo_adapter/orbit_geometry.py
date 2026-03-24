import numpy as np

from environment_definition.constants import EARTH_GRAVITATIONAL_PARAMETER, EARTH_RADIUS
from environment_definition.constants import UREG as ureg


def circular_orbital_speed_from_altitude(altitude):
    """
    Compute circular orbital speed from project-provided constants.
    """
    mu, r_earth = EARTH_GRAVITATIONAL_PARAMETER, EARTH_RADIUS
    r = r_earth + altitude
    return np.sqrt(mu / r)


def satellite_horizon_geometry(observer_height, orbit_height, default_r_earth, ureg):
    """
    Compute line-of-sight geometry from project-provided Earth radius.
    """
    r_earth = default_r_earth
    r_observer = r_earth + observer_height
    r_sat = r_earth + orbit_height
    if r_sat <= r_observer:
        raise ValueError("Satellite must be higher than observer")

    cos_eta = r_earth / r_sat
    eta_rad = np.arccos(cos_eta)
    theta_rad = np.arcsin(r_earth / r_sat)
    slant_range = np.sqrt(r_sat ** 2 + r_earth ** 2 - 2 * r_sat * r_earth * cos_eta)

    grazing_arg = (r_sat / slant_range) * np.sin(theta_rad)
    grazing_arg_mag = np.clip(grazing_arg.to_base_units().magnitude, -1.0, 1.0)
    grazing_rad = np.arcsin(grazing_arg_mag) * ureg.rad

    eta_deg = eta_rad.to(ureg.deg)
    theta_deg = theta_rad.to(ureg.deg)
    grazing_deg = grazing_rad.to(ureg.deg) - 90.0 * ureg.deg

    return {
        "central_angle_deg": eta_deg,
        "horizon_angle_sat_deg": theta_deg,
        "max_off_nadir_deg": theta_deg,
        "slant_range_km": slant_range.to(ureg.km),
        "grazing_angle_deg": grazing_deg,
        "earth_angular_diameter_deg": 2.0 * theta_deg,
    }


def minimum_contact_angle_from_heights(observer_height, orbit_height, default_r_earth, ureg):
    """
    Minimum contact half-angle alpha = arctan(slant_range / R_earth).
    """
    los = satellite_horizon_geometry(
        observer_height=observer_height,
        orbit_height=orbit_height,
        default_r_earth=default_r_earth,
        ureg=ureg,
    )
    r_earth = default_r_earth
    slant_range = los["slant_range_km"].to(r_earth.units)
    return np.arctan(slant_range / r_earth)

