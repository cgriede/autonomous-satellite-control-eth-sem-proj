from pymap3d.ellipsoid import Ellipsoid

from .UNIT_REGISTRY import UREG as ureg

# Baseline orbit/planet constants currently used in visualizations.
AVERAGE_EARTH_RADIUS = 6371.0088 * ureg.km
EARTH_RADIUS = AVERAGE_EARTH_RADIUS
EARTH_GRAVITATIONAL_PARAMETER = 398600.4418 * ureg.km**3 / ureg.s**2

# WGS84 reference ellipsoid (meters) for Vincenty geodesics, ENU/LLA, and ``lookAtSpheroid``.
WGS84_ELLIPSOID = Ellipsoid.from_name("wgs84")
