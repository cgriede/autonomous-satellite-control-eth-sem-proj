"""Unit tests for take-picture budget and capture reward."""

from __future__ import annotations

import unittest

from autonomous_control.reward import (
    RewardConfig,
    RewardSignals,
    applied_capture_reward,
    compute_reward,
    latent_capture_reward,
)
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


class CaptureRewardTest(unittest.TestCase):
    def test_latent_coverage_times_quality(self) -> None:
        r = latent_capture_reward(
            target_visible=True,
            primary_target_pixel_coverage=0.5,
            camera_image_quality=0.8,
            camera_cloud_blocked_fraction=0.0,
            k_capture=100.0,
        )
        self.assertAlmostEqual(r, 40.0)

    def test_applied_zero_without_shutter(self) -> None:
        self.assertEqual(
            applied_capture_reward(
                picture_taken=False,
                target_visible=True,
                primary_target_pixel_coverage=1.0,
                camera_image_quality=0.9,
                k_capture=100.0,
            ),
            0.0,
        )

    def test_applied_matches_latent_on_shutter(self) -> None:
        latent = latent_capture_reward(
            target_visible=True,
            primary_target_pixel_coverage=0.8,
            camera_image_quality=0.8,
            camera_cloud_blocked_fraction=0.25,
            k_capture=100.0,
        )
        applied = applied_capture_reward(
            picture_taken=True,
            target_visible=True,
            primary_target_pixel_coverage=0.8,
            camera_image_quality=0.8,
            camera_cloud_blocked_fraction=0.25,
            k_capture=100.0,
        )
        self.assertAlmostEqual(applied, latent)
        self.assertAlmostEqual(applied, 48.0)

    def test_applied_zero_on_repeat_target(self) -> None:
        latent = latent_capture_reward(
            target_visible=True,
            primary_target_pixel_coverage=1.0,
            camera_image_quality=0.9,
            k_capture=100.0,
        )
        applied = applied_capture_reward(
            picture_taken=True,
            capture_target_novel=False,
            target_visible=True,
            primary_target_pixel_coverage=1.0,
            camera_image_quality=0.9,
            k_capture=100.0,
        )
        self.assertGreater(latent, 0.0)
        self.assertEqual(applied, 0.0)

    def test_budget_repeat_target_consumes_slot(self) -> None:
        budget = TakePictureBudget.from_config(TakePictureConfig(max_pictures_per_episode=2))
        ok1, novel1 = budget.attempt_capture(0)
        ok2, novel2 = budget.attempt_capture(0)
        self.assertTrue(ok1 and novel1)
        self.assertTrue(ok2 and not novel2)
        self.assertEqual(budget.remaining, 0)

    def test_compute_reward_latent_vs_applied(self) -> None:
        cfg = RewardConfig(enable_distance_reward=False, enable_image_quality_capture=True)
        signals_latent_only = RewardSignals(
            distance_to_target=500.0 * ureg.km,
            picture_taken=False,
            target_visible=True,
            camera_image_quality=0.5,
            primary_target_pixel_coverage=0.4,
            camera_cloud_blocked_fraction=0.0,
        )
        _total_latent, components_latent = compute_reward(signals=signals_latent_only, cfg=cfg)
        expected_latent = REWARD_IMAGE_QUALITY_CAPTURE_WEIGHT * 0.4 * 0.5
        self.assertAlmostEqual(components_latent["latent_capture_reward"], expected_latent)
        self.assertEqual(components_latent["image_quality_capture_reward"], 0.0)

        signals_applied = RewardSignals(
            distance_to_target=500.0 * ureg.km,
            picture_taken=True,
            target_visible=True,
            camera_image_quality=0.5,
            primary_target_pixel_coverage=0.4,
            camera_cloud_blocked_fraction=0.0,
        )
        total, components = compute_reward(signals=signals_applied, cfg=cfg)
        self.assertAlmostEqual(components["latent_capture_reward"], expected_latent)
        self.assertAlmostEqual(components["image_quality_capture_reward"], expected_latent)
        self.assertAlmostEqual(total, expected_latent)


if __name__ == "__main__":
    unittest.main()
