"""Unit tests for attitude safety controller kinematics and arbitration."""

from __future__ import annotations

import math
import unittest

import numpy as np

from environment_definition.constants.ATTITUDE_SAFETY import OFF_NADIR_HARD_LIMIT_DEG
from environment_definition.constants.SATELLITE import (
    MOMENT_OF_INERTIA_2D,
    REACTION_WHEEL_MAX_MOMENTUM,
    REACTION_WHEEL_MAX_TORQUE,
)
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from simulation.attitude_controller import (
    AttitudeSafetyConfig,
    AttitudeSafetyController,
    braking_distance_rad,
    default_nadir_pointing_gains,
    nadir_pointing_torque_nm,
    nadir_target_angle_rad,
    safe_mode_activation_angle_rad,
    target_boresight_angle_rad,
    target_boresight_rate_rad_s,
    torque_taper_scale,
)
from simulation.attitude_dynamics import AttitudeState2D, propagate_reaction_wheel_attitude_2d


class AttitudeControllerKinematicsTest(unittest.TestCase):
    def test_braking_distance_at_3_deg_per_s(self):
        omega = 3.0 * ureg.deg / ureg.s
        brake_rad = braking_distance_rad(
            omega_sat=omega,
            tau_max=REACTION_WHEEL_MAX_TORQUE,
            sat_inertia=MOMENT_OF_INERTIA_2D,
        )
        brake_deg = (brake_rad * ureg.rad).to(ureg.deg).magnitude
        self.assertAlmostEqual(brake_deg, 24.6, delta=0.5)

    def test_safe_mode_activation_angle_at_3_deg_per_s(self):
        omega = 3.0 * ureg.deg / ureg.s
        arm_rad = safe_mode_activation_angle_rad(
            off_nadir_limit=OFF_NADIR_HARD_LIMIT_DEG,
            omega_sat=omega,
            tau_max=REACTION_WHEEL_MAX_TORQUE,
            sat_inertia=MOMENT_OF_INERTIA_2D,
        )
        arm_deg = (arm_rad * ureg.rad).to(ureg.deg).magnitude
        self.assertAlmostEqual(arm_deg, 20.4, delta=0.5)

    def test_torque_taper_scale_between_arm_and_hard(self):
        omega = 2.0 * ureg.deg / ureg.s
        hard = float(OFF_NADIR_HARD_LIMIT_DEG.to(ureg.rad).magnitude)
        arm = safe_mode_activation_angle_rad(
            off_nadir_limit=OFF_NADIR_HARD_LIMIT_DEG,
            omega_sat=omega,
            tau_max=REACTION_WHEEL_MAX_TORQUE,
            sat_inertia=MOMENT_OF_INERTIA_2D,
        )
        self.assertLess(arm, hard)
        off_mid = arm + 0.4 * (hard - arm)
        scale = torque_taper_scale(off_nadir_rad=off_mid, arm_rad=arm, hard_rad=hard)
        self.assertGreater(scale, 0.0)
        self.assertLess(scale, 1.0)

    def test_target_boresight_rate_matches_orbit_at_nadir(self):
        theta = 0.3
        omega = 0.0012
        r_km = 6878.0
        sat = np.array([r_km * math.cos(theta), r_km * math.sin(theta)])
        tgt = np.array([0.0, 0.0])
        bore = target_boresight_angle_rad(sat, tgt)
        nadir = nadir_target_angle_rad(theta)
        self.assertAlmostEqual(bore, nadir, places=6)
        rate = target_boresight_rate_rad_s(
            sat_pos_xy_km=sat,
            omega_orbit_rad_s=omega,
            ground_target_xy_km=tgt,
        )
        self.assertAlmostEqual(rate, omega, places=9)

    def test_passthrough_constant_agent_below_arm(self):
        ctrl = AttitudeSafetyController(
            config=AttitudeSafetyConfig(tau_max=REACTION_WHEEL_MAX_TORQUE),
            sat_inertia=MOMENT_OF_INERTIA_2D,
            tau_max_nm=0.1,
        )
        state = AttitudeState2D(
            theta=math.pi * ureg.rad,
            omega_sat=0.0 * ureg.rad / ureg.s,
            omega_wheel=0.0 * ureg.rad / ureg.s,
        )
        sat_xy = np.array([6878.0, 0.0])
        result = ctrl.arbitrate(
            tau_cmd_nm=0.1,
            state=state,
            sat_pos_xy_km=sat_xy,
            theta_orbit_rad=0.0,
            omega_orbit_rad_s=0.0,
            dt_s=0.4,
        )
        self.assertAlmostEqual(result.tau_out_nm, 0.1)
        self.assertTrue(result.agent_applied)
        self.assertFalse(result.events)

    def test_safe_mode_ignores_agent_and_starts_brake(self):
        ctrl = AttitudeSafetyController(
            config=AttitudeSafetyConfig(tau_max=REACTION_WHEEL_MAX_TORQUE),
            sat_inertia=MOMENT_OF_INERTIA_2D,
            tau_max_nm=0.1,
        )
        hard = float(OFF_NADIR_HARD_LIMIT_DEG.to(ureg.rad).magnitude)
        state = AttitudeState2D(
            theta=(math.pi + hard) * ureg.rad,
            omega_sat=0.0 * ureg.rad / ureg.s,
            omega_wheel=0.0 * ureg.rad / ureg.s,
        )
        sat_xy = np.array([6878.0, 0.0])
        result = ctrl.arbitrate(
            tau_cmd_nm=0.1,
            state=state,
            sat_pos_xy_km=sat_xy,
            theta_orbit_rad=0.0,
            omega_orbit_rad_s=0.0,
            dt_s=0.4,
        )
        self.assertIn("SAFE_MODE_TAKEOVER", result.events)
        self.assertIn("SAFE_MODE_INTERVAL_BRAKE", result.events)
        self.assertFalse(result.agent_applied)
        self.assertIsNotNone(ctrl._interval_idx)
        self.assertNotAlmostEqual(result.tau_out_nm, 0.1)

    def test_predictive_safe_mode_before_hard_at_high_rate(self):
        ctrl = AttitudeSafetyController(
            config=AttitudeSafetyConfig(tau_max=REACTION_WHEEL_MAX_TORQUE),
            sat_inertia=MOMENT_OF_INERTIA_2D,
            tau_max_nm=0.1,
        )
        arm = safe_mode_activation_angle_rad(
            off_nadir_limit=OFF_NADIR_HARD_LIMIT_DEG,
            omega_sat=3.0 * ureg.deg / ureg.s,
            tau_max=REACTION_WHEEL_MAX_TORQUE,
            sat_inertia=MOMENT_OF_INERTIA_2D,
        )
        hard = float(OFF_NADIR_HARD_LIMIT_DEG.to(ureg.rad).magnitude)
        off_mid = arm + 0.5 * (hard - arm)
        state = AttitudeState2D(
            theta=(math.pi + off_mid) * ureg.rad,
            omega_sat=3.0 * ureg.deg / ureg.s,
            omega_wheel=0.0 * ureg.rad / ureg.s,
        )
        sat_xy = np.array([6878.0, 0.0])
        result = ctrl.arbitrate(
            tau_cmd_nm=0.1,
            state=state,
            sat_pos_xy_km=sat_xy,
            theta_orbit_rad=0.0,
            omega_orbit_rad_s=0.0,
            dt_s=0.4,
        )
        self.assertIn("SAFE_MODE_TAKEOVER", result.events)
        self.assertLess(off_mid, hard)

    def test_nadir_mode_tracks_moving_nadir(self):
        """Orbit feedforward keeps off-nadir bounded when nadir target moves."""
        gains = default_nadir_pointing_gains(tau_max_nm=0.1, sat_inertia=MOMENT_OF_INERTIA_2D)
        omega_orbit = 0.05 * ureg.deg / ureg.s
        omega_orbit_rad_s = float(omega_orbit.to(ureg.rad / ureg.s).magnitude)
        dt = 0.4 * ureg.s
        wheel_inertia = (REACTION_WHEEL_MAX_MOMENTUM / (150.0 * ureg.rad / ureg.s)).to(ureg.kg * ureg.m**2)
        theta_orbit = 0.0
        body_z = nadir_target_angle_rad(theta_orbit)
        state = AttitudeState2D(
            theta=body_z * ureg.rad,
            omega_sat=omega_orbit,
            omega_wheel=0.0 * ureg.rad / ureg.s,
        )
        max_off = 0.0
        for _ in range(80):
            sat_xy = np.array([6878.0 * math.cos(theta_orbit), 6878.0 * math.sin(theta_orbit)])
            bore = np.array([math.cos(float(state.theta.to(ureg.rad).magnitude)), math.sin(float(state.theta.to(ureg.rad).magnitude))])
            nadir = -sat_xy / np.linalg.norm(sat_xy)
            off = math.degrees(math.acos(float(np.clip(np.dot(bore / np.linalg.norm(bore), nadir), -1.0, 1.0))))
            max_off = max(max_off, off)
            tau = nadir_pointing_torque_nm(
                body_z_rad=float(state.theta.to(ureg.rad).magnitude),
                omega_sat_rad_s=float(state.omega_sat.to(ureg.rad / ureg.s).magnitude),
                theta_orbit_rad=theta_orbit,
                omega_orbit_rad_s=omega_orbit_rad_s,
                omega_cmd_rad_s=0.0,
                tau_max_nm=0.1,
                gains=gains,
            )
            state = propagate_reaction_wheel_attitude_2d(
                state=state,
                wheel_torque=tau * ureg.N * ureg.m,
                sat_inertia=MOMENT_OF_INERTIA_2D,
                wheel_inertia=wheel_inertia,
                dt=dt,
            )
            theta_orbit += omega_orbit_rad_s * float(dt.to(ureg.s).magnitude)
        self.assertLess(max_off, 2.0)


if __name__ == "__main__":
    unittest.main()
