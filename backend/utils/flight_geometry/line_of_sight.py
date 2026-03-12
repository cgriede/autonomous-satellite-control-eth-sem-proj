import numpy as np

from backend.environment_definition.constants import EARTH_RADIUS

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
    # Effective radii
    r_earth   = EARTH_RADIUS
    r_observer = r_earth + observer_height
    r_sat     = r_earth + orbit_height
    
    # Prevent invalid geometry
    if r_sat <= r_observer:
        raise ValueError("Satellite must be higher than observer")
    
    # Earth central angle to horizon tangent point (η)
    cos_eta = r_earth / r_sat
    eta_rad = np.arccos(cos_eta)
    eta_deg = np.degrees(eta_rad)
    
    # Horizon angle at satellite (angle between nadir and LOS to horizon)
    sin_theta = r_earth / r_sat
    theta_rad = np.arcsin(sin_theta)
    theta_deg = np.degrees(theta_rad)
    
    # Alternative: theta = 90° - eta  (in the limit observer_height=0)
    # But we keep the clean trig version above
    
    # Slant range to horizon tangent point
    slant_range = np.sqrt(r_sat**2 + r_earth**2 - 2 * r_sat * r_earth * cos_eta)
    
    # Grazing / depression angle at tangent point
    # (angle between LOS and local tangent plane ≈ 0° for pure geometric horizon)
    grazing_arg = (r_sat / slant_range) * np.sin(theta_rad)
    grazing_rad = np.arcsin(grazing_arg)
    grazing_deg = np.degrees(grazing_rad) - 90.0   # usually very small negative
    
    # For observer at height > 0 → visibility cone is slightly different
    # Here we give the satellite-to-horizon values (most common use case)
    
    return {
        "central_angle_deg": eta_deg,               # angle at Earth center
        "horizon_angle_sat_deg": theta_deg,         # most useful for camera tilt
        "max_off_nadir_deg": theta_deg,             # synonym in many contexts
        "slant_range_km": slant_range,
        "grazing_angle_deg": grazing_deg,           # near 0 for geometric case
        # Bonus: approximate max Earth disk angular diameter from sat
        "earth_angular_diameter_deg": 2 * theta_deg
    }


def minimum_contact_angle(observer_height: float, orbit_height: float):
    """
    Minimum contact half-angle:
        alpha = arctan(slant_range / R_earth)
    Returns a Pint angle quantity.
    """
    los = satellite_horizon_los(observer_height=observer_height, orbit_height=orbit_height)
    slant_range = los["slant_range_km"]
    alpha = np.arctan(slant_range / EARTH_RADIUS)
    return alpha

if __name__ == "__main__":
    # ────────────────────────────────────────────────
    # Quick usage examples

    from backend.environment_definition.constants import UREG as ureg
    from rich.pretty import pprint
    # Example: from ground observer looking up to satellite horizon
    pprint(satellite_horizon_los(450.0 * ureg.m, 550.0 * ureg.km))