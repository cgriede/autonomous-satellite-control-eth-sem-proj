from .UNIT_REGISTRY import UREG as ureg
from pyproj import Geod

# Baseline orbit/planet constants currently used in visualizations.
AVERAGE_EARTH_RADIUS = 6371.0088* ureg.km
EARTH_RADIUS = AVERAGE_EARTH_RADIUS
EARTH_GRAVITATIONAL_PARAMETER = 398600.4418* ureg.km**3/ureg.s**2

geod = Geod(ellps="WGS84")