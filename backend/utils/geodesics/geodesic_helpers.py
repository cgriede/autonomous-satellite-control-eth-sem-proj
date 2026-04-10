"""Ellipsoidal geodesic helpers (WGS84 via ``environment_definition.constants.geod``)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from environment_definition.constants.EARTH import geod as default_geod
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from utils.units.require_compatible_unit import require_compatible_units

if TYPE_CHECKING:
    from pint import Quantity
    from pyproj import Geod


def east_north_km_to_lon_lat(
    lon0: Quantity,
    lat0: Quantity,
    east: Quantity,
    north: Quantity,
    *,
    geod: Geod | None = None,
) -> tuple[Quantity, Quantity]:
    """
    Map a local east/north offset from ``(lon0, lat0)`` to geodetic coordinates.

    Uses two ``Geod.fwd`` legs (north, then east) on the reference ellipsoid.
    ``east`` / ``north`` accept any length dimension (e.g. km or m).

    Returns:
        ``(lat, lon)`` as angle quantities (degrees internally).
    """
    require_compatible_units(lon0, "radian", "lon0")
    require_compatible_units(lat0, "radian", "lat0")
    require_compatible_units(east, "meter", "east")
    require_compatible_units(north, "meter", "north")
    g = default_geod if geod is None else geod

    lon0_deg = float(lon0.to(ureg.deg).magnitude)
    lat0_deg = float(lat0.to(ureg.deg).magnitude)
    north_m = float(north.to(ureg.m).magnitude)
    east_m = float(east.to(ureg.m).magnitude)

    lon1_deg, lat1_deg, _back1 = g.fwd(lon0_deg, lat0_deg, 0.0, north_m)
    lon2_deg, lat2_deg, _back2 = g.fwd(lon1_deg, lat1_deg, 90.0, east_m)

    return lat2_deg * ureg.deg, lon2_deg * ureg.deg


def geodesic_distance(
    lon1: Quantity,
    lat1: Quantity,
    lon2: Quantity,
    lat2: Quantity,
    *,
    geod: Geod | None = None,
) -> Quantity:
    """Ellipsoidal geodesic distance between two lon/lat points."""
    require_compatible_units(lon1, "radian", "lon1")
    require_compatible_units(lat1, "radian", "lat1")
    require_compatible_units(lon2, "radian", "lon2")
    require_compatible_units(lat2, "radian", "lat2")
    g = default_geod if geod is None else geod

    a1 = float(lon1.to(ureg.deg).magnitude)
    b1 = float(lat1.to(ureg.deg).magnitude)
    a2 = float(lon2.to(ureg.deg).magnitude)
    b2 = float(lat2.to(ureg.deg).magnitude)

    _az12, _az21, dist_m = g.inv(a1, b1, a2, b2)
    return float(dist_m) * ureg.m


def sigma_deg_to_meters_north(
    lon: Quantity,
    lat: Quantity,
    sigma_deg: Quantity,
    *,
    geod: Geod | None = None,
) -> Quantity:
    """
    Geodesic length of a northward ``sigma_deg`` span at ``(lon, lat)``.

    Used to translate an old degree-space Gaussian width to meters on the ellipsoid.
    """
    require_compatible_units(lon, "radian", "lon")
    require_compatible_units(lat, "radian", "lat")
    require_compatible_units(sigma_deg, "radian", "sigma_deg")
    g = default_geod if geod is None else geod

    lon_d = float(lon.to(ureg.deg).magnitude)
    lat_d = float(lat.to(ureg.deg).magnitude)
    sig_d = float(sigma_deg.to(ureg.deg).magnitude)

    _az12, _az21, dist_m = g.inv(lon_d, lat_d, lon_d, lat_d + sig_d)
    return abs(float(dist_m)) * ureg.m
