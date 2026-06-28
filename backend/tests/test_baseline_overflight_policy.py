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

from environment_definition.constants.ATTITUDE_SAFETY import SAFE_MODE_LOCKOUT_S
from environment_definition.constants.MISSION import ObservationTargetArea
from environment_definition.constants.SATELLITE import MOMENT_OF_INERTIA_2D
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from simulation.attitude_controller import AttitudePointingController, target_boresight_angle_rad
from simulation.state_types import SimulationTimestepState
from s01_utils.baseline_overflight import (
    BaselinePolicyObservation,
    SequentialTargetBaselinePolicy,
    build_baseline_overflight_setup,
    build_overflight_policy,
    run_baseline_overflight_rollout,
    warmup_capture_targets,
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
            sat_track_offset_deg=-10.0,
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

    def test_phi_window_at_engage_lo_stays_nadir_until_target_safe(self):
        setup = build_baseline_overflight_setup(n_targets=1, cloud_seed=0)
        resolved = setup.resolve(require_camera=True)
        policy = build_overflight_policy(
            setup,
            earth_radius_km=float(resolved.earth_radius.to(ureg.km).magnitude),
        )
        from environment_definition.constants.SATELLITE import REACTION_WHEEL_MAX_TORQUE
        from simulation.stepper_factory import build_stepper
        from environment_definition.constants.SIMULATION import training_episode_simulation_config

        stepper = build_stepper(
            resolved,
            simulation_config=training_episode_simulation_config(),
        )
        anchor = np.asarray(policy.target_anchors[0], dtype=float)
        engage_lo_rad = np.deg2rad(
            float(policy.target_leading_phi_lo_deg[0]) - float(policy.lead_margin_deg)
        )
        saw_phi_without_safe = False
        while not stepper.done:
            state = stepper.current_timestep_state()
            sat_xy = np.asarray(state.sat_pos_xy_km, dtype=float)
            if float(state.theta_orbit_rad) >= float(engage_lo_rad):
                in_phi = policy.in_phi_engage_window(float(state.theta_orbit_rad))
                can = policy.can_engage(
                    state,
                    sat_pos_xy_km=sat_xy,
                    sat_inertia=MOMENT_OF_INERTIA_2D,
                    tau_max_nm=float(
                        REACTION_WHEEL_MAX_TORQUE.to(ureg.N * ureg.m).magnitude
                    ),
                )
                if in_phi and not can:
                    saw_phi_without_safe = True
                policy.update_pointing_phase(
                    state,
                    sat_pos_xy_km=sat_xy,
                    sat_inertia=MOMENT_OF_INERTIA_2D,
                    tau_max_nm=float(
                        REACTION_WHEEL_MAX_TORQUE.to(ureg.N * ureg.m).magnitude
                    ),
                )
                if policy.pointing_phase == "engage":
                    break
            stepper.step(wheel_torque_cmd_nm=0.0)
        self.assertTrue(saw_phi_without_safe)
        self.assertEqual(policy.pointing_phase, "engage")

    def test_lockout_duration_is_one_minute(self):
        self.assertAlmostEqual(
            float(SAFE_MODE_LOCKOUT_S.to(ureg.s).magnitude),
            60.0,
            places=6,
        )


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


class WarmupCaptureTargetsTest(unittest.TestCase):
    def test_fifty_targets_ten_per_episode(self):
        self.assertEqual(
            warmup_capture_targets(0, n_targets=50, targets_per_episode=10),
            (0, 5, 10, 15, 20, 25, 30, 35, 40, 45),
        )
        self.assertEqual(
            warmup_capture_targets(1, n_targets=50, targets_per_episode=10),
            (1, 6, 11, 16, 21, 26, 31, 36, 41, 46),
        )
        self.assertEqual(
            warmup_capture_targets(4, n_targets=50, targets_per_episode=10),
            (4, 9, 14, 19, 24, 29, 34, 39, 44, 49),
        )
        self.assertEqual(
            warmup_capture_targets(5, n_targets=50, targets_per_episode=10),
            (0, 5, 10, 15, 20, 25, 30, 35, 40, 45),
        )

    def test_partial_last_chunk_and_wrap(self):
        self.assertEqual(
            warmup_capture_targets(4, n_targets=45, targets_per_episode=10),
            (4, 9, 14, 19, 24, 29, 34, 39, 44),
        )
        self.assertEqual(
            warmup_capture_targets(5, n_targets=45, targets_per_episode=10),
            (0, 5, 10, 15, 20, 25, 30, 35, 40),
        )

    def test_window_larger_than_target_count(self):
        self.assertEqual(
            warmup_capture_targets(0, n_targets=7, targets_per_episode=10),
            (0, 1, 2, 3, 4, 5, 6),
        )
        self.assertEqual(
            warmup_capture_targets(3, n_targets=7, targets_per_episode=10),
            (0, 1, 2, 3, 4, 5, 6),
        )

    def test_policy_starts_at_slice(self):
        areas = tuple(
            ObservationTargetArea(
                lat_min=(80 + i * 0.2) * ureg.deg,
                lat_max=(80.1 + i * 0.2) * ureg.deg,
                label=f"t{i}",
            )
            for i in range(5)
        )
        anchors = tuple((float(i), 0.0) for i in range(5))
        policy = SequentialTargetBaselinePolicy(
            target_anchors=anchors,
            target_areas=areas,
            target_leading_phi_lo_deg=tuple(0.0 for _ in areas),
            target_trailing_phi_hi_deg=tuple(90.0 for _ in areas),
            capture_targets=(2, 3),
        )
        self.assertEqual(policy.active_target_index, 2)
        self.assertEqual(policy.capture_targets, (2, 3))

    def test_flown_over_previous_allows_next_after_early_shutter(self):
        """Strided schedule: δ gate must not block after prev target already shuttered."""
        areas = (
            ObservationTargetArea(lat_min=88.0 * ureg.deg, lat_max=88.1 * ureg.deg, label="t0"),
            ObservationTargetArea(lat_min=85.0 * ureg.deg, lat_max=85.1 * ureg.deg, label="t1"),
        )
        policy = SequentialTargetBaselinePolicy(
            target_anchors=((0.0, 0.0), (1.0, 0.0)),
            target_areas=areas,
            target_leading_phi_lo_deg=(0.0, 0.0),
            target_trailing_phi_hi_deg=(90.0, 90.0),
            capture_targets=(0, 1),
        )
        policy._capture_i = 1
        policy._shuttered.add(0)
        policy.active_target_index = 1
        self.assertTrue(policy._flown_over_previous_capture(-5.0))

    def test_flown_over_target_uses_monotonic_track_offset(self):
        areas = tuple(
            ObservationTargetArea(
                lat_min=(89.9 - i * 0.15) * ureg.deg,
                lat_max=(90.0 - i * 0.15) * ureg.deg,
                label=f"t{i}",
            )
            for i in range(4)
        )
        policy = SequentialTargetBaselinePolicy(
            target_anchors=tuple((float(i), 0.0) for i in range(4)),
            target_areas=areas,
            target_leading_phi_lo_deg=tuple(0.0 for _ in areas),
            target_trailing_phi_hi_deg=tuple(90.0 for _ in areas),
        )
        _lo, hi = policy._target_track_range_deg(2)
        self.assertFalse(policy._flown_over_target(2, hi - 0.05))
        self.assertTrue(policy._flown_over_target(2, hi + 0.05))


if __name__ == "__main__":
    unittest.main()
