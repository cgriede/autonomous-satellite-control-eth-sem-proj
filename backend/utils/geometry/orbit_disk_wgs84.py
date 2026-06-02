"""Orbit-disk ↔ WGS84 ECEF mapping and ellipsoid ray intersections."""

from __future__ import annotations

import numpy as np
from pymap3d.ecef import ecef2geodetic
from pymap3d.ellipsoid import Ellipsoid

from environment_definition.constants.EARTH import WGS84_ELLIPSOID

KM_TO_M = 1000.0


def disk_xy_km_to_ecef_m(xy_km: np.ndarray) -> np.ndarray:
    """Map disk ``(x,y)_km`` to ECEF meters ``(x, 0, z)`` per locked orbit-plane convention."""
    p = np.asarray(xy_km, dtype=float).reshape(2)
    return np.array([p[0] * KM_TO_M, 0.0, p[1] * KM_TO_M], dtype=float)


def ecef_m_to_disk_xy_km(xyz_m: np.ndarray) -> np.ndarray:
    """Inverse of :func:`disk_xy_km_to_ecef_m` (drops ``y_ecef``)."""
    q = np.asarray(xyz_m, dtype=float).reshape(3)
    return np.array([q[0], q[2]], dtype=float) / KM_TO_M


def disk_direction_xy_to_ecef_unit(dx_dy_unit: np.ndarray) -> np.ndarray:
    """Unit direction ``(dx, 0, dz)_normalized`` from disk-plane ``(dx, dy_disk)``."""
    d = np.asarray(dx_dy_unit, dtype=float).reshape(2)
    v = np.array([float(d[0]), 0.0, float(d[1])], dtype=float)
    n = float(np.linalg.norm(v))
    if n <= 0.0:
        raise ValueError("disk direction must be non-zero.")
    return v / n


def batch_disk_direction_xy_to_ecef_unit(dirs_xy_unit: np.ndarray) -> np.ndarray:
    """Vectorized :func:`disk_direction_xy_to_ecef_unit` for rows ``(N, 2)``."""
    d = np.asarray(dirs_xy_unit, dtype=float)
    if d.ndim != 2 or d.shape[1] != 2:
        raise ValueError("dirs_xy_unit must have shape (N, 2).")
    v = np.stack([d[:, 0], np.zeros(d.shape[0], dtype=float), d[:, 1]], axis=1)
    norms = np.linalg.norm(v, axis=1, keepdims=True)
    norms = np.maximum(norms, 1e-15)
    return v / norms


def disk_xy_km_to_geodetic_deg(
    xy_km: np.ndarray,
    *,
    ell: Ellipsoid | None = None,
) -> tuple[float, float]:
    """Geodetic ``(lon_deg, lat_deg)`` for a disk ground/shadow point."""
    e = WGS84_ELLIPSOID if ell is None else ell
    xyz_m = disk_xy_km_to_ecef_m(xy_km)
    lat_deg, lon_deg, _h_m = ecef2geodetic(float(xyz_m[0]), float(xyz_m[1]), float(xyz_m[2]), ell=e, deg=True)
    return float(lon_deg), float(lat_deg)


def batch_disk_xy_rows_km_to_geodetic_deg(
    xy_km_n2: np.ndarray,
    *,
    ell: Ellipsoid | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Vectorized geodetic ``(lon_deg, lat_deg)`` for disk ground points as rows ``(n, 2)``.
    """
    p = np.asarray(xy_km_n2, dtype=float)
    if p.ndim != 2 or p.shape[1] != 2:
        raise ValueError("xy_km_n2 must have shape (n, 2).")
    x_m = p[:, 0] * KM_TO_M
    z_m = p[:, 1] * KM_TO_M
    y_m = np.zeros_like(x_m)
    e = WGS84_ELLIPSOID if ell is None else ell
    lat_deg, lon_deg, _h_m = ecef2geodetic(x_m, y_m, z_m, ell=e, deg=True)
    return np.asarray(lon_deg, dtype=float), np.asarray(lat_deg, dtype=float)


def satellite_disk_xy_rows_km_to_geodetic_deg(
    sat_xy_km_n2: np.ndarray,
    *,
    ell: Ellipsoid | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Vectorized subsatellite geodetic coordinates for satellite positions as disk rows ``(n, 2)``.

    Returns:
        ``(lon_deg, lat_deg)`` arrays (degrees), matching ``ecef2geodetic`` latitude-first storage split.
    """
    p = np.asarray(sat_xy_km_n2, dtype=float)
    if p.ndim != 2 or p.shape[1] != 2:
        raise ValueError("sat_xy_km_n2 must have shape (n, 2).")
    x_m = p[:, 0] * KM_TO_M
    z_m = p[:, 1] * KM_TO_M
    y_m = np.zeros_like(x_m)
    e = WGS84_ELLIPSOID if ell is None else ell
    lat_deg, lon_deg, _h_m = ecef2geodetic(x_m, y_m, z_m, ell=e, deg=True)
    return np.asarray(lon_deg, dtype=float), np.asarray(lat_deg, dtype=float)


def ray_oblate_spheroid_positive_hit_distance_m(
    origin_m: np.ndarray,
    dir_unit_m: np.ndarray,
    *,
    ell: Ellipsoid | None = None,
) -> float | None:
    """Smallest strictly positive ray parameter ``t`` hitting the oblate spheroid ``ell``, or ``None``."""
    e = WGS84_ELLIPSOID if ell is None else ell
    a = float(e.semimajor_axis)
    b = float(e.semiminor_axis)
    ox, oy, oz = [float(v) for v in np.asarray(origin_m, dtype=float).reshape(3)]
    dx, dy, dz = [float(v) for v in np.asarray(dir_unit_m, dtype=float).reshape(3)]
    ia2 = 1.0 / (a * a)
    ib2 = 1.0 / (b * b)
    aa = (dx * dx + dy * dy) * ia2 + dz * dz * ib2
    bb = 2.0 * ((ox * dx + oy * dy) * ia2 + oz * dz * ib2)
    cc = (ox * ox + oy * oy) * ia2 + oz * oz * ib2 - 1.0
    disc = bb * bb - 4.0 * aa * cc
    if disc < 0.0 or aa <= 0.0:
        return None
    sqrt_disc = float(np.sqrt(disc))
    t1 = (-bb - sqrt_disc) / (2.0 * aa)
    t2 = (-bb + sqrt_disc) / (2.0 * aa)
    candidates = [t for t in (t1, t2) if t > 1e-9]
    if not candidates:
        return None
    return float(min(candidates))


def batch_ray_oblate_spheroid_positive_hit_distance_m(
    origin_m: np.ndarray,
    dirs_unit_m: np.ndarray,
    *,
    ell: Ellipsoid | None = None,
) -> np.ndarray:
    """Same as :func:`ray_oblate_spheroid_positive_hit_distance_m` but ``dirs_unit_m`` is ``(N, 3)``."""
    e = WGS84_ELLIPSOID if ell is None else ell
    a = float(e.semimajor_axis)
    b = float(e.semiminor_axis)
    ox, oy, oz = [float(v) for v in np.asarray(origin_m, dtype=float).reshape(3)]
    dirs = np.asarray(dirs_unit_m, dtype=float)
    if dirs.ndim != 2 or dirs.shape[1] != 3:
        raise ValueError("dirs_unit_m must have shape (N, 3).")
    dx = dirs[:, 0]
    dy = dirs[:, 1]
    dz = dirs[:, 2]
    ia2 = 1.0 / (a * a)
    ib2 = 1.0 / (b * b)
    aa = (dx * dx + dy * dy) * ia2 + dz * dz * ib2
    bb = 2.0 * ((ox * dx + oy * dy) * ia2 + oz * dz * ib2)
    cc = (ox * ox + oy * oy) * ia2 + oz * oz * ib2 - 1.0
    disc = bb * bb - 4.0 * aa * cc
    out = np.full(aa.shape[0], np.nan, dtype=float)
    mask = (disc >= 0.0) & (aa > 0.0)
    if not np.any(mask):
        return out
    sqrt_disc = np.sqrt(np.maximum(disc[mask], 0.0))
    Am = aa[mask]
    Bm = bb[mask]
    t1 = (-Bm - sqrt_disc) / (2.0 * Am)
    t2 = (-Bm + sqrt_disc) / (2.0 * Am)
    t1p = np.where(t1 > 1e-9, t1, np.inf)
    t2p = np.where(t2 > 1e-9, t2, np.inf)
    best = np.minimum(t1p, t2p)
    best = np.where(np.isfinite(best), best, np.nan)
    out[mask] = best
    return out


def disk_ray_earth_hit_xy_km(
    *,
    sat_xy_km: np.ndarray,
    ray_dir_unit_xy: np.ndarray,
    ell: Ellipsoid | None = None,
) -> tuple[float | None, np.ndarray | None]:
    """
    Intersect an orbital-plane ray with the WGS84 ellipsoid; return ``(t_km, hit_xy_km)``.

    Ray parameter ``t_km`` scales the **meter** direction consistent with kilometer disk coords.
    """
    o_m = disk_xy_km_to_ecef_m(sat_xy_km)
    d_m = disk_direction_xy_to_ecef_unit(ray_dir_unit_xy)
    t_m = ray_oblate_spheroid_positive_hit_distance_m(o_m, d_m, ell=ell)
    if t_m is None:
        return None, None
    hit_m = o_m + float(t_m) * d_m
    return float(t_m) / KM_TO_M, ecef_m_to_disk_xy_km(hit_m)
