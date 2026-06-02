import unittest

import numpy as np

from simulation.state_types import SimulationMetadata, SimulationStateSeries


def _build_valid_series(n: int = 3) -> SimulationStateSeries:
    n_bins = 4
    cloud_cols = 1
    return SimulationStateSeries(
        t_s=np.linspace(0.0, 2.0, n),
        theta_orbit_rad=np.zeros(n, dtype=float),
        radius_km=np.full(n, 6871.0, dtype=float),
        body_z_angle_rad=np.zeros(n, dtype=float),
        simulation_reward=np.zeros(n, dtype=float),
        wheel_torque_cmd_nm=np.zeros(n, dtype=float),
        camera_gsd_m=np.zeros(n, dtype=float),
        camera_vertical_fov_rad=0.1,
        camera_ground_left_xy_km=np.zeros((n, 2), dtype=float),
        camera_ground_right_xy_km=np.zeros((n, 2), dtype=float),
        camera_ground_center_xy_km=np.zeros((n, 2), dtype=float),
        camera_center_first_hit_xy_km=np.zeros((n, 2), dtype=float),
        camera_center_first_hit_is_cloud=np.zeros(n, dtype=bool),
        camera_center_ray_observation_code=np.zeros(n, dtype=np.int8),
        camera_cloud_blocked_fraction=np.zeros(n, dtype=float),
        camera_observation_line_codes=np.zeros((n, n_bins), dtype=np.int8),
        sat_subpoint_lat_deg=np.zeros(n, dtype=float),
        sat_subpoint_lon_deg=np.zeros(n, dtype=float),
        sat_altitude_m=np.full(n, 500000.0, dtype=float),
        camera_ground_left_lon_lat_deg=np.zeros((n, 2), dtype=float),
        camera_ground_right_lon_lat_deg=np.zeros((n, 2), dtype=float),
        camera_ground_center_lon_lat_deg=np.zeros((n, 2), dtype=float),
        target_area_intersection_ratio=np.zeros(n, dtype=float),
        target_area_novelty_ratio=np.zeros(n, dtype=float),
        cloud_arc_radius_km=np.zeros((n, cloud_cols), dtype=float),
        cloud_arc_start_rad=np.zeros((n, cloud_cols), dtype=float),
        cloud_arc_end_rad=np.zeros((n, cloud_cols), dtype=float),
        metadata=SimulationMetadata(
            orbit_period_s=1.0,
            omega_rad_s=1.0,
            sim_total_s=2.0,
            sim_dt_s=1.0,
            theta_start_rad=0.0,
            theta_end_rad=1.0,
            sat_theta_start_rad=0.0,
            sat_theta_span_rad=1.0,
            start_angle_deg=0.0,
            end_angle_deg=0.0,
        ),
    )


class SimulationStateSeriesGeodeticFieldsTest(unittest.TestCase):
    def test_valid_geodetic_fields_accept(self):
        series = _build_valid_series()
        self.assertEqual(series.sat_subpoint_lat_deg.shape[0], series.t_s.shape[0])

    def test_invalid_geodetic_lat_lon_shape_rejected(self):
        n = 3
        with self.assertRaises(ValueError):
            _ = SimulationStateSeries(
                **{
                    **_build_valid_series(n=n).__dict__,
                    "camera_ground_center_lon_lat_deg": np.zeros((n, 3), dtype=float),
                }
            )


if __name__ == "__main__":
    unittest.main()
