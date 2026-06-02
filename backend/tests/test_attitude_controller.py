"""Unit tests for attitude safety controller kinematics and arbitration."""

from __future__ import annotations

import math
import unittest

import numpy as np

from environment_definition.constants.ATTITUDE_SAFETY import OFF_NADIR_HARD_LIMIT_DEG
from environment_definition.constants.SATELLITE import MOMENT_OF_INERTIA_2D, REACTION_WHEEL_MAX_TORQUE
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from simulation.attitude_controller import (
    AttitudeSafetyConfig,
    AttitudeSafetyController,
    SafeModePhase,
    braking_distance_rad,
    safe_mode_activation_angle_rad,
    torque_taper_scale,
)
from simulation.attitude_dynamics import AttitudeState2D


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
            dt_s=0.4,
        )
        self.assertAlmostEqual(result.tau_out_nm, 0.1)
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
            dt_s=0.4,
        )
        self.assertIn("SAFE_MODE_TAKEOVER", result.events)
        self.assertIsNotNone(ctrl._phase)
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
            dt_s=0.4,
        )
        self.assertIn("SAFE_MODE_TAKEOVER", result.events)
        self.assertLess(off_mid, hard)


if __name__ == "__main__":
    unittest.main()
