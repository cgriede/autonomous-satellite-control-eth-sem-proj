"""
Canonical pole-meridian ↔ orbit-disk ↔ geodetic conversions for the simulation plane.

Track offset ``δ`` (degrees) is along-track distance from the north pole in the locked
``y_ecef = 0`` orbit-disk model:

- ``δ ≤ 0``: ascending leg, ``λ = lon_ascending`` (default ``LON_GLOBAL`` = 0°)
- ``δ > 0``: descending leg, ``λ = lon_ascending ± 180°``
- Disk polar angle ``φ_deg = theta_center_deg + δ`` (default ``theta_center = 90°``)

Use this module for clouds, targets, and mission stripe geometry — not the renderer's
north-polar azimuthal map in ``geodesic_helpers.polar_azimuthal_plane_xy_km_to_lon_lat_deg``.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from pymap3d.ecef import geodetic2ecef

from environment_definition.constants.EARTH import WGS84_ELLIPSOID
from environment_definition.constants.MISSION import LON_GLOBAL
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from utils.geodesics.geodesic_helpers import _normalize_lon_deg
from utils.geometry.polar_meridian_track import (
    lat_deg_from_track_offset_deg,
    phi_deg_from_track_offset_deg,
)
from utils.units.require_compatible_unit import require_compatible_units

_MERIDIAN_LON_TOL_DEG = 1e-3


def _lon_ascending_deg(lon_ascending: Any | None) -> float:
    if lon_ascending is None:
        return float(LON_GLOBAL.to(ureg.deg).magnitude)
    require_compatible_units(lon_ascending, ureg.deg, "lon_ascending")
    return _normalize_lon_deg(float(lon_ascending.to(ureg.deg).magnitude))


def lon_deg_from_track_offset_deg(
    offset_deg: float,
    *,
    lon_ascending: Any | None = None,
) -> float:
    """Meridian longitude for track offset ``δ`` on the Greenwich orbital plane."""
    lon_asc = _lon_ascending_deg(lon_ascending)
    if float(offset_deg) > 0.0:
        return _normalize_lon_deg(lon_asc + 180.0)
    return lon_asc


def geodetic_deg_from_track_offset_deg(
    offset_deg: float,
    *,
    lon_ascending: Any | None = None,
) -> tuple[float, float]:
    """Return ``(lat_deg, lon_deg)`` for track offset ``δ``."""
    lat_deg = lat_deg_from_track_offset_deg(float(offset_deg))
    lon_deg = lon_deg_from_track_offset_deg(float(offset_deg), lon_ascending=lon_ascending)
    return lat_deg, lon_deg


def track_offset_deg_from_geodetic_deg(
    lat_deg: float,
    lon_deg: float,
    *,
    lon_ascending: Any | None = None,
    lon_tol_deg: float = _MERIDIAN_LON_TOL_DEG,
) -> float:
    """
    Inverse of :func:`geodetic_deg_from_track_offset_deg` on the meridian plane only.

    Raises ``ValueError`` if ``lon`` is not on the ascending or descending meridian.
    """
    lat = float(lat_deg)
    lon_n = _normalize_lon_deg(float(lon_deg))
    lon_asc = _lon_ascending_deg(lon_ascending)

    if abs(lat - 90.0) <= lon_tol_deg:
        return 0.0

    on_ascending = abs(lon_n - lon_asc) <= lon_tol_deg
    lon_desc = _normalize_lon_deg(lon_asc + 180.0)
    on_descending = abs(lon_n - lon_desc) <= lon_tol_deg

    if on_ascending and not on_descending:
        return lat - 90.0
    if on_descending and not on_ascending:
        return 90.0 - lat
    if on_ascending and on_descending:
        return 0.0

    raise ValueError(
        f"geodetic ({lat_deg}, {lon_deg}) is not on the pole meridian plane "
        f"(expected lon near {lon_asc}° or {lon_desc}°)."
    )


def disk_phi_deg_from_track_offset_deg(
    offset_deg: float,
    *,
    theta_center_deg: float = 90.0,
) -> float:
    """Orbit-disk polar angle ``φ`` (degrees) for track offset ``δ``."""
    return phi_deg_from_track_offset_deg(float(offset_deg), theta_center_deg=theta_center_deg)


def track_offset_deg_from_disk_phi_deg(
    phi_deg: float,
    *,
    theta_center_deg: float = 90.0,
) -> float:
    """Track offset ``δ = φ − theta_center`` (simulation disk angle, not renderer azimuth)."""
    return float(phi_deg) - float(theta_center_deg)


def geodetic_deg_from_disk_phi_deg(
    phi_deg: float,
    *,
    theta_center_deg: float = 90.0,
    lon_ascending: Any | None = None,
) -> tuple[float, float]:
    """``(lat_deg, lon_deg)`` from orbit-disk polar angle ``φ``."""
    offset_deg = track_offset_deg_from_disk_phi_deg(phi_deg, theta_center_deg=theta_center_deg)
    return geodetic_deg_from_track_offset_deg(offset_deg, lon_ascending=lon_ascending)


def disk_phi_deg_from_geodetic_deg(
    lat_deg: float,
    lon_deg: float,
    *,
    ell: Any | None = None,
) -> float:
    """Orbit-disk ``φ = atan2(z, x)`` for surface geodetic on the meridian plane."""
    e = WGS84_ELLIPSOID if ell is None else ell
    x_m, _y_m, z_m = geodetic2ecef(float(lat_deg), float(lon_deg), 0.0, ell=e, deg=True)
    return float(np.rad2deg(np.arctan2(float(z_m), float(x_m))))


def geodetic_lonlat_deg(location: Any) -> tuple[float, float]:
    """Extract ``(lat_deg, lon_deg)`` from a :class:`~environment_definition.constants.SIMULATION.GeodeticLonLat`."""
    lat_q = getattr(location, "lat", None)
    lon_q = getattr(location, "lon", None)
    if lat_q is None or lon_q is None:
        raise ValueError("location must provide lat and lon (e.g. GeodeticLonLat).")
    require_compatible_units(lat_q, ureg.deg, "lat")
    require_compatible_units(lon_q, ureg.deg, "lon")
    return float(lat_q.to(ureg.deg).magnitude), float(lon_q.to(ureg.deg).magnitude)


def track_offset_deg_from_disk_xy_km(
    xy_km: np.ndarray,
    *,
    ell: Any | None = None,
) -> float:
    """Along-track offset δ [deg] for a subsatellite / ground point on the orbit disk."""
    from utils.geometry.orbit_disk_wgs84 import disk_xy_km_to_geodetic_deg

    lon_deg, lat_deg = disk_xy_km_to_geodetic_deg(np.asarray(xy_km, dtype=float), ell=ell)
    return track_offset_deg_from_geodetic_deg(float(lat_deg), float(lon_deg))


def track_offset_deg_from_latitude_only_deg(lat_deg: float) -> float:
    """
    Map latitude [deg] to track offset when longitude is implied by the meridian rule.

    Values ``> 90°`` are treated as ``90° + δ`` (offset past pole encoded in a latitude field).
    """
    val = float(lat_deg)
    if val > 90.0:
        return val - 90.0
    return val - 90.0


def cloud_disk_phi_bounds_deg(cloud: Any) -> tuple[float, float]:
    """Orbit-disk φ bounds [deg] for a :class:`~environment_definition.constants.SIMULATION.Cloud`."""
    lat_s, lon_s = geodetic_lonlat_deg(cloud.start_location)
    lat_e, lon_e = geodetic_lonlat_deg(cloud.end_location)
    phi_s = disk_phi_deg_from_geodetic_deg(lat_s, lon_s)
    phi_e = disk_phi_deg_from_geodetic_deg(lat_e, lon_e)
    return min(phi_s, phi_e), max(phi_s, phi_e)


def cloud_mean_altitude_km(cloud: Any) -> float:
    """Mid-altitude of a cloud slab [km] for circular arc radius in the orbit-disk model."""
    require_compatible_units(cloud.base_altitude, ureg.km, "base_altitude")
    require_compatible_units(cloud.top_altitude, ureg.km, "top_altitude")
    base_km = float(cloud.base_altitude.to(ureg.km).magnitude)
    top_km = float(cloud.top_altitude.to(ureg.km).magnitude)
    if top_km < base_km:
        base_km, top_km = top_km, base_km
    return 0.5 * (base_km + top_km)

