import unittest

import numpy as np

from autonomous_control.reward import RewardConfig
from environment_definition.constants.SIMULATION import RenderMode, SimulationConfig
from environment_definition.mission_profiles.s01_multiple_targets_fwd_fish import build_setup
from simulation.simulation_info import (
    _display_info_panel,
    _reward_program_rows,
    build_simulation_info_rows,
    build_training_live_stats_rows,
    build_warmup_phase_summary_rows,
)
from simulation.state_types import SimulationTimestepState
from simulation.stepper_factory import build_stepper


def _minimal_timestep_state() -> SimulationTimestepState:
    return SimulationTimestepState(
        step_idx=0,
        sim_time_s=1.0,
        sat_pos_xy_km=np.zeros(2, dtype=float),
        body_z_angle_rad=0.1,
        theta_orbit_rad=0.2,
        radius_km=7000.0,
        omega_sat_rad_s=0.01,
        omega_wheel_rad_s=0.0,
        reward=0.0,
        camera_observation_line_codes=np.zeros(8, dtype=np.int8),
        camera_center_ray_observation_code=np.int8(0),
    )


class RewardProgramRowsTest(unittest.TestCase):
    def test_capture_only_omits_inactive_outer_gate(self) -> None:
        rows = dict(
            _reward_program_rows(
                RewardConfig(
                    enable_distance_reward=False,
                    enable_image_quality_capture=True,
                    enable_outer_gate=True,
                )
            )
        )
        self.assertIn("reward (capture)", rows)
        self.assertNotIn("reward (distance band)", rows)
        self.assertNotIn("outer_gate", rows["reward (capture)"].lower())

    def test_distance_band_reports_outer_gate(self) -> None:
        rows = dict(
            _reward_program_rows(
                RewardConfig(enable_distance_reward=True, enable_outer_gate=True),
            )
        )
        self.assertIn("outer gate on", rows["reward (distance band)"])


class SimulationInfoRowsTest(unittest.TestCase):
    def test_dual_camera_setup_includes_key_fields(self) -> None:
        setup = build_setup(seed=0, include_cameras=True)
        resolved = setup.resolve(require_camera=False)
        sim_cfg = SimulationConfig(render_mode=RenderMode.HEADLESS)
        stepper = build_stepper(resolved, simulation_config=sim_cfg)
        rows = dict(
            build_simulation_info_rows(
                stepper,
                simulation_config=sim_cfg,
                tau_max_nm=0.1,
                episode_mode="eval",
            )
        )
        self.assertIn("simulation timestep", rows)
        self.assertIn("episode theta start (rel. center)", rows)
        self.assertNotIn("theta center offset", rows)
        self.assertNotIn("sat z offset", rows)
        self.assertNotIn("target phi stripe", rows)
        self.assertNotIn("torque command source", rows)
        self.assertNotIn("control stack (display)", rows)
        self.assertNotIn("controller seed", rows)
        self.assertNotIn("camera kernel backend", rows)
        self.assertEqual(rows["rollout"], "evaluation")
        self.assertIn("  observation line bins", rows)
        self.assertIn("  FOV (cross x along)", rows)
        self.assertIn("attitude safe-mode limit", rows)
        self.assertIn("attitude RW rate limit", rows)


class TrainingLiveStatsRowsTest(unittest.TestCase):
    def test_includes_safe_mode_activation_counter(self) -> None:
        rows = dict(
            build_training_live_stats_rows(
                _minimal_timestep_state(),
                step=10,
                total_steps=100,
                reward=0.0,
                episode_return=6.86,
                mode="eval",
                episode_idx=0,
                episode_total=1,
                safe_mode_activations=7,
            )
        )
        self.assertEqual(rows["safe mode activations"], "7")
        self.assertEqual(rows["reward"], "6.86")


class NotebookInfoPanelDisplayTest(unittest.TestCase):
    def test_display_info_panel_calls_ipython_display_once(self) -> None:
        calls: list[object] = []

        def _fake_display(obj, **_kwargs):
            calls.append(obj)

        import simulation.simulation_info as sim_info

        original = sim_info._in_notebook
        sim_info._in_notebook = lambda: True
        try:
            import IPython.display as ipd

            original_display = ipd.display
            ipd.display = _fake_display
            try:
                _display_info_panel([("episode duration", "773 s")], title="Simulation info", border_style="blue")
            finally:
                ipd.display = original_display
        finally:
            sim_info._in_notebook = original

        self.assertEqual(len(calls), 1)


class WarmupPhaseSummaryRowsTest(unittest.TestCase):
    def test_builds_aggregate_warmup_rows(self) -> None:
        from types import SimpleNamespace

        results = [
            SimpleNamespace(episode_return=1.0, steps=100),
            SimpleNamespace(episode_return=3.0, steps=120),
        ]
        rows = dict(build_warmup_phase_summary_rows(results, agent=SimpleNamespace(buffer=[1, 2], step_counter=5)))
        self.assertEqual(rows["phase"], "warmup complete")
        self.assertEqual(rows["episodes"], "2")
        self.assertEqual(rows["mean return"], "2.00")
        self.assertEqual(rows["buffer"], "2")


if __name__ == "__main__":
    unittest.main()
