"""Tests for sequential baseline pointing policy and unified-stack rollout."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

BACKEND = Path(__file__).resolve().parents[1]
S01 = BACKEND / "notebooks" / "s01"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
if str(S01) not in sys.path:
    sys.path.insert(0, str(S01))

from environment_definition.constants.MISSION import ObservationTargetArea
from environment_definition.constants.SATELLITE import MOMENT_OF_INERTIA_2D
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from simulation.attitude_controller import AttitudePointingController, target_boresight_angle_rad
from simulation.state_types import SimulationTimestepState
from s01_utils.baseline_overflight import (
    BaselinePolicyObservation,
    SequentialTargetBaselinePolicy,
    build_baseline_overflight_setup,
    run_baseline_overflight_rollout,
)


def _dummy_state(
    *,
    body_z: float,
    visible: bool,
    sat_xy: np.ndarray | None = None,
    theta_orbit_rad: float = 0.0,
    omega_sat: float = 0.0,
) -> SimulationTimestepState:
    codes = np.array([3 if visible else 1], dtype=np.int8)
    return SimulationTimestepState(
        step_idx=0,
        sim_time_s=0.0,
        sat_pos_xy_km=sat_xy if sat_xy is not None else np.array([6878.0, 0.0]),
        body_z_angle_rad=body_z,
        theta_orbit_rad=theta_orbit_rad,
        radius_km=6878.0,
        omega_sat_rad_s=omega_sat,
        omega_wheel_rad_s=0.0,
        reward=0.0,
        camera_observation_line_codes=codes,
        camera_center_ray_observation_code=np.int8(3 if visible else 1),
    )


def _act_kwargs(
    policy: SequentialTargetBaselinePolicy,
    obs: BaselinePolicyObservation,
    *,
    step_idx: int = 0,
    state: SimulationTimestepState | None = None,
) -> dict:
    sat_xy = np.array([6878.0, 0.0])
    st = state or _dummy_state(body_z=obs.body_z_angle_rad, visible=obs.target_visible_in_strip)
    return {
        "step_idx": step_idx,
        "state": st,
        "sat_pos_xy_km": sat_xy,
        "omega_orbit_rad_s": 0.001,
        "sat_inertia": MOMENT_OF_INERTIA_2D,
        "tau_max_nm": 0.1,
    }


class SequentialTargetBaselinePolicyTest(unittest.TestCase):
    def _policy(self) -> SequentialTargetBaselinePolicy:
        areas = (
            ObservationTargetArea(lat_min=80 * ureg.deg, lat_max=80.1 * ureg.deg, label="t0"),
            ObservationTargetArea(lat_min=81 * ureg.deg, lat_max=81.1 * ureg.deg, label="t1"),
        )
        anchors = ((100.0, 500.0), (120.0, 480.0))
        leading = (70.0, 71.0)
        trailing = (70.1, 71.1)
        return SequentialTargetBaselinePolicy(
            target_anchors=anchors,
            target_areas=areas,
            target_leading_phi_lo_deg=leading,
            target_trailing_phi_hi_deg=trailing,
        )

    def test_advances_after_shutter_not_twice(self):
        policy = self._policy()
        policy.pointing_phase = "engage"
        sat_xy = np.array([6878.0, 0.0])
        bearing0 = target_boresight_angle_rad(sat_xy, np.asarray(policy.target_anchors[0]))
        lat_mid = float(policy.target_areas[0].lat_min.to(ureg.deg).magnitude)
        obs = BaselinePolicyObservation(
            active_target_index=0,
            pointing_phase="engage",
            target_boresight_angles_rad=np.array([bearing0, 0.5]),
            body_z_angle_rad=bearing0,
            target_visible_in_strip=True,
            sat_subpoint_lat_deg=lat_mid,
            camera_image_quality=0.9,
        )
        kwargs = _act_kwargs(policy, obs, step_idx=10)
        a1 = policy.act(obs, **kwargs)
        self.assertTrue(a1.take_picture)
        self.assertTrue(np.isfinite(a1.torque_request_nm))
        self.assertEqual(policy.active_target_index, 1)
        a2 = policy.act(obs, **kwargs)
        self.assertFalse(a2.take_picture)
        self.assertEqual(tuple(policy.cmd_steps), (10,))

    def test_observe_exposes_bearing_vector(self):
        policy = self._policy()
        state = _dummy_state(body_z=0.1, visible=True)
        obs = policy.observe(state, sat_pos_xy_km=np.asarray(state.sat_pos_xy_km))
        self.assertEqual(obs.target_boresight_angles_rad.shape, (2,))
        self.assertEqual(obs.pointing_phase, "nadir")

    def test_nadir_phase_emits_finite_torque_request(self):
        policy = self._policy()
        state = _dummy_state(body_z=0.2, visible=False, theta_orbit_rad=1.0)
        obs = policy.observe(state, sat_pos_xy_km=np.asarray(state.sat_pos_xy_km))
        action = policy.act(obs, **_act_kwargs(policy, obs, state=state))
        self.assertFalse(action.take_picture)
        self.assertTrue(np.isfinite(action.torque_request_nm))


class BaselineOverflightRolloutTest(unittest.TestCase):
    def test_rollout_uses_training_stack_with_torque_requests(self):
        setup = build_baseline_overflight_setup(n_targets=3, cloud_seed=0)
        rollout = run_baseline_overflight_rollout(setup, show_progress=False)
        meta = rollout.series.metadata
        self.assertIn("sequential_target_baseline", str(meta.torque_policy_label or ""))
        agent_cmds = np.asarray(rollout.series.wheel_torque_agent_cmd_nm, dtype=float)
        self.assertTrue(np.any(np.abs(agent_cmds) > 1e-9))
        self.assertLessEqual(len(rollout.cmd_steps), 3)
        self.assertGreater(len(rollout.cmd_steps), 0)


class AttitudePointingGroundTargetUpdateTest(unittest.TestCase):
    def test_set_ground_target_updates_anchor(self):
        ctrl = AttitudePointingController(
            mode="target",
            sat_inertia=MOMENT_OF_INERTIA_2D,
            tau_max_nm=0.1,
            ground_target_xy_km=(0.0, 6378.0),
        )
        sat_xy = np.array([6878.0, 0.0])
        bore_a = target_boresight_angle_rad(sat_xy, np.asarray(ctrl.ground_target_xy_km))
        ctrl.set_ground_target_xy_km((2000.0, 6000.0))
        bore_b = target_boresight_angle_rad(sat_xy, np.asarray(ctrl.ground_target_xy_km))
        self.assertEqual(ctrl.ground_target_xy_km, (2000.0, 6000.0))
        self.assertNotAlmostEqual(bore_a, bore_b, places=6)

    def test_set_ground_target_requires_target_mode(self):
        ctrl = AttitudePointingController(
            mode="nadir",
            sat_inertia=MOMENT_OF_INERTIA_2D,
            tau_max_nm=0.1,
        )
        with self.assertRaises(ValueError):
            ctrl.set_ground_target_xy_km((0.0, 6378.0))


if __name__ == "__main__":
    unittest.main()
