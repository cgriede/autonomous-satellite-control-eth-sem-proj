import unittest

from environment_definition.constants.SIMULATION import RenderMode, SimulationConfig
from environment_definition.mission_profiles.s01_multiple_targets_fwd_fish import build_setup
from simulation.simulation_info import build_simulation_info_rows
from simulation.stepper_factory import build_stepper


class SimulationInfoRowsTest(unittest.TestCase):
    def test_dual_camera_setup_includes_key_fields(self):
        setup = build_setup(seed=0, include_cameras=True)
        resolved = setup.resolve(require_camera=False)
        sim_cfg = SimulationConfig(render_mode=RenderMode.HEADLESS, controller_mode="coast")
        stepper = build_stepper(resolved, simulation_config=sim_cfg)
        rows = dict(
            build_simulation_info_rows(
                stepper,
                simulation_config=sim_cfg,
                tau_max_nm=0.1,
            )
        )
        self.assertIn("simulation timestep", rows)
        self.assertIn("episode theta start (rel. center)", rows)
        self.assertIn("controller mode", rows)
        self.assertEqual(rows["controller mode"], "coast")
        self.assertIn("Camera 1 (primary) - observation line bins", rows)
        self.assertIn("Camera 2 (secondary) - FOV (cross x along)", rows)
        self.assertIn("attitude safety cutoff", rows)


if __name__ == "__main__":
    unittest.main()
