import unittest

from environment_definition.attitude_control_env import SatelliteAttitudeControlEnv
from environment_definition.constants.SIMULATION import SIMULATION


class EpisodeStepConstantsTest(unittest.TestCase):
    def test_gym_episode_step_limit_uses_simulation_constant(self):
        expected_steps = int(SIMULATION.max_episode_steps)

        gym_env = SatelliteAttitudeControlEnv()

        self.assertEqual(gym_env.max_episode_steps, expected_steps)
        self.assertEqual(expected_steps, 1000)


if __name__ == "__main__":
    unittest.main()
