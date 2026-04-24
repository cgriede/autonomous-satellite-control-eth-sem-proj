import unittest

from environment_definition.environment import SatelliteAttitude2D


class EnvObservationVectorTest(unittest.TestCase):
    def test_observation_contains_required_kinematic_terms(self):
        env = SatelliteAttitude2D()
        obs, _ = env.reset(seed=0)
        self.assertEqual(obs.shape, (5,))
        # [angle_rel_nadir, angular_velocity, angular_acceleration, angle_to_target, omega_wheel]
        self.assertAlmostEqual(float(obs[2]), 0.0, places=6)
        next_obs, *_ = env.step([0.0])
        self.assertEqual(next_obs.shape, (5,))


if __name__ == "__main__":
    unittest.main()
