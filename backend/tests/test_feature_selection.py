import unittest

import numpy as np

from autonomous_control.feature_selection import (
    AutonomousControllerState,
    build_controller_state_from_env,
    build_controller_state_from_series,
)
from environment_definition.constants.SIMULATION import OBSERVATION_TARGET
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from environment_definition.attitude_control_env import SatelliteAttitudeControlEnv
from simulation.state_types import SimulationMetadata, SimulationStateSeries


def _make_trivial_series(n_bins: int = 4, n_frames: int = 2) -> SimulationStateSeries:
    t = np.linspace(0.0, 1.0, n_frames)
    theta_orbit = np.zeros(n_frames)
    radius = np.full(n_frames, 7000.0)
    body_z = np.zeros(n_frames)
    simulation_reward = np.zeros(n_frames)

    gsd = np.zeros(n_frames)
    left = np.zeros((n_frames, 2))
    right = np.zeros((n_frames, 2))
    center = np.zeros((n_frames, 2))
    first_hit = np.full((n_frames, 2), np.nan)
    first_hit_is_cloud = np.zeros(n_frames, dtype=bool)
    center_code = np.zeros(n_frames, dtype=np.int8)
    blocked = np.zeros(n_frames)

    obs_line = np.zeros((n_frames, n_bins), dtype=np.int8)
    # Mark one bin as target in frame 1 to exercise target_visible path.
    obs_line[1, 2] = np.int8(OBSERVATION_TARGET)
    fixed_ground = np.zeros((n_frames, n_bins), dtype=np.int8)

    cloud_r = np.full((n_frames, 1), np.nan)
    cloud_s = np.full((n_frames, 1), np.nan)
    cloud_e = np.full((n_frames, 1), np.nan)

    # Populate a valid ground-center point for frame 1 to exercise distance calc.
    center[1] = np.array([7000.0 - 6378.0, 0.0])

    meta = SimulationMetadata(
        orbit_period_s=1.0,
        omega_rad_s=1.0,
        sim_total_s=1.0,
        sim_dt_s=0.5,
        theta_start_rad=0.0,
        theta_end_rad=1.0,
        sat_theta_start_rad=0.0,
        sat_theta_span_rad=1.0,
        start_angle_deg=0.0,
        end_angle_deg=0.0,
    )
    return SimulationStateSeries(
        t_s=t,
        theta_orbit_rad=theta_orbit,
        radius_km=radius,
        body_z_angle_rad=body_z,
        simulation_reward=simulation_reward,
        camera_gsd_m=gsd,
        camera_vertical_fov_rad=0.02,
        camera_ground_left_xy_km=left,
        camera_ground_right_xy_km=right,
        camera_ground_center_xy_km=center,
        camera_center_first_hit_xy_km=first_hit,
        camera_center_first_hit_is_cloud=first_hit_is_cloud,
        camera_center_ray_observation_code=center_code,
        camera_cloud_blocked_fraction=blocked,
        camera_observation_line_codes=obs_line,
        fixed_ground_line_codes=fixed_ground,
        cloud_arc_radius_km=cloud_r,
        cloud_arc_start_rad=cloud_s,
        cloud_arc_end_rad=cloud_e,
        metadata=meta,
    )


class FeatureSelectionTest(unittest.TestCase):
    def test_build_from_env_returns_expected_shape_and_metadata(self):
        env = SatelliteAttitudeControlEnv()
        env.reset(seed=0)
        cs = build_controller_state_from_env(env)
        self.assertIsInstance(cs, AutonomousControllerState)
        self.assertEqual(cs.obs_vector.shape, (5,))
        self.assertIsNotNone(cs.target_visible)
        self.assertIsNotNone(cs.distance_to_target)
        # Distance should be at least satellite altitude (nadir case).
        d_km = float(cs.distance_to_target.to(ureg.km).magnitude)
        alt_km = env._altitude_km
        self.assertGreaterEqual(d_km, alt_km - 1e-6)

    def test_build_from_series_populates_fields(self):
        series = _make_trivial_series()
        cs0 = build_controller_state_from_series(series, 0)
        self.assertEqual(cs0.obs_vector.shape, (3,))
        self.assertFalse(cs0.target_visible)

        cs1 = build_controller_state_from_series(series, 1)
        self.assertTrue(cs1.target_visible)
        # distance_to_target resolved since camera_ground_center is set.
        self.assertIsNotNone(cs1.distance_to_target)


if __name__ == "__main__":
    unittest.main()
