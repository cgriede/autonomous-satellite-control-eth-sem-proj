"""Render φ bands align with lat-only target matching for polar-grid areas."""

from environment_definition.constants import ureg
from environment_definition.constants.MISSION import LON_GLOBAL
from utils.geometry.mission_stripe_disk import target_areas_disk_phi_bounds_deg
from utils.geometry.polar_meridian_track import build_target_grid_polar_meridian


def test_polar_grid_render_phi_uses_lat_only_track_offset() -> None:
    segments = build_target_grid_polar_meridian(
        anchor_lat=80 * ureg.deg,
        anchor_lon=LON_GLOBAL,
        n_targets=50,
        target_size=15 * ureg.kilometer,
        spacing=40 * ureg.kilometer,
    )
    targets = [s.to_observation_target_area() for s in segments]
    bounds = target_areas_disk_phi_bounds_deg(tuple(targets))
    last_seg_phi = segments[-1].phi_bounds_deg()
    render_phi = bounds[-1]
    lat_lo = float(targets[-1].lat_min.to(ureg.deg).magnitude)
    # Past-pole segment: branch lon=180° used to draw φ≈104°; lat-only render matches ascending φ≈75°.
    assert render_phi[0] < 90.0
    assert abs(render_phi[0] - last_seg_phi[0]) > 10.0
    assert abs(render_phi[0] - (90.0 + (lat_lo - 90.0))) < 0.2
