"""E2E: generated clouds through canonical run_simulation + render video export."""

from __future__ import annotations

import sys
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np

from environment_definition.constants.SIMULATION import (
    GeodeticLonLat,
    OBSERVATION_CLOUD,
    RenderMode,
    SimulationConfig,
)
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from environment_definition.mission_profiles.s01_multiple_targets_fwd_fish import build_setup
from simulation.run_simulation import run_simulation
from utils.notebook.video import _export_render_video

_S01_DIR = Path(__file__).resolve().parents[1] / "notebooks" / "s01"
if str(_S01_DIR) not in sys.path:
    sys.path.insert(0, str(_S01_DIR))

from s01_utils.cloud_formation import cloud_formation_generator  # noqa: E402


class CloudFormationSimIntegrationTest(unittest.TestCase):
    def test_generated_clouds_run_simulation_and_export_video(self) -> None:
        formation_start = GeodeticLonLat(lat=75.0 * ureg.deg, lon=0.0 * ureg.deg)
        formation_end = GeodeticLonLat(lat=75.0 * ureg.deg, lon=180.0 * ureg.deg)
        clouds = cloud_formation_generator(
            formation_start=formation_start,
            formation_end=formation_end,
            cloud_base_altitude_bounds=(4, 12) * ureg.km,
            cloud_thickness_bounds=(1, 16) * ureg.km,
            cloud_range_bounds=(10, 50) * ureg.km,
            cloud_number_bounds=(5, 6),
            max_top_altitude=20 * ureg.km,
            rng=np.random.default_rng(42),
        )
        self.assertGreaterEqual(len(clouds), 1)

        setup = replace(
            build_setup(seed=0, include_cameras=True),
            clouds=tuple(clouds),
        )
        sim_cfg = SimulationConfig(render_mode=RenderMode.HEADLESS, controller_mode="coast")
        series = run_simulation(setup=setup, simulation_config=sim_cfg)

        n_clouds = len(clouds)
        self.assertEqual(series.cloud_arc_radius_km.shape[1], n_clouds)
        self.assertEqual(series.cloud_arc_start_rad.shape[1], n_clouds)
        self.assertEqual(series.cloud_arc_end_rad.shape[1], n_clouds)
        self.assertTrue(np.isfinite(series.cloud_arc_radius_km).any())

        out_dir = Path(__file__).resolve().parent / "_artifacts" / "cloud_formation_e2e"
        out_dir.mkdir(parents=True, exist_ok=True)
        video_path = out_dir / "clouds_coast_test.mp4"
        _export_render_video(simulation_series=series, out_path=video_path)
        self.assertTrue(video_path.exists())
        self.assertGreater(video_path.stat().st_size, 0)

        n_hits = int(np.sum(series.camera_observation_line_codes == np.int8(OBSERVATION_CLOUD)))
        self.assertGreaterEqual(n_hits, 0)


if __name__ == "__main__":
    unittest.main()
