"""Episode θ window must follow target placement (disk φ + LOS), with optional overrides."""

from __future__ import annotations

import unittest

from environment_definition.constants import SIMULATION, ureg
from environment_definition.constants.MISSION import episode_theta_offsets_deg_for_target_areas
from environment_definition.mission_profiles.s01_multiple_targets_fwd_fish import (
    SATELLITE,
    sample_satellite_altitude,
)
from simulation.setup_types import EnvironmentSetup, OrbitConfig
from utils.geometry.polar_meridian_track import build_target_grid_polar_meridian


_ALTITUDE = sample_satellite_altitude(seed=42)
_MARGIN_DEG = float(SIMULATION.contact_margin_angle.to(ureg.deg).magnitude)


def _grid_targets(*, anchor_lat_deg: float):
    segments = build_target_grid_polar_meridian(
        anchor_lat=anchor_lat_deg * ureg.deg,
        anchor_lon=0 * ureg.deg,
        n_targets=10,
        target_size=20 * ureg.km,
        spacing=40 * ureg.km,
    )
    return tuple(s.to_observation_target_area() for s in segments)


class EpisodeThetaFromTargetPlacementTest(unittest.TestCase):
    def test_southern_anchor_widens_start_offset_vs_pole_anchor(self):
        targets_south = _grid_targets(anchor_lat_deg=60.0)
        targets_pole = _grid_targets(anchor_lat_deg=85.0)
        lo_south, _ = episode_theta_offsets_deg_for_target_areas(
            targets_south,
            orbit_height=_ALTITUDE,
            margin_deg=_MARGIN_DEG,
        )
        lo_pole, _ = episode_theta_offsets_deg_for_target_areas(
            targets_pole,
            orbit_height=_ALTITUDE,
            margin_deg=_MARGIN_DEG,
        )
        self.assertLess(lo_south, lo_pole)

    def test_southern_anchor_widens_episode_span_vs_pole_anchor(self):
        lo_south, hi_south = episode_theta_offsets_deg_for_target_areas(
            _grid_targets(anchor_lat_deg=60.0),
            orbit_height=_ALTITUDE,
            margin_deg=_MARGIN_DEG,
        )
        lo_pole, hi_pole = episode_theta_offsets_deg_for_target_areas(
            _grid_targets(anchor_lat_deg=85.0),
            orbit_height=_ALTITUDE,
            margin_deg=_MARGIN_DEG,
        )
        self.assertGreater(hi_south - lo_south, hi_pole - lo_pole)

    def test_orbit_config_overrides_replace_inference(self):
        targets = _grid_targets(anchor_lat_deg=85.0)
        setup = EnvironmentSetup(
            satellite=SATELLITE,
            orbit=OrbitConfig(
                altitude=_ALTITUDE,
                start_angle_deg=-40.0,
                end_angle_deg=5.0,
            ),
            target_areas=targets,
        )
        resolved = setup.resolve()
        self.assertAlmostEqual(resolved.start_angle_deg, -40.0, places=9)
        self.assertAlmostEqual(resolved.end_angle_deg, 5.0, places=9)

    def test_partial_override_uses_inference_for_unset_endpoint(self):
        targets = _grid_targets(anchor_lat_deg=85.0)
        inferred_lo, _ = episode_theta_offsets_deg_for_target_areas(
            targets,
            orbit_height=_ALTITUDE,
            margin_deg=_MARGIN_DEG,
        )
        setup = EnvironmentSetup(
            satellite=SATELLITE,
            orbit=OrbitConfig(altitude=_ALTITUDE, end_angle_deg=12.0),
            target_areas=targets,
        )
        resolved = setup.resolve()
        self.assertAlmostEqual(resolved.start_angle_deg, inferred_lo, places=6)
        self.assertAlmostEqual(resolved.end_angle_deg, 12.0, places=9)


if __name__ == "__main__":
    unittest.main()
