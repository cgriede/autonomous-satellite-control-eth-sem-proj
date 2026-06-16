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

from utils.geometry.orbit_disk_polar_meridian import (
    disk_phi_deg_from_geodetic_deg,
    disk_phi_deg_from_track_offset_deg,
    geodetic_deg_from_track_offset_deg,
    track_offset_deg_from_geodetic_deg,
    track_offset_deg_from_latitude_only_deg,
)

from utils.geometry.orbit_disk_wgs84 import KM_TO_M


def _area_endpoint_geodetic_deg(
    area: Any,
    *,
    which: str,
) -> tuple[float, float]:
    """Resolve ``lat_min`` or ``lat_max`` on an ``ObservationTargetArea`` to ``(lat, lon)``."""
    if which == "min":
        lat_deg = float(area.lat_min.to(ureg.deg).magnitude)
        lon_q = getattr(area, "lat_min_lon", None)
    elif which == "max":
        lat_deg = float(area.lat_max.to(ureg.deg).magnitude)
        lon_q = getattr(area, "lat_max_lon", None)
    else:
        raise ValueError("which must be 'min' or 'max'.")
    if lon_q is not None:
        lon_deg = float(lon_q.to(ureg.deg).magnitude)
        return lat_deg, lon_deg
    offset_deg = track_offset_deg_from_latitude_only_deg(lat_deg)
    return geodetic_deg_from_track_offset_deg(offset_deg)


def target_areas_track_offset_ranges_deg(target_areas: tuple) -> tuple[tuple[float, float], ...]:
    """Per-area track-offset δ bounds [deg] for pole-meridian target hit tests."""
    ranges: list[tuple[float, float]] = []
    for area in target_areas:
        if getattr(area, "lat_min_lon", None) is not None:
            lat_a, lon_a = _area_endpoint_geodetic_deg(area, which="min")
            lat_b, lon_b = _area_endpoint_geodetic_deg(area, which="max")
            off_a = track_offset_deg_from_geodetic_deg(lat_a, lon_a)
            off_b = track_offset_deg_from_geodetic_deg(lat_b, lon_b)
        else:
            lat_lo = float(area.lat_min.to(ureg.deg).magnitude)
            lat_hi = float(area.lat_max.to(ureg.deg).magnitude)
            off_a = track_offset_deg_from_latitude_only_deg(lat_lo)
            off_b = track_offset_deg_from_latitude_only_deg(lat_hi)
        ranges.append((min(off_a, off_b), max(off_a, off_b)))
    return tuple(ranges)


def geodetic_deg_in_target_areas(
    *,
    lon_deg: float,
    lat_deg: float,
    offset_ranges: tuple[tuple[float, float], ...],
) -> bool:
    """True when geodetic (lon, lat) lies in any target area on the meridian model."""
    return geodetic_target_area_index(
        lon_deg=lon_deg,
        lat_deg=lat_deg,
        offset_ranges=offset_ranges,
    ) is not None


def geodetic_target_area_index(
    *,
    lon_deg: float,
    lat_deg: float,
    offset_ranges: tuple[tuple[float, float], ...],
) -> int | None:
    """Index of the first target area containing ``(lon, lat)``, or ``None``."""
    try:
        off = track_offset_deg_from_geodetic_deg(lat_deg, lon_deg)
    except ValueError:
        return None
    for i, (lo, hi) in enumerate(offset_ranges):
        if lo <= off <= hi:
            return int(i)
    return None


def classify_earth_hit_observation_code(
    hit_xy_km: np.ndarray,
    *,
    target_areas: tuple,
    earth_code: int,
    target_code: int | None = None,
) -> int:
    """Earth-hit code: indexed target T0..Tn when inside a configured area, else earth."""
    from environment_definition.constants.observation_codes import observation_target_code_for_index
    from utils.geometry.orbit_disk_wgs84 import disk_xy_km_to_geodetic_deg

    _ = target_code  # legacy callers passed OBSERVATION_TARGET (= T0 base); index selects code.
    ranges = target_areas_track_offset_ranges_deg(target_areas)
    lon_deg, lat_deg = disk_xy_km_to_geodetic_deg(np.asarray(hit_xy_km, dtype=float))
    idx = geodetic_target_area_index(lon_deg=lon_deg, lat_deg=lat_deg, offset_ranges=ranges)
    if idx is not None:
        return int(observation_target_code_for_index(idx))
    return int(earth_code)


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


def target_areas_disk_phi_bounds_deg(
    target_areas: tuple,
    *,
    lon_deg: float | None = None,
    ell: Ellipsoid | None = None,
) -> tuple[tuple[float, float], ...]:
    """Per-area minor-arc bounds on the orbit-disk polar coordinate φ (degrees)."""
    e = WGS84_ELLIPSOID if ell is None else ell
    bounds: list[tuple[float, float]] = []
    for area in target_areas:
        if lon_deg is not None:
            lat_min_deg = float(area.lat_min.to(ureg.deg).magnitude)
            lat_max_deg = float(area.lat_max.to(ureg.deg).magnitude)
            lon = float(lon_deg)
            phi_a = geodetic_on_lon_meridian_to_disk_polar_deg(lat_deg=lat_min_deg, lon_deg=lon, ell=e)
            phi_b = geodetic_on_lon_meridian_to_disk_polar_deg(lat_deg=lat_max_deg, lon_deg=lon, ell=e)
        else:
            lat_a, lon_a = _area_endpoint_geodetic_deg(area, which="min")
            lat_b, lon_b = _area_endpoint_geodetic_deg(area, which="max")
            if getattr(area, "lat_min_lon", None) is not None:
                off_a = track_offset_deg_from_latitude_only_deg(lat_a)
                off_b = track_offset_deg_from_latitude_only_deg(lat_b)
                phi_a = disk_phi_deg_from_track_offset_deg(off_a)
                phi_b = disk_phi_deg_from_track_offset_deg(off_b)
            else:
                phi_a = disk_phi_deg_from_geodetic_deg(lat_a, lon_a, ell=e)
                phi_b = disk_phi_deg_from_geodetic_deg(lat_b, lon_b, ell=e)
        bounds.append((min(phi_a, phi_b), max(phi_a, phi_b)))
    return tuple(bounds)


def target_areas_envelope_disk_phi_bounds_deg(
    target_areas: tuple,
    *,
    lon_deg: float | None = None,
    ell: Ellipsoid | None = None,
) -> tuple[float, float]:
    """Union envelope of all target-area φ bounds (degrees)."""
    per_area = target_areas_disk_phi_bounds_deg(target_areas, lon_deg=lon_deg, ell=ell)
    if not per_area:
        raise ValueError("target_areas must contain at least one ObservationTargetArea.")
    return min(lo for lo, _ in per_area), max(hi for _, hi in per_area)


def target_areas_midpoint_disk_xy_km_on_sphere(
    target_areas: tuple,
    *,
    earth_radius_km: float,
    lon_deg: float | None = None,
    ell: Ellipsoid | None = None,
) -> np.ndarray:
    """Mid-latitude anchor between the first and last target bands on the rendering sphere."""
    e = WGS84_ELLIPSOID if ell is None else ell
    lon = float(LON_GLOBAL.to(ureg.deg).magnitude) if lon_deg is None else float(lon_deg)
    first = target_areas[0]
    last = target_areas[-1]
    lat_mid_deg = 0.5 * (
        float(first.lat_min.to(ureg.deg).magnitude) + float(last.lat_max.to(ureg.deg).magnitude)
    )
    x_m, _y_m, z_m = geodetic2ecef(lat_mid_deg, lon, 0.0, ell=e, deg=True)
    xy = np.array([float(x_m), float(z_m)], dtype=float) / KM_TO_M
    norm = float(np.linalg.norm(xy))
    rr = float(earth_radius_km)
    if norm <= 0.0 or rr <= 0.0:
        return np.array([0.0, rr], dtype=float)
    return xy * (rr / norm)


def primary_stripe_disk_phi_bounds_deg(*, ell: Ellipsoid | None = None) -> tuple[float, float]:
    """Minor stripe arc bounds on the orbit-disk polar coordinate ``φ`` (degrees)."""
    area = primary_observation_target_area()
    lat_a, lon_a = _area_endpoint_geodetic_deg(area, which="min")
    lat_b, lon_b = _area_endpoint_geodetic_deg(area, which="max")
    phi_a = disk_phi_deg_from_geodetic_deg(lat_a, lon_a, ell=ell)
    phi_b = disk_phi_deg_from_geodetic_deg(lat_b, lon_b, ell=ell)
    return min(phi_a, phi_b), max(phi_a, phi_b)


def primary_stripe_midpoint_geodetic_deg(*, ell: Ellipsoid | None = None) -> tuple[float, float]:
    """Geodetic midpoint of the primary stripe on the pole-meridian model."""
    area = primary_observation_target_area()
    lat_a, lon_a = _area_endpoint_geodetic_deg(area, which="min")
    lat_b, lon_b = _area_endpoint_geodetic_deg(area, which="max")
    off_mid = 0.5 * (
        track_offset_deg_from_latitude_only_deg(lat_a)
        + track_offset_deg_from_latitude_only_deg(lat_b)
    )
    return geodetic_deg_from_track_offset_deg(off_mid)


def primary_stripe_midpoint_disk_xy_km_on_sphere(*, earth_radius_km: float, ell: Ellipsoid | None = None) -> np.ndarray:
    """
    Primary target-stripe midpoint on the **mean rendering sphere** for render anchoring.

    LLA uses stripe midpoint latitude on ``LON_GLOBAL``, ECEF projection, then radial normalization
    to ``earth_radius_km`` so overlays stay consistent with circular Earth artwork.
    """
    e = WGS84_ELLIPSOID if ell is None else ell
    lat_mid_deg, lon_deg = primary_stripe_midpoint_geodetic_deg(ell=e)
    x_m, _y_m, z_m = geodetic2ecef(lat_mid_deg, lon_deg, 0.0, ell=e, deg=True)
    xy = np.array([float(x_m), float(z_m)], dtype=float) / KM_TO_M
    norm = float(np.linalg.norm(xy))
    rr = float(earth_radius_km)
    if norm <= 0.0 or rr <= 0.0:
        return np.array([0.0, rr], dtype=float)
    return xy * (rr / norm)
