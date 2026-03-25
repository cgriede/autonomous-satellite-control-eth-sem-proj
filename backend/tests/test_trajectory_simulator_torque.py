import unittest

from simulation.trajectory_simulator import KinematicSimulationConfig, simulate_kinematic_trajectory


class TorqueDrivenTrajectorySimulatorTest(unittest.TestCase):
    def _base_config(self) -> KinematicSimulationConfig:
        return KinematicSimulationConfig(
            earth_radius_km=6378.0,
            sat_altitude_km=500.0,
            mu_earth_km3_s2=398600.4418,
            theta_center_rad=1.2,
            start_angle_deg=-10.0,
            end_angle_deg=10.0,
            sat_motion_span_scale=1.0,
            num_frames=8,
            sat_z_offset_deg=0.0,
            body_torque_cmd_nm=0.1,
            body_inertia_kg_m2=20.0,
            body_initial_omega_rad_s=0.0,
        )

    def test_body_z_angle_shape_is_unchanged(self):
        series = simulate_kinematic_trajectory(self._base_config())
        self.assertEqual(series.body_z_angle_rad.shape, series.t_s.shape)
        self.assertEqual(series.body_z_angle_rad.shape[0], 8)

    def test_first_step_matches_zero_initial_rate_recurrence(self):
        config = self._base_config()
        series = simulate_kinematic_trajectory(config)
        dt_s = series.metadata.sim_dt_s
        alpha = config.body_torque_cmd_nm / config.body_inertia_kg_m2
        expected_delta_theta_1 = alpha * dt_s * dt_s
        observed_delta_theta_1 = series.body_z_angle_rad[1] - series.body_z_angle_rad[0]
        self.assertAlmostEqual(observed_delta_theta_1, expected_delta_theta_1, places=12)

    def test_positive_torque_produces_monotonic_body_angle_growth(self):
        series = simulate_kinematic_trajectory(self._base_config())
        deltas = series.body_z_angle_rad[1:] - series.body_z_angle_rad[:-1]
        self.assertTrue((deltas > 0.0).all())


if __name__ == "__main__":
    unittest.main()
