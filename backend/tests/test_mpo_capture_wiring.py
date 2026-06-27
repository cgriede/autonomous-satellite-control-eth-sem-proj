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
    def test_env_action_space_is_normalized_torque_plus_shutter(self) -> None:
        env = make_attitude_control_env()
        self.assertEqual(tuple(env.action_space.shape), (POLICY_RAW_DIM,))
        np.testing.assert_allclose(env.action_space.low, [-1.0, -1.0])
        np.testing.assert_allclose(env.action_space.high, [1.0, 1.0])

    def test_policy_output_to_gym_action_shape_and_torque_scale(self) -> None:
        from environment_definition.constants.SATELLITE import REACTION_WHEEL_MAX_TORQUE

        tau_max = float(REACTION_WHEEL_MAX_TORQUE.to("N*m").magnitude)
        parsed, gym_action = policy_output_to_gym_action(
            np.array([-0.1, 0.75], dtype=np.float64),
        )
        self.assertEqual(gym_action.shape, (2,))
        self.assertAlmostEqual(float(gym_action[0]), -0.1)
        self.assertAlmostEqual(float(gym_action[1]), 0.75)
        self.assertAlmostEqual(
            float(parsed.wheel_torque_cmd.to("N*m").magnitude),
            -0.1 * tau_max,
            places=6,
        )
        self.assertTrue(parsed.active_observation)

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
