import unittest

from autonomous_control.controller_baselines import MaxTorqueSweepPolicy, RandomTorquePolicy
from environment_definition.attitude_control_env import SatelliteAttitudeControlEnv


class ControllerBaselinesTest(unittest.TestCase):
    def test_sweep_policy_runs_from_positive_to_negative(self):
        env = SatelliteAttitudeControlEnv()
        policy = MaxTorqueSweepPolicy(env, period_s=10.0)
        obs, _ = env.reset()
        values = [float(policy.get_action(obs, train=False)[0]) for _ in range(3)]
        self.assertGreater(values[0], values[1])
        self.assertGreater(values[1], values[2])
        self.assertGreater(values[0], 0.0)

    def test_random_policy_stays_in_action_bounds(self):
        env = SatelliteAttitudeControlEnv()
        policy = RandomTorquePolicy(env)
        obs, _ = env.reset()
        low = float(env.action_space.low[0])
        high = float(env.action_space.high[0])
        for _ in range(50):
            action = float(policy.get_action(obs, train=False)[0])
            self.assertGreaterEqual(action, low)
            self.assertLessEqual(action, high)


if __name__ == "__main__":
    unittest.main()
