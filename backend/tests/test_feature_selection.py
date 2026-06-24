import unittest

import numpy as np

from autonomous_control.feature_selection import (
    ControllerFeatureConfig,
    select_controller_inputs_from_timestep,
)
from autonomous_control.training_runtime import (
    build_state_vector_from_timestep,
    controller_observation_dim,
)
from environment_definition.constants import SIMULATION
from simulation.state_types import SimulationTimestepState


def _minimal_timestep(*, n_bins: int | None = None) -> SimulationTimestepState:
    bins = int(n_bins if n_bins is not None else SIMULATION.camera_observation_line_n_bins)
    return SimulationTimestepState(
        step_idx=0,
        sim_time_s=0.0,
        sat_pos_xy_km=np.array([7000.0, 0.0], dtype=float),
        body_z_angle_rad=0.1,
        theta_orbit_rad=0.2,
        radius_km=7000.0,
        omega_sat_rad_s=0.01,
        omega_wheel_rad_s=0.0,
        reward=0.0,
        camera_observation_line_codes=np.zeros(bins, dtype=np.int8),
        camera_center_ray_observation_code=np.int8(0),
        secondary_camera_observation_line_codes=np.empty(0, dtype=np.int8),
    )


class FeatureSelectionTest(unittest.TestCase):
    def test_select_controller_inputs_returns_all_configured_keys(self):
        ts = _minimal_timestep()
        cfg = ControllerFeatureConfig()
        selected = select_controller_inputs_from_timestep(timestep=ts, feature_config=cfg)
        for key in cfg.selected_keys:
            self.assertIn(key, selected)

    def test_build_state_vector_matches_controller_observation_dim(self):
        ts = _minimal_timestep()
        vec = build_state_vector_from_timestep(timestep=ts)
        self.assertEqual(vec.shape, (controller_observation_dim(),))
        self.assertEqual(vec.dtype, np.float32)

    def test_secondary_camera_bins_extend_state_vector(self):
        n_primary = int(SIMULATION.camera_observation_line_n_bins)
        n_secondary = 8
        ts = SimulationTimestepState(
            step_idx=0,
            sim_time_s=0.0,
            sat_pos_xy_km=np.array([7000.0, 0.0], dtype=float),
            body_z_angle_rad=0.0,
            theta_orbit_rad=0.0,
            radius_km=7000.0,
            omega_sat_rad_s=0.0,
            omega_wheel_rad_s=0.0,
            reward=0.0,
            camera_observation_line_codes=np.zeros(n_primary, dtype=np.int8),
            camera_center_ray_observation_code=np.int8(0),
            secondary_camera_observation_line_codes=np.zeros(n_secondary, dtype=np.int8),
        )
        dim = controller_observation_dim(
            secondary_camera_observation_line_n_bins=n_secondary
        )
        vec = build_state_vector_from_timestep(timestep=ts)
        self.assertEqual(vec.shape, (dim,))


if __name__ == "__main__":
    unittest.main()
