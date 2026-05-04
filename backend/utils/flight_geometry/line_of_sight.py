import numpy as np

from environment_definition.constants.EARTH import EARTH_RADIUS
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from utils.leo_adapter import (
    minimum_contact_angle_from_heights,
    satellite_horizon_geometry,
)

def satellite_horizon_los(observer_height: float, orbit_height: float) -> dict:
    """
    Calculate line-of-sight geometry from a satellite to Earth's horizon.
    
    Returns angles and distances useful for visibility / camera pointing.
    
    Args:
        observer_height:  height of observer above surface [km] (0 = surface)
        orbit_height:     satellite height above surface [km]
    
    Returns:
        dict with:
            - central_angle_deg        → Earth central angle to horizon [°]
            - horizon_angle_sat_deg    → angle at satellite between nadir and horizon LOS [°]
            - grazing_angle_deg        → angle between LOS and local horizontal at tangent point [°]
            - slant_range_km           → distance from satellite to horizon tangent point [km]
            - max_off_nadir_deg        → maximum off-nadir angle for seeing surface [°]
    """
    return satellite_horizon_geometry(
        observer_height=observer_height,
        orbit_height=orbit_height,
        default_r_earth=EARTH_RADIUS,
        ureg=ureg,
    )


def minimum_contact_angle(observer_height: float, orbit_height: float):
    """
    Minimum contact half-angle:
        alpha = arctan(slant_range / R_earth)
    Returns a Pint angle quantity.
    """
    return minimum_contact_angle_from_heights(
        observer_height=observer_height,
        orbit_height=orbit_height,
        default_r_earth=EARTH_RADIUS,
        ureg=ureg,
    )


def subsatellite_latitude_deg_polar_meridian(
    theta_orbit_rad: np.ndarray | float,
    *,
    theta_center_rad: float,
) -> np.ndarray | float:
    """
    Geodetic latitude (degrees) for the polar meridian / orbit-disk model.

    Orbit angle ``theta_orbit_rad`` advances around the circular cross-section with
    ``theta_center_rad`` at the north pole (λ = 90°). Past the pole, latitude decreases
    symmetrically: λ = 90° − |Δθ| with Δθ wrapped to (−π, π].
    """
    arr = np.asarray(theta_orbit_rad, dtype=float)
    dtheta = arr - float(theta_center_rad)
    delta_wrapped = np.arctan2(np.sin(dtheta), np.cos(dtheta))
    delta_deg = np.rad2deg(delta_wrapped)
    out = np.clip(90.0 - np.abs(delta_deg), -90.0, 90.0)
    if np.ndim(theta_orbit_rad) == 0:
        return float(out)
    return out.astype(float)


if __name__ == "__main__":
    # ────────────────────────────────────────────────
    # Quick usage examples

    from environment_definition.constants import UREG as ureg
    from rich.pretty import pprint
    # Example: from ground observer looking up to satellite horizon
    pprint(satellite_horizon_los(450.0 * ureg.m, 550.0 * ureg.km))