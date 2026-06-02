"""Geometry helpers: orbit-disk projection vs WGS84 ECEF and mission-derived stripe angles."""

from .mission_stripe_disk import (
    geodetic_on_lon_meridian_to_disk_polar_deg,
    primary_stripe_disk_phi_bounds_deg,
    primary_stripe_midpoint_disk_xy_km_on_sphere,
)
from .orbit_disk_polar_meridian import (
    cloud_disk_phi_bounds_deg,
    cloud_mean_altitude_km,
    disk_phi_deg_from_geodetic_deg,
    disk_phi_deg_from_track_offset_deg,
    geodetic_deg_from_disk_phi_deg,
    geodetic_deg_from_track_offset_deg,
    geodetic_lonlat_deg,
    lon_deg_from_track_offset_deg,
    track_offset_deg_from_disk_phi_deg,
    track_offset_deg_from_geodetic_deg,
    track_offset_deg_from_latitude_only_deg,
)
from .polar_meridian_track import (
    MeridianTargetSegment,
    build_target_grid_polar_meridian,
    lat_deg_from_track_offset_deg,
    phi_deg_from_track_offset_deg,
)

__all__ = [
    "MeridianTargetSegment",
    "build_target_grid_polar_meridian",
    "cloud_disk_phi_bounds_deg",
    "cloud_mean_altitude_km",
    "disk_phi_deg_from_geodetic_deg",
    "disk_phi_deg_from_track_offset_deg",
    "geodetic_deg_from_track_offset_deg",
    "geodetic_deg_from_disk_phi_deg",
    "geodetic_on_lon_meridian_to_disk_polar_deg",
    "lat_deg_from_track_offset_deg",
    "lon_deg_from_track_offset_deg",
    "phi_deg_from_track_offset_deg",
    "primary_stripe_disk_phi_bounds_deg",
    "primary_stripe_midpoint_disk_xy_km_on_sphere",
    "geodetic_lonlat_deg",
    "track_offset_deg_from_latitude_only_deg",
    "track_offset_deg_from_disk_phi_deg",
    "track_offset_deg_from_geodetic_deg",
]
