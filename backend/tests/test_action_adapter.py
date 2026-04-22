import unittest

import numpy as np

from environment_definition.constants.SATELLITE import REACTION_WHEEL_MAX_TORQUE
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg

from autonomous_control.action_adapter import (
    POLICY_RAW_DIM,
    raw_policy_to_action,
    to_gym_torque_array,
)


class ActionAdapterTest(unittest.TestCase):
    def test_torque_clipped_to_max(self):
        tau_max = float(REACTION_WHEEL_MAX_TORQUE.to(ureg.N * ureg.m).magnitude)
        raw = np.array([tau_max * 10.0, -1.0], dtype=np.float64)
        action = raw_policy_to_action(raw)
        got = float(action.wheel_torque_cmd.to(ureg.N * ureg.m).magnitude)
        self.assertAlmostEqual(got, tau_max, places=6)
        self.assertFalse(action.active_observation)

    def test_active_observation_threshold(self):
        raw = np.array([0.0, 0.5], dtype=np.float64)
        action = raw_policy_to_action(raw, active_threshold=0.0)
        self.assertTrue(action.active_observation)

    def test_gym_array_shape(self):
        action = raw_policy_to_action(np.zeros(POLICY_RAW_DIM, dtype=np.float64))
        arr = to_gym_torque_array(action)
        self.assertEqual(arr.shape, (1,))
        self.assertEqual(arr.dtype, np.float32)

    def test_raw_dim_enforced(self):
        with self.assertRaises(ValueError):
            raw_policy_to_action(np.zeros(3, dtype=np.float64))


if __name__ == "__main__":
    unittest.main()
