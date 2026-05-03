"""Ellipsoidal geodesic helpers (WGS84 via ``environment_definition.constants.geod``)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from environment_definition.constants.EARTH import geod as default_geod
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from utils.units.require_compatible_unit import require_compatible_units

if TYPE_CHECKING:
    from pint import Quantity
    from pyproj import Geod


@dataclass(frozen=True)
class GeodeticBoundingBox:
    """Axis-aligned geodetic bbox (degrees/radians accepted via pint quantities)."""

    lon_min: Quantity
    lon_max: Quantity
    lat_min: Quantity
    lat_max: Quantity


def _normalize_lon_deg(lon_deg: float) -> float:
    normalized = ((float(lon_deg) + 180.0) % 360.0) - 180.0
    # Keep +180 representable for interval boundaries when needed.
    if normalized == -180.0 and lon_deg > 0.0:
        return 180.0
    return normalized


def _lon_segments_deg(lon_min_deg: float, lon_max_deg: float) -> list[tuple[float, float]]:
    """
    Return one or two non-wrapping lon segments in degrees.

    If ``lon_min <= lon_max``: one segment [min, max].
    If wrapping across date line: two segments [min, 180], [-180, max].
    """
    lo = _normalize_lon_deg(lon_min_deg)
    hi = _normalize_lon_deg(lon_max_deg)
    if lo <= hi:
        return [(lo, hi)]
    return [(lo, 180.0), (-180.0, hi)]


def _segment_overlap(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float] | None:
    lo = max(float(a[0]), float(b[0]))
    hi = min(float(a[1]), float(b[1]))
    if hi <= lo:
        return None
    return (lo, hi)


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


def geodesic_initial_bearing(
    lon1: Quantity,
    lat1: Quantity,
    lon2: Quantity,
    lat2: Quantity,
    *,
    geod: Geod | None = None,
) -> Quantity:
    """Forward azimuth (initial bearing) from point 1 to point 2."""
    require_compatible_units(lon1, "radian", "lon1")
    require_compatible_units(lat1, "radian", "lat1")
    require_compatible_units(lon2, "radian", "lon2")
    require_compatible_units(lat2, "radian", "lat2")
    g = default_geod if geod is None else geod
    a1 = float(lon1.to(ureg.deg).magnitude)
    b1 = float(lat1.to(ureg.deg).magnitude)
    a2 = float(lon2.to(ureg.deg).magnitude)
    b2 = float(lat2.to(ureg.deg).magnitude)
    az12, _az21, _dist_m = g.inv(a1, b1, a2, b2)
    return float(az12) * ureg.deg


def geodetic_bbox_contains(
    *,
    lon: Quantity,
    lat: Quantity,
    bbox: GeodeticBoundingBox,
) -> bool:
    """Return whether a geodetic point lies inside a possibly date-line-wrapping bbox."""
    require_compatible_units(lon, "radian", "lon")
    require_compatible_units(lat, "radian", "lat")
    require_compatible_units(bbox.lon_min, "radian", "bbox.lon_min")
    require_compatible_units(bbox.lon_max, "radian", "bbox.lon_max")
    require_compatible_units(bbox.lat_min, "radian", "bbox.lat_min")
    require_compatible_units(bbox.lat_max, "radian", "bbox.lat_max")

    lat_deg = float(lat.to(ureg.deg).magnitude)
    lat_min_deg = float(bbox.lat_min.to(ureg.deg).magnitude)
    lat_max_deg = float(bbox.lat_max.to(ureg.deg).magnitude)
    if not (lat_min_deg <= lat_deg <= lat_max_deg):
        return False

    lon_deg = _normalize_lon_deg(float(lon.to(ureg.deg).magnitude))
    for seg_lo, seg_hi in _lon_segments_deg(
        float(bbox.lon_min.to(ureg.deg).magnitude),
        float(bbox.lon_max.to(ureg.deg).magnitude),
    ):
        if seg_lo <= lon_deg <= seg_hi:
            return True
    return False


def geodetic_bbox_intersection_ratio(
    *,
    target_bbox: GeodeticBoundingBox,
    footprint_bbox: GeodeticBoundingBox,
    geod: Geod | None = None,
) -> float:
    """
    Approximate intersection ratio = (intersection area) / (target area), clipped to [0, 1].

    Area is estimated from geodesic north-south and east-west extents (at overlap mid-lat).
    """
    g = default_geod if geod is None else geod

    lat_a_min = float(target_bbox.lat_min.to(ureg.deg).magnitude)
    lat_a_max = float(target_bbox.lat_max.to(ureg.deg).magnitude)
    lat_b_min = float(footprint_bbox.lat_min.to(ureg.deg).magnitude)
    lat_b_max = float(footprint_bbox.lat_max.to(ureg.deg).magnitude)

    lat_int_min = max(lat_a_min, lat_b_min)
    lat_int_max = min(lat_a_max, lat_b_max)
    if lat_int_max <= lat_int_min:
        return 0.0

    target_segments = _lon_segments_deg(
        float(target_bbox.lon_min.to(ureg.deg).magnitude),
        float(target_bbox.lon_max.to(ureg.deg).magnitude),
    )
    footprint_segments = _lon_segments_deg(
        float(footprint_bbox.lon_min.to(ureg.deg).magnitude),
        float(footprint_bbox.lon_max.to(ureg.deg).magnitude),
    )
    overlap_segments: list[tuple[float, float]] = []
    for seg_t in target_segments:
        for seg_f in footprint_segments:
            overlap = _segment_overlap(seg_t, seg_f)
            if overlap is not None:
                overlap_segments.append(overlap)
    if len(overlap_segments) == 0:
        return 0.0

    overlap_mid_lat = 0.5 * (lat_int_min + lat_int_max)
    _az1, _az2, overlap_height_m = g.inv(0.0, lat_int_min, 0.0, lat_int_max)
    overlap_height_m = abs(float(overlap_height_m))
    if overlap_height_m <= 0.0:
        return 0.0

    def _width_m(segments: list[tuple[float, float]], lat_deg: float) -> float:
        total = 0.0
        for lo, hi in segments:
            if hi <= lo:
                continue
            _w_az1, _w_az2, seg_m = g.inv(float(lo), lat_deg, float(hi), lat_deg)
            total += abs(float(seg_m))
        return total

    target_mid_lat = 0.5 * (lat_a_min + lat_a_max)
    _t_az1, _t_az2, target_height_m = g.inv(0.0, lat_a_min, 0.0, lat_a_max)
    target_height_m = abs(float(target_height_m))
    target_width_m = _width_m(target_segments, target_mid_lat)
    if target_width_m <= 0.0:
        return 0.0
    if target_height_m <= 0.0:
        return 0.0
    overlap_width_m = _width_m(overlap_segments, overlap_mid_lat)
    if overlap_width_m <= 0.0:
        return 0.0

    target_area_m2 = target_width_m * target_height_m
    overlap_area_m2 = overlap_width_m * overlap_height_m
    return float(max(0.0, min(1.0, overlap_area_m2 / target_area_m2)))


def lonlat_to_z0_plane_angle_deg(lon: "Quantity", lat: "Quantity") -> float:
    """Azimuth on the z=0 plane from geodetic lon/lat (degrees, [-180, 180))."""
    require_compatible_units(lon, "radian", "lon")
    require_compatible_units(lat, "radian", "lat")
    lon_r = float(lon.to(ureg.rad).magnitude)
    lat_r = float(lat.to(ureg.rad).magnitude)
    x = float(np.cos(lat_r) * np.cos(lon_r))
    y = float(np.cos(lat_r) * np.sin(lon_r))
    return float(np.rad2deg(np.arctan2(y, x)))


def xy_km_to_plane_angle_deg(xy_km: np.ndarray) -> float:
    """Same convention as ``SimulationStepper._xy_to_equatorial_lat_lon_deg`` longitude-from-xy."""
    p = np.asarray(xy_km, dtype=float).reshape(2)
    if not np.all(np.isfinite(p)):
        return float("nan")
    return float(np.rad2deg(np.arctan2(float(p[1]), float(p[0]))))


def minor_arc_length_deg(phi0_deg: float, phi1_deg: float) -> float:
    """Shortest central angle in degrees between two directions on the circle."""
    d = (float(phi1_deg) - float(phi0_deg) + 180.0) % 360.0 - 180.0
    return float(abs(d))


def _point_on_minor_arc_deg(
    phi_deg: float,
    arc_start_deg: float,
    arc_end_deg: float,
    *,
    tol_deg: float = 0.25,
) -> bool:
    arc_len = minor_arc_length_deg(arc_start_deg, arc_end_deg)
    d0 = minor_arc_length_deg(arc_start_deg, phi_deg)
    d1 = minor_arc_length_deg(phi_deg, arc_end_deg)
    return abs(d0 + d1 - arc_len) <= tol_deg + 1e-9


def minor_arc_midpoint_deg(arc_start_deg: float, arc_end_deg: float) -> float:
    """Midpoint on the minor arc from ``arc_start_deg`` to ``arc_end_deg`` (degrees)."""
    a = float(arc_start_deg)
    delta = (float(arc_end_deg) - a + 180.0) % 360.0 - 180.0
    mid = a + 0.5 * delta
    return float((mid + 180.0) % 360.0 - 180.0)


def circle_stripe_footprint_overlap_ratio(
    *,
    footprint_left_xy_km: np.ndarray,
    footprint_right_xy_km: np.ndarray,
    stripe_angle_start_deg: float,
    stripe_angle_end_deg: float,
    n_samples: int = 24,
) -> float:
    """
    Approximate overlap of camera footprint (minor arc between left/right ground points)
    with the mission target stripe (minor arc), in [0, 1].
    """
    phi_l = xy_km_to_plane_angle_deg(footprint_left_xy_km)
    phi_r = xy_km_to_plane_angle_deg(footprint_right_xy_km)
    if not (np.isfinite(phi_l) and np.isfinite(phi_r)):
        return 0.0
    arc_len = minor_arc_length_deg(phi_l, phi_r)
    if arc_len <= 1e-9:
        return (
            1.0
            if _point_on_minor_arc_deg(phi_l, stripe_angle_start_deg, stripe_angle_end_deg)
            else 0.0
        )
    n = max(2, int(n_samples))
    delta = (phi_r - phi_l + 180.0) % 360.0 - 180.0
    inside = 0
    for i in range(n):
        t = i / (n - 1) if n > 1 else 0.0
        phi = phi_l + t * delta
        if _point_on_minor_arc_deg(phi, stripe_angle_start_deg, stripe_angle_end_deg):
            inside += 1
    return float(max(0.0, min(1.0, inside / n)))


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
