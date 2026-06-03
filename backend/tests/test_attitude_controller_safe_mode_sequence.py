"""Safe-mode interval sequence: brake -> cruise -> settle -> lockout."""

from __future__ import annotations

import math
import unittest

import numpy as np

from environment_definition.constants.ATTITUDE_SAFETY import NADIR_RECOVERY_TOLERANCE_DEG
from environment_definition.constants.SATELLITE import (
    MOMENT_OF_INERTIA_2D,
    REACTION_WHEEL_MAX_MOMENTUM,
    REACTION_WHEEL_MAX_TORQUE,
)
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from simulation.attitude_controller import (
    AttitudeSafetyConfig,
    AttitudeSafetyController,
)
from simulation.attitude_dynamics import AttitudeState2D, propagate_reaction_wheel_attitude_2d


class SafeModeSequenceTest(unittest.TestCase):
    def _ctrl(self) -> AttitudeSafetyController:
        return AttitudeSafetyController(
            config=AttitudeSafetyConfig(tau_max=REACTION_WHEEL_MAX_TORQUE),
            sat_inertia=MOMENT_OF_INERTIA_2D,
            tau_max_nm=0.1,
        )

    def test_safe_mode_rejects_agent_and_runs_brake_first(self):
        ctrl = self._ctrl()
        ctrl._interval_idx = 0
        state = AttitudeState2D(
            theta=0.5 * ureg.rad,
            omega_sat=0.5 * ureg.deg / ureg.s,
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
        self.assertIn("SAFE_MODE_INTERVAL_BRAKE", result.events)
        self.assertFalse(result.agent_applied)

    def test_normal_mode_passes_agent_torque_unchanged(self):
        ctrl = self._ctrl()
        state = AttitudeState2D(
            theta=(np.pi + 0.01) * ureg.rad,
            omega_sat=0.0 * ureg.rad / ureg.s,
            omega_wheel=0.0 * ureg.rad / ureg.s,
        )
        sat_xy = np.array([6878.0, 0.0])
        result = ctrl.arbitrate(
            tau_cmd_nm=0.08,
            state=state,
            sat_pos_xy_km=sat_xy,
            theta_orbit_rad=0.0,
            omega_orbit_rad_s=0.0,
            dt_s=0.4,
        )
        self.assertEqual(result.tau_out_nm, 0.08)
        self.assertTrue(result.agent_applied)
        self.assertNotIn("SAFE_MODE_TAKEOVER", result.events)

    def test_lockout_holds_nadir_and_exits(self):
        config = AttitudeSafetyConfig(
            tau_max=REACTION_WHEEL_MAX_TORQUE,
            lockout_s=2.0 * ureg.s,
        )
        ctrl = AttitudeSafetyController(
            config=config,
            sat_inertia=MOMENT_OF_INERTIA_2D,
            tau_max_nm=0.1,
        )
        omega_orbit = 0.05 * ureg.deg / ureg.s
        omega_orbit_rad_s = float(omega_orbit.to(ureg.rad / ureg.s).magnitude)
        dt = 0.4 * ureg.s
        wheel_inertia = (REACTION_WHEEL_MAX_MOMENTUM / (150.0 * ureg.rad / ureg.s)).to(ureg.kg * ureg.m**2)
        theta_orbit = 0.0
        ctrl._interval_idx = 3
        ctrl._safe_mode_entered = True
        state = AttitudeState2D(
            theta=math.pi * ureg.rad,
            omega_sat=omega_orbit,
            omega_wheel=0.0 * ureg.rad / ureg.s,
        )
        saw_lockout = False
        saw_exit = False
        for _ in range(20):
            sat_xy = np.array([6878.0 * math.cos(theta_orbit), 6878.0 * math.sin(theta_orbit)])
            result = ctrl.arbitrate(
                tau_cmd_nm=0.1,
                state=state,
                sat_pos_xy_km=sat_xy,
                theta_orbit_rad=theta_orbit,
                omega_orbit_rad_s=omega_orbit_rad_s,
                dt_s=float(dt.to(ureg.s).magnitude),
            )
            self.assertFalse(result.agent_applied)
            self.assertNotAlmostEqual(result.tau_out_nm, 0.1)
            if "LOCKOUT_ACTIVE" in result.events:
                saw_lockout = True
            if "SAFE_MODE_EXIT" in result.events:
                saw_exit = True
                break
            state = propagate_reaction_wheel_attitude_2d(
                state=state,
                wheel_torque=result.tau_out_nm * ureg.N * ureg.m,
                sat_inertia=MOMENT_OF_INERTIA_2D,
                wheel_inertia=wheel_inertia,
                dt=dt,
            )
            theta_orbit += omega_orbit_rad_s * float(dt.to(ureg.s).magnitude)
        self.assertTrue(saw_lockout)
        self.assertTrue(saw_exit)


if __name__ == "__main__":
    unittest.main()
