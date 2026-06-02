"""E2E: delayed max-torque violation with attitude safety on canonical stepper."""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

import numpy as np

from environment_definition.constants.SIMULATION import RenderMode, SimulationConfig
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg

_S01_DIR = Path(__file__).resolve().parents[1] / "notebooks" / "s01"
if str(_S01_DIR) not in sys.path:
    sys.path.insert(0, str(_S01_DIR))

from s01_utils.movement_constraints_patch import (  # noqa: E402
    build_fast_movement_setup,
    build_movement_stepper,
    build_movement_video_setup,
    export_movement_verification_video,
    make_delayed_max_policy,
    max_off_nadir_deg_series,
    print_movement_verification_summary,
    run_policy_rollout,
)


class MovementConstraintsSimIntegrationTest(unittest.TestCase):
    def _run_delayed_max(self, *, tau_scale: float = 1.0):
        setup = build_fast_movement_setup(seed=0, include_cameras=False)
        sim_cfg = SimulationConfig(
            render_mode=RenderMode.HEADLESS,
            controller_mode="coast",
            attitude_safety_enabled=True,
        )
        stepper, _ = build_movement_stepper(setup, simulation_config=sim_cfg, patch=True)
        policy = make_delayed_max_policy(stepper, delay_s=5.0, tau_scale=tau_scale)
        series, events = run_policy_rollout(stepper, policy, print_events=False)
        return series, events, stepper

    def test_delayed_max_violation_envelope_and_takeover(self):
        series, events, _ = self._run_delayed_max(tau_scale=1.0)
        summary = print_movement_verification_summary(series, events, delay_s=5.0)
        self.assertTrue(summary["envelope_ok"])
        self.assertTrue(summary["takeover_ok"])
        self.assertGreaterEqual(summary["n_warnings"], 0)

    def test_delayed_max_deterministic_takeover_step(self):
        _, events_a, _ = self._run_delayed_max(tau_scale=1.0)
        _, events_b, _ = self._run_delayed_max(tau_scale=1.0)
        take_a = [e for e in events_a if e["event"] == "SAFE_MODE_TAKEOVER"]
        take_b = [e for e in events_b if e["event"] == "SAFE_MODE_TAKEOVER"]
        self.assertEqual(len(take_a), len(take_b))
        if take_a:
            self.assertEqual(take_a[0]["step"], take_b[0]["step"])

    def test_delayed_half_violation_envelope(self):
        series, events, _ = self._run_delayed_max(tau_scale=0.5)
        off_deg = max_off_nadir_deg_series(series)
        self.assertLessEqual(float(np.max(off_deg)), 45.5)
        summary = print_movement_verification_summary(series, events, delay_s=5.0)
        self.assertTrue(summary["envelope_ok"])

    def test_delayed_max_exports_required_mp4(self) -> None:
        setup = build_movement_video_setup(seed=0)
        sim_cfg = SimulationConfig(
            render_mode=RenderMode.HEADLESS,
            controller_mode="coast",
            attitude_safety_enabled=True,
        )
        stepper, _ = build_movement_stepper(setup, simulation_config=sim_cfg, patch=True)
        policy = make_delayed_max_policy(stepper, delay_s=5.0, tau_scale=1.0)
        series, _ = run_policy_rollout(stepper, policy, print_events=False)
        out_dir = Path(__file__).resolve().parent / "_artifacts" / "movement_constraints_e2e"
        out_dir.mkdir(parents=True, exist_ok=True)
        video_path = export_movement_verification_video(
            series, out_path=out_dir / "movement_constraints_delayed_max.mp4"
        )
        self.assertTrue(video_path.exists())
        self.assertGreater(video_path.stat().st_size, 10_000)


if __name__ == "__main__":
    unittest.main()
