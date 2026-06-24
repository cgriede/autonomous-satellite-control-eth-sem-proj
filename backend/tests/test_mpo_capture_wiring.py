"""Tests for MPO capture wiring (2D action, budget, RewardKernel shutter context)."""

from __future__ import annotations

import unittest

import numpy as np

from autonomous_control.action_adapter import POLICY_RAW_DIM, policy_output_to_gym_action
from autonomous_control.reward import RewardConfig
from autonomous_control.training_runtime import make_attitude_control_env
from simulation.episode_capture import evaluate_shutter_from_arrays
from simulation.take_picture import TakePictureBudget, TakePictureConfig

from s01_utils import take_picture_verification as tpv


class MpoCaptureWiringTest(unittest.TestCase):
    def test_env_action_space_is_torque_plus_shutter(self) -> None:
        env = make_attitude_control_env()
        self.assertEqual(tuple(env.action_space.shape), (POLICY_RAW_DIM,))

    def test_policy_output_to_gym_action_shape(self) -> None:
        env = make_attitude_control_env()
        tau_max = float(env.action_space.high[0])
        _, gym_action = policy_output_to_gym_action(
            np.array([0.5 * tau_max, 0.75], dtype=np.float64),
        )
        self.assertEqual(gym_action.shape, (2,))

    def test_shutter_evaluation_matches_verification_helper(self) -> None:
        ctx = tpv.build_take_picture_verification_context(seed=tpv.TAKE_PICTURE_VERIFICATION_SEED)
        series = ctx.target_series
        cmd_step = ctx.capture_step
        budget_a = TakePictureBudget.from_config(TakePictureConfig())
        budget_b = TakePictureBudget.from_config(TakePictureConfig())
        reward_cfg = RewardConfig(
            enable_distance_reward=False,
            enable_image_quality_capture=True,
        )
        expected = tpv.evaluate_capture_at_step(
            series,
            cmd_step=cmd_step,
            budget=budget_a,
            reward_config=reward_cfg,
        )
        actual = evaluate_shutter_from_arrays(
            cmd_step=cmd_step,
            n_steps=int(series.t_s.shape[0]),
            observation_line_codes=series.camera_observation_line_codes,
            camera_image_quality=series.camera_image_quality,
            camera_cloud_blocked_fraction=series.camera_cloud_blocked_fraction,
            budget=budget_b,
        )
        self.assertEqual(actual.capture_step, expected.capture_step)
        self.assertEqual(actual.override.picture_taken, expected.picture_taken)
        self.assertEqual(actual.override.capture_target_novel, expected.capture_target_novel)
        self.assertAlmostEqual(
            actual.override.primary_target_pixel_coverage,
            expected.target_coverage,
        )
        self.assertAlmostEqual(
            actual.override.camera_image_quality,
            expected.quality if np.isfinite(expected.quality) else 0.0,
            places=6,
        )
        self.assertEqual(actual.budget_remaining, expected.budget_remaining)


if __name__ == "__main__":
    unittest.main()
