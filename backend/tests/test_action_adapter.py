"""Tests for normalized MPO action adapter (torque fraction + shutter threshold)."""

from __future__ import annotations

import unittest

import numpy as np

from autonomous_control.action_adapter import (
    DEFAULT_SHUTTER_THRESHOLD,
    POLICY_RAW_DIM,
    policy_output_to_gym_action,
    raw_policy_to_action,
    shutter_cmd_from_gym,
    shutter_gym_to_unit_interval,
    to_gym_action_array,
)
from environment_definition.constants.SATELLITE import REACTION_WHEEL_MAX_TORQUE


def _tau_max_nm() -> float:
    return float(REACTION_WHEEL_MAX_TORQUE.to("N*m").magnitude)


class ShutterMappingTest(unittest.TestCase):
    def test_gym_to_unit_interval_endpoints(self) -> None:
        self.assertAlmostEqual(shutter_gym_to_unit_interval(-1.0), 0.0)
        self.assertAlmostEqual(shutter_gym_to_unit_interval(0.0), 0.5)
        self.assertAlmostEqual(shutter_gym_to_unit_interval(1.0), 1.0)

    def test_shutter_threshold_default(self) -> None:
        self.assertFalse(shutter_cmd_from_gym(-1.0))
        self.assertFalse(shutter_cmd_from_gym(0.0))
        self.assertFalse(shutter_cmd_from_gym(-0.01))
        self.assertTrue(shutter_cmd_from_gym(0.01))
        self.assertTrue(shutter_cmd_from_gym(0.75))
        self.assertTrue(shutter_cmd_from_gym(1.0))

    def test_shutter_threshold_strictly_above_half(self) -> None:
        # mapped == 0.5 must not fire (raw gym == 0)
        self.assertAlmostEqual(
            shutter_gym_to_unit_interval(0.0),
            DEFAULT_SHUTTER_THRESHOLD,
        )
        self.assertFalse(shutter_cmd_from_gym(0.0))


class TorqueScalingTest(unittest.TestCase):
    def test_torque_scales_with_tau_max(self) -> None:
        tau_max = _tau_max_nm()
        parsed = raw_policy_to_action(np.array([-0.25, -1.0], dtype=np.float64))
        self.assertAlmostEqual(
            float(parsed.wheel_torque_cmd.to("N*m").magnitude),
            -0.25 * tau_max,
            places=9,
        )

    def test_torque_clipped_before_scale(self) -> None:
        tau_max = _tau_max_nm()
        parsed = raw_policy_to_action(np.array([2.0, -1.0], dtype=np.float64))
        self.assertAlmostEqual(
            float(parsed.wheel_torque_cmd.to("N*m").magnitude),
            tau_max,
            places=9,
        )


class BufferStorageTest(unittest.TestCase):
    def test_stored_action_is_normalized_not_newton_meters(self) -> None:
        tau_max = _tau_max_nm()
        raw = np.array([0.5, 0.6], dtype=np.float64)
        _, stored = policy_output_to_gym_action(raw)
        self.assertAlmostEqual(float(stored[0]), 0.5)
        self.assertAlmostEqual(float(stored[1]), 0.6)
        self.assertNotAlmostEqual(float(stored[0]), 0.5 * tau_max)

    def test_to_gym_action_array_clips_both_dims(self) -> None:
        out = to_gym_action_array(np.array([1.5, -2.0], dtype=np.float64))
        np.testing.assert_allclose(out, [1.0, -1.0])

    def test_continuous_shutter_preserved_in_buffer(self) -> None:
        _, stored = policy_output_to_gym_action(np.array([0.0, 0.6], dtype=np.float64))
        self.assertAlmostEqual(float(stored[1]), 0.6)
        parsed, _ = policy_output_to_gym_action(np.array([0.0, 0.6], dtype=np.float64))
        self.assertTrue(parsed.active_observation)


class PolicyOutputIntegrationTest(unittest.TestCase):
    def test_dim_mismatch_raises(self) -> None:
        with self.assertRaises(ValueError):
            raw_policy_to_action(np.array([0.0], dtype=np.float64))

    def test_action_space_contract(self) -> None:
        from autonomous_control.training_runtime import make_attitude_control_env

        env = make_attitude_control_env()
        self.assertEqual(tuple(env.action_space.shape), (POLICY_RAW_DIM,))
        np.testing.assert_allclose(env.action_space.low, [-1.0, -1.0])
        np.testing.assert_allclose(env.action_space.high, [1.0, 1.0])


if __name__ == "__main__":
    unittest.main()
