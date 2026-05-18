"""
Mission stripe ↔ orbit-disk polar geometry (single derivation).

The simulation orbit-disk ``(x, y)`` km plane used by ``camera_2d`` matches **ECEF** axes as::

    disk_x ↔ x_ecef (km · 1000 → m),   disk_y ↔ z_ecef,   y_ecef ≡ 0

So polar angle ``φ = atan2(disk_y, disk_x)`` matches ``atan2(z, x)`` on subsatellite-sector points that
share this meridian-plane orbit model (mixed sphere orbit / ellipsoid surface per project docs).

Stripe endpoints from ``MISSION`` latitude bounds on ``LON_GLOBAL`` map through ``geodetic2ecef``
(WGS84) and this projection — shared by overlap comparator angles and Earth-rim stripe overlays.
"""

from __future__ import annotations

import numpy as np
from pymap3d.ecef import geodetic2ecef
from pymap3d.ellipsoid import Ellipsoid

from environment_definition.constants.EARTH import WGS84_ELLIPSOID
from environment_definition.constants.MISSION import LON_GLOBAL, primary_observation_target_area
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg

from utils.geometry.orbit_disk_wgs84 import KM_TO_M


def geodetic_on_lon_meridian_to_disk_polar_deg(
    *,
    lat_deg: float,
    lon_deg: float,
    ell: Ellipsoid | None = None,
) -> float:
    """Return ``φ = atan2(z, x)`` in degrees for ``(lat, lon, h=0)`` on the reference ellipsoid."""
    e = WGS84_ELLIPSOID if ell is None else ell
    x_m, _y_m, z_m = geodetic2ecef(lat_deg, lon_deg, 0.0, ell=e, deg=True)
    return float(np.rad2deg(np.arctan2(float(z_m), float(x_m))))


def primary_stripe_disk_phi_bounds_deg(*, ell: Ellipsoid | None = None) -> tuple[float, float]:
    """Minor stripe arc bounds on the orbit-disk polar coordinate ``φ`` (degrees)."""
    area = primary_observation_target_area()
    lon_deg = float(LON_GLOBAL.to(ureg.deg).magnitude)
    lat_min_deg = float(area.lat_min.to(ureg.deg).magnitude)
    lat_max_deg = float(area.lat_max.to(ureg.deg).magnitude)
    phi_a = geodetic_on_lon_meridian_to_disk_polar_deg(lat_deg=lat_min_deg, lon_deg=lon_deg, ell=ell)
    phi_b = geodetic_on_lon_meridian_to_disk_polar_deg(lat_deg=lat_max_deg, lon_deg=lon_deg, ell=ell)
    return min(phi_a, phi_b), max(phi_a, phi_b)


def stripe_mid_observer_disk_xy_km_on_sphere(*, earth_radius_km: float, ell: Ellipsoid | None = None) -> np.ndarray:
    """
    Reference rim observer on the **mean rendering sphere** toward ``SIMULATION`` LOS art.

    LLA uses stripe midpoint latitude on ``LON_GLOBAL``, ECEF projection, then radial normalization
    to ``earth_radius_km`` so overlays stay consistent with circular Earth artwork.
    """
    e = WGS84_ELLIPSOID if ell is None else ell
    area = primary_observation_target_area()
    lon_deg = float(LON_GLOBAL.to(ureg.deg).magnitude)
    lat_mid_deg = 0.5 * (
        float(area.lat_min.to(ureg.deg).magnitude) + float(area.lat_max.to(ureg.deg).magnitude)
    )
    x_m, _y_m, z_m = geodetic2ecef(lat_mid_deg, lon_deg, 0.0, ell=e, deg=True)
    xy = np.array([float(x_m), float(z_m)], dtype=float) / KM_TO_M
    norm = float(np.linalg.norm(xy))
    rr = float(earth_radius_km)
    if norm <= 0.0 or rr <= 0.0:
        return np.array([0.0, rr], dtype=float)
    return xy * (rr / norm)
