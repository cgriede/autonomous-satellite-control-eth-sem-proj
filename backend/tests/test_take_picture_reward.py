"""Unit tests for take-picture budget and capture reward."""

from __future__ import annotations

import unittest

from autonomous_control.reward import RewardConfig, RewardSignals, compute_reward, image_quality_capture_reward
from environment_definition.constants.AUTONOMOUS_CONTROL_REWARD import REWARD_IMAGE_QUALITY_CAPTURE_WEIGHT
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from simulation.take_picture import TakePictureBudget, TakePictureConfig, resolve_capture_frame_index


class TakePictureBudgetTest(unittest.TestCase):
    def test_budget_exhaustion(self) -> None:
        budget = TakePictureBudget.from_config(TakePictureConfig(max_pictures_per_episode=2))
        self.assertTrue(budget.try_capture())
        self.assertTrue(budget.try_capture())
        self.assertFalse(budget.try_capture())
        self.assertEqual(budget.remaining, 0)


class CaptureFrameIndexTest(unittest.TestCase):
    def test_resolve_capture_frame(self) -> None:
        self.assertEqual(resolve_capture_frame_index(cmd_step=5, n_steps=10), 5)
        self.assertEqual(resolve_capture_frame_index(cmd_step=5, n_steps=10, capture_latency_steps=1), 6)
        self.assertIsNone(resolve_capture_frame_index(cmd_step=9, n_steps=10, capture_latency_steps=1))


class ImageQualityCaptureRewardTest(unittest.TestCase):
    def test_no_picture_zero(self) -> None:
        self.assertEqual(
            image_quality_capture_reward(
                picture_taken=False,
                camera_image_quality=0.9,
                k_capture=100.0,
            ),
            0.0,
        )

    def test_quality_and_cloud_scaling(self) -> None:
        r = image_quality_capture_reward(
            picture_taken=True,
            camera_image_quality=0.8,
            camera_cloud_blocked_fraction=0.25,
            k_capture=100.0,
        )
        self.assertAlmostEqual(r, 60.0)

    def test_compute_reward_component(self) -> None:
        cfg = RewardConfig(enable_distance_reward=False, enable_image_quality_capture=True)
        signals = RewardSignals(
            distance_to_target=500.0 * ureg.km,
            picture_taken=True,
            target_visible=True,
            camera_image_quality=0.5,
            camera_cloud_blocked_fraction=0.0,
        )
        total, components = compute_reward(signals=signals, cfg=cfg)
        expected = REWARD_IMAGE_QUALITY_CAPTURE_WEIGHT * 0.5
        self.assertAlmostEqual(components["image_quality_capture_reward"], expected)
        self.assertAlmostEqual(total, expected)


if __name__ == "__main__":
    unittest.main()
