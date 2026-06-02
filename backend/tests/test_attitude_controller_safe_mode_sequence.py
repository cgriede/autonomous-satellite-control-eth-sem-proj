"""Safe-mode phase sequence: brake -> spin-up -> coast -> decel -> lockout."""

from __future__ import annotations

import unittest

import numpy as np

from environment_definition.constants.SATELLITE import MOMENT_OF_INERTIA_2D, REACTION_WHEEL_MAX_TORQUE
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from simulation.attitude_controller import AttitudeSafetyConfig, AttitudeSafetyController, SafeModePhase
from simulation.attitude_dynamics import AttitudeState2D


class SafeModeSequenceTest(unittest.TestCase):
    def _ctrl(self) -> AttitudeSafetyController:
        return AttitudeSafetyController(
            config=AttitudeSafetyConfig(tau_max=REACTION_WHEEL_MAX_TORQUE),
            sat_inertia=MOMENT_OF_INERTIA_2D,
            tau_max_nm=0.1,
        )

    def test_safe_mode_rejects_agent_and_runs_brake_first(self):
        ctrl = self._ctrl()
        ctrl._phase = SafeModePhase.BRAKE
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
            dt_s=0.4,
        )
        self.assertIn("SAFE_MODE_PHASE_BRAKE", result.events)
        self.assertLess(result.tau_out_nm * float(state.omega_sat.to(ureg.rad / ureg.s).magnitude), 0.0)

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
            dt_s=0.4,
        )
        self.assertEqual(result.tau_out_nm, 0.08)
        self.assertNotIn("SAFE_MODE_TAKEOVER", result.events)


if __name__ == "__main__":
    unittest.main()
