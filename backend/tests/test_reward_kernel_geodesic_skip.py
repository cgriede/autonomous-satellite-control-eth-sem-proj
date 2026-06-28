"""RewardKernel skips Vincenty geodesic when distance terms are disabled."""

from __future__ import annotations

import unittest
from unittest.mock import patch

import numpy as np

from autonomous_control.reward import RewardConfig
from environment_definition.constants import UREG as ureg
from environment_definition.constants.MISSION import OBSERVATION_TARGET_AREAS
from simulation.reward_kernel import RewardKernel


class RewardKernelGeodesicSkipTest(unittest.TestCase):
    def test_capture_only_config_skips_geodesic_distance(self) -> None:
        cfg = RewardConfig(
            enable_distance_reward=False,
            enable_image_quality_capture=True,
            enable_energy=False,
        )
        codes = np.full(101, 1, dtype=np.int8)

        with patch(
            "simulation.reward_kernel.geodesic_distance",
            side_effect=AssertionError("geodesic_distance should not run"),
        ):
            reward = RewardKernel.evaluate(
                sat_pos_xy_km=np.array([6800.0, 0.0], dtype=float),
                sat_subpoint_lat_deg=0.0,
                sat_subpoint_lon_deg=0.0,
                target_area_intersection_ratio=0.0,
                target_area_novelty_ratio=0.0,
                camera_observation_line_codes=codes,
                wheel_inertia=1.0 * ureg.kg * ureg.m**2,
                omega_before=0.0 * ureg.rad / ureg.s,
                omega_after=0.0 * ureg.rad / ureg.s,
                reward_config=cfg,
                ureg=ureg,
                target_areas=OBSERVATION_TARGET_AREAS,
            )

        self.assertTrue(np.isfinite(reward))

    def test_distance_reward_still_calls_geodesic(self) -> None:
        cfg = RewardConfig(enable_distance_reward=True, enable_image_quality_capture=False)
        codes = np.full(101, 1, dtype=np.int8)

        with patch(
            "simulation.reward_kernel.geodesic_distance",
            return_value=500.0 * ureg.km,
        ) as mock_geo:
            RewardKernel.evaluate(
                sat_pos_xy_km=np.array([6800.0, 0.0], dtype=float),
                sat_subpoint_lat_deg=0.0,
                sat_subpoint_lon_deg=0.0,
                target_area_intersection_ratio=0.0,
                target_area_novelty_ratio=0.0,
                camera_observation_line_codes=codes,
                wheel_inertia=1.0 * ureg.kg * ureg.m**2,
                omega_before=0.0 * ureg.rad / ureg.s,
                omega_after=0.0 * ureg.rad / ureg.s,
                reward_config=cfg,
                ureg=ureg,
                target_areas=OBSERVATION_TARGET_AREAS,
            )

        self.assertGreater(mock_geo.call_count, 0)


if __name__ == "__main__":
    unittest.main()
