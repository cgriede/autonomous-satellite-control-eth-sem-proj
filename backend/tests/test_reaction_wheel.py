import unittest

from pint import UnitRegistry

from simulation import AttitudeState2D, ReactionWheel


class ReactionWheelTest(unittest.TestCase):
    def test_passthrough_within_limit(self):
        ureg = UnitRegistry()
        rw = ReactionWheel(
            wheel_inertia=1.0 * ureg.kg * ureg.m**2,
            max_manouver_rate=1.0 * ureg.rad / ureg.s,
        )

        state = AttitudeState2D(
            theta=0.0 * ureg.rad,
            omega_sat=0.5 * ureg.rad / ureg.s,
            omega_wheel=0.0 * ureg.rad / ureg.s,
        )
        tau_cmd = 0.2 * ureg.N * ureg.m
        tau_applied = rw.compute_applied_torque(state=state, tau_cmd=tau_cmd)

        self.assertAlmostEqual(
            tau_applied.to(ureg.N * ureg.m).magnitude,
            tau_cmd.to(ureg.N * ureg.m).magnitude,
        )

    def test_cutoff_blocks_opposite_sign_positive_omega(self):
        ureg = UnitRegistry()
        rw = ReactionWheel(
            wheel_inertia=1.0 * ureg.kg * ureg.m**2,
            max_manouver_rate=1.0 * ureg.rad / ureg.s,
        )

        state = AttitudeState2D(
            theta=0.0 * ureg.rad,
            omega_sat=1.1 * ureg.rad / ureg.s,
            omega_wheel=0.0 * ureg.rad / ureg.s,
        )
        tau_cmd = -0.2 * ureg.N * ureg.m
        tau_applied = rw.compute_applied_torque(state=state, tau_cmd=tau_cmd)

        self.assertAlmostEqual(tau_applied.to(ureg.N * ureg.m).magnitude, 0.0)

    def test_cutoff_allows_same_sign_positive_omega(self):
        ureg = UnitRegistry()
        rw = ReactionWheel(
            wheel_inertia=1.0 * ureg.kg * ureg.m**2,
            max_manouver_rate=1.0 * ureg.rad / ureg.s,
        )

        state = AttitudeState2D(
            theta=0.0 * ureg.rad,
            omega_sat=1.1 * ureg.rad / ureg.s,
            omega_wheel=0.0 * ureg.rad / ureg.s,
        )
        tau_cmd = +0.2 * ureg.N * ureg.m
        tau_applied = rw.compute_applied_torque(state=state, tau_cmd=tau_cmd)

        self.assertAlmostEqual(
            tau_applied.to(ureg.N * ureg.m).magnitude,
            tau_cmd.to(ureg.N * ureg.m).magnitude,
        )

    def test_cutoff_blocks_opposite_sign_negative_omega(self):
        ureg = UnitRegistry()
        rw = ReactionWheel(
            wheel_inertia=1.0 * ureg.kg * ureg.m**2,
            max_manouver_rate=1.0 * ureg.rad / ureg.s,
        )

        state = AttitudeState2D(
            theta=0.0 * ureg.rad,
            omega_sat=-1.1 * ureg.rad / ureg.s,
            omega_wheel=0.0 * ureg.rad / ureg.s,
        )
        tau_cmd = +0.2 * ureg.N * ureg.m
        tau_applied = rw.compute_applied_torque(state=state, tau_cmd=tau_cmd)

        self.assertAlmostEqual(tau_applied.to(ureg.N * ureg.m).magnitude, 0.0)

    def test_cutoff_allows_same_sign_negative_omega(self):
        ureg = UnitRegistry()
        rw = ReactionWheel(
            wheel_inertia=1.0 * ureg.kg * ureg.m**2,
            max_manouver_rate=1.0 * ureg.rad / ureg.s,
        )

        state = AttitudeState2D(
            theta=0.0 * ureg.rad,
            omega_sat=-1.1 * ureg.rad / ureg.s,
            omega_wheel=0.0 * ureg.rad / ureg.s,
        )
        tau_cmd = -0.2 * ureg.N * ureg.m
        tau_applied = rw.compute_applied_torque(state=state, tau_cmd=tau_cmd)

        self.assertAlmostEqual(
            tau_applied.to(ureg.N * ureg.m).magnitude,
            tau_cmd.to(ureg.N * ureg.m).magnitude,
        )

    def test_cutoff_is_strictly_greater_than_limit(self):
        ureg = UnitRegistry()
        rw = ReactionWheel(
            wheel_inertia=1.0 * ureg.kg * ureg.m**2,
            max_manouver_rate=1.0 * ureg.rad / ureg.s,
        )

        state = AttitudeState2D(
            theta=0.0 * ureg.rad,
            omega_sat=1.0 * ureg.rad / ureg.s,
            omega_wheel=0.0 * ureg.rad / ureg.s,
        )
        tau_cmd = -0.2 * ureg.N * ureg.m
        tau_applied = rw.compute_applied_torque(state=state, tau_cmd=tau_cmd)

        # abs(omega_sat) == limit should not trigger the cutoff (uses `>`).
        self.assertAlmostEqual(
            tau_applied.to(ureg.N * ureg.m).magnitude,
            tau_cmd.to(ureg.N * ureg.m).magnitude,
        )


if __name__ == "__main__":
    unittest.main()

