"""
Cloud formation along an orbit-disk path (minimal-feature / notebook cycle).

Authors specify ``formation_start`` / ``formation_end`` as geodetic (lat, lon).
Each :class:`~environment_definition.constants.SIMULATION.Cloud` stores geodetic
endpoints; simulation converts to disk φ via ``orbit_disk_polar_meridian``.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from pymap3d.ecef import ecef2geodetic, geodetic2ecef

from environment_definition.constants.EARTH import WGS84_ELLIPSOID
from environment_definition.constants.SIMULATION import Cloud, GeodeticLonLat
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from utils.geodesics.geodesic_helpers import geodesic_distance
from utils.geometry.orbit_disk_polar_meridian import geodetic_lonlat_deg
from utils.units.require_compatible_unit import require_compatible_units

DEFAULT_MAX_TOP_ALTITUDE_KM = 20


def geodetic_deg_on_disk_path_between(
    lat_s_deg: float,
    lon_s_deg: float,
    lat_e_deg: float,
    lon_e_deg: float,
    fraction: float,
    *,
    ell: Any | None = None,
) -> tuple[float, float]:
    """
    Geodetic point along the orbit-disk path between two surface endpoints.

    Interpolates ECEF position between endpoints (WGS84); simulation disk φ is
    ``atan2(z, x)`` of the result.
    """
    f = float(np.clip(float(fraction), 0.0, 1.0))
    e = WGS84_ELLIPSOID if ell is None else ell
    xs, ys, zs = geodetic2ecef(float(lat_s_deg), float(lon_s_deg), 0.0, ell=e, deg=True)
    xe, ye, ze = geodetic2ecef(float(lat_e_deg), float(lon_e_deg), 0.0, ell=e, deg=True)
    xm = (1.0 - f) * float(xs) + f * float(xe)
    ym = (1.0 - f) * float(ys) + f * float(ye)
    zm = (1.0 - f) * float(zs) + f * float(ze)
    lat_deg, lon_deg, _alt_m = ecef2geodetic(xm, ym, zm, ell=e, deg=True)
    return float(lat_deg), float(lon_deg)


def formation_disk_path_length_m(
    formation_start: Any,
    formation_end: Any,
    *,
    ell: Any | None = None,
) -> float:
    """Ellipsoidal path length [m] between two ``GeodeticLonLat`` formation endpoints."""
    lat_s, lon_s = geodetic_lonlat_deg(formation_start)
    lat_e, lon_e = geodetic_lonlat_deg(formation_end)
    e = WGS84_ELLIPSOID if ell is None else ell
    dist = geodesic_distance(
        lon_s * ureg.deg,
        lat_s * ureg.deg,
        lon_e * ureg.deg,
        lat_e * ureg.deg,
        ell=e,
    )
    return float(dist.to(ureg.m).magnitude)


def formation_path_length_km(
    formation_start: Any,
    formation_end: Any,
    *,
    ell: Any | None = None,
) -> int:
    """Formation path length as integer km stations (minimum block size 1 km)."""
    path_m = formation_disk_path_length_m(formation_start, formation_end, ell=ell)
    return int(path_m // 1000.0)


def vertical_extent_km(
    base_km: int,
    thickness_km: int,
    *,
    max_top_km: int = DEFAULT_MAX_TOP_ALTITUDE_KM,
) -> tuple[int, int]:
    """Return ``(base_km, top_km)`` with top capped at ``max_top_km``."""
    top_km = min(int(base_km) + int(thickness_km), int(max_top_km))
    return int(base_km), top_km


def sample_vertical_extent_km(
    rng: np.random.Generator,
    *,
    base_lo_km: int,
    base_hi_km: int,
    thickness_lo_km: int,
    thickness_hi_km: int,
    max_top_km: int = DEFAULT_MAX_TOP_ALTITUDE_KM,
) -> tuple[int, int]:
    """Sample integer base [km] and thickness [km]; derive capped top."""
    base_km = int(rng.integers(base_lo_km, base_hi_km + 1))
    thickness_km = int(rng.integers(thickness_lo_km, thickness_hi_km + 1))
    return vertical_extent_km(base_km, thickness_km, max_top_km=max_top_km)


def sample_extent_km(
    rng: np.random.Generator,
    *,
    range_lo_km: int,
    range_hi_km: int,
) -> int:
    """Sample along-path cloud extent as integer km in ``[range_lo_km, range_hi_km]``."""
    return int(rng.integers(int(range_lo_km), int(range_hi_km) + 1))


def sample_start_km(
    rng: np.random.Generator,
    path_km: int,
    extent_km: int,
) -> int | None:
    """Sample integer start offset [km] so ``start + extent <= path_km``."""
    if path_km <= 0 or extent_km <= 0 or extent_km > path_km:
        return None
    max_start = path_km - extent_km
    return int(rng.integers(0, max_start + 1))


def _bounds_to_int_km(lo_q: Any, hi_q: Any, *, name: str) -> tuple[int, int]:
    require_compatible_units(lo_q, ureg.km, f"{name}[0]")
    require_compatible_units(hi_q, ureg.km, f"{name}[1]")
    lo_km = int(round(float(lo_q.to(ureg.km).magnitude)))
    hi_km = int(round(float(hi_q.to(ureg.km).magnitude)))
    if hi_km < lo_km:
        lo_km, hi_km = hi_km, lo_km
    return lo_km, hi_km


def _cloud_on_disk_path_segment(
    *,
    formation_start: Any,
    formation_end: Any,
    fraction_lo: float,
    fraction_hi: float,
    base_altitude_km: int,
    top_altitude_km: int,
    ell: Any | None = None,
) -> Cloud:
    lat_s, lon_s = geodetic_lonlat_deg(formation_start)
    lat_e, lon_e = geodetic_lonlat_deg(formation_end)
    lat_lo, lon_lo = geodetic_deg_on_disk_path_between(
        lat_s, lon_s, lat_e, lon_e, fraction_lo, ell=ell
    )
    lat_hi, lon_hi = geodetic_deg_on_disk_path_between(
        lat_s, lon_s, lat_e, lon_e, fraction_hi, ell=ell
    )
    return Cloud(
        base_altitude=int(base_altitude_km) * ureg.km,
        top_altitude=int(top_altitude_km) * ureg.km,
        start_location=GeodeticLonLat(lat=lat_lo * ureg.deg, lon=lon_lo * ureg.deg),
        end_location=GeodeticLonLat(lat=lat_hi * ureg.deg, lon=lon_hi * ureg.deg),
    )


def cloud_formation_generator(
    *,
    formation_start: Any,
    formation_end: Any,
    cloud_number_bounds: tuple[int, int],
    cloud_range_bounds: tuple[Any, Any],
    cloud_base_altitude_bounds: tuple[Any, Any],
    cloud_thickness_bounds: tuple[Any, Any],
    max_top_altitude: Any | None = None,
    rng: np.random.Generator | None = None,
    ell: Any | None = None,
) -> list[Cloud]:
    """Random clouds along the formation path (integer-km blocks; for SimConfig / rainforest sampling)."""
    require_compatible_units(cloud_range_bounds[0], ureg.km, "cloud_range_bounds[0]")
    require_compatible_units(cloud_range_bounds[1], ureg.km, "cloud_range_bounds[1]")
    require_compatible_units(cloud_base_altitude_bounds[0], ureg.km, "cloud_base_altitude_bounds[0]")
    require_compatible_units(cloud_base_altitude_bounds[1], ureg.km, "cloud_base_altitude_bounds[1]")
    require_compatible_units(cloud_thickness_bounds[0], ureg.km, "cloud_thickness_bounds[0]")
    require_compatible_units(cloud_thickness_bounds[1], ureg.km, "cloud_thickness_bounds[1]")

    max_top_q = max_top_altitude if max_top_altitude is not None else DEFAULT_MAX_TOP_ALTITUDE_KM * ureg.km
    require_compatible_units(max_top_q, ureg.km, "max_top_altitude")
    max_top_km = int(round(float(max_top_q.to(ureg.km).magnitude)))

    range_lo_km, range_hi_km = _bounds_to_int_km(
        cloud_range_bounds[0], cloud_range_bounds[1], name="cloud_range_bounds"
    )
    base_lo_km, base_hi_km = _bounds_to_int_km(
        cloud_base_altitude_bounds[0], cloud_base_altitude_bounds[1], name="cloud_base_altitude_bounds"
    )
    thickness_lo_km, thickness_hi_km = _bounds_to_int_km(
        cloud_thickness_bounds[0], cloud_thickness_bounds[1], name="cloud_thickness_bounds"
    )

    gen = rng if rng is not None else np.random.default_rng()
    path_km = formation_path_length_km(formation_start, formation_end, ell=ell)
    if path_km < range_lo_km:
        return []

    n_lo, n_hi = int(cloud_number_bounds[0]), int(cloud_number_bounds[1])
    if n_hi <= n_lo:
        return []
    n_clouds = int(gen.integers(n_lo, n_hi))

    clouds: list[Cloud] = []
    for _ in range(n_clouds):
        extent_km = sample_extent_km(gen, range_lo_km=range_lo_km, range_hi_km=range_hi_km)
        start_km = sample_start_km(gen, path_km, extent_km)
        if start_km is None:
            continue
        base_km, top_km = sample_vertical_extent_km(
            gen,
            base_lo_km=base_lo_km,
            base_hi_km=base_hi_km,
            thickness_lo_km=thickness_lo_km,
            thickness_hi_km=thickness_hi_km,
            max_top_km=max_top_km,
        )
        f_lo = float(start_km) / float(path_km)
        f_hi = float(start_km + extent_km) / float(path_km)
        clouds.append(
            _cloud_on_disk_path_segment(
                formation_start=formation_start,
                formation_end=formation_end,
                fraction_lo=f_lo,
                fraction_hi=f_hi,
                base_altitude_km=base_km,
                top_altitude_km=top_km,
                ell=ell,
            )
        )
    return clouds
