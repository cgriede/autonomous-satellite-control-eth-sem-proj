from backend.environment_definition.constants import EARTH_GRAVITATIONAL_PARAMETER, EARTH_RADIUS
import numpy as np

def circular_orbital_speed(altitude_km: float) -> float:
    """
    Returns orbital speed in km/s for circular orbit at given altitude
    The speed is relative to the ECI frame (standard non-rotating frame)
    
    Args:
        altitude_km: Altitude of the satellite in km
    Returns:
        v: Orbital speed in km/s
    """
    
    r = EARTH_RADIUS + altitude_km
    v = np.sqrt(EARTH_GRAVITATIONAL_PARAMETER / r)
    return v


if __name__ == "__main__":
    from backend.environment_definition.constants import UREG as ureg
    print("GEO orbital speed:")
    print(circular_orbital_speed(35786.0* ureg.km))