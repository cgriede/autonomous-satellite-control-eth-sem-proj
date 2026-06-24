"""Render φ bands align with orbit-disk geodetic endpoints (reward/sensor parity)."""

from environment_definition.constants import ureg
from environment_definition.constants.MISSION import LON_GLOBAL
from utils.geometry.mission_stripe_disk import target_areas_disk_phi_bounds_deg
from utils.geometry.orbit_disk_polar_meridian import disk_phi_deg_from_geodetic_deg
from utils.geometry.polar_meridian_track import build_target_grid_polar_meridian


def test_polar_grid_render_phi_matches_geodetic_endpoints() -> None:
    segments = build_target_grid_polar_meridian(
        anchor_lat=80 * ureg.deg,
        anchor_lon=LON_GLOBAL,
        n_targets=50,
        target_size=15 * ureg.kilometer,
        spacing=40 * ureg.kilometer,
    )
    targets = [s.to_observation_target_area() for s in segments]
    bounds = target_areas_disk_phi_bounds_deg(tuple(targets))
    for seg, area, render_phi in zip(segments, targets, bounds):
        seg_phi = seg.phi_bounds_deg()
        lat_lo = float(area.lat_min.to(ureg.deg).magnitude)
        lon_lo = float(area.lat_min_lon.to(ureg.deg).magnitude)
        lat_hi = float(area.lat_max.to(ureg.deg).magnitude)
        lon_hi = float(area.lat_max_lon.to(ureg.deg).magnitude)
        geo_phi = (
            disk_phi_deg_from_geodetic_deg(lat_lo, lon_lo),
            disk_phi_deg_from_geodetic_deg(lat_hi, lon_hi),
        )
        assert abs(render_phi[0] - min(geo_phi)) < 0.05
        assert abs(render_phi[1] - max(geo_phi)) < 0.05
        assert abs(render_phi[0] - seg_phi[0]) < 0.15
        assert abs(render_phi[1] - seg_phi[1]) < 0.15
