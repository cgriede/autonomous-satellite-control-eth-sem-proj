import unittest
from pint import UnitRegistry

from simulation import AttitudeState2D, propagate_reaction_wheel_attitude_2d, wrap_angle_to_pi

ureg = UnitRegistry()


class AttitudeDynamics2DTest(unittest.TestCase):
    def test_positive_wheel_torque_slows_satellite_and_spins_wheel_up(self):
        next_state = propagate_reaction_wheel_attitude_2d(
            state=AttitudeState2D(
                theta=0.0 * ureg.rad,
                omega_sat=0.0 * ureg.rad / ureg.s,
                omega_wheel=0.0 * ureg.rad / ureg.s,
            ),
            wheel_torque=0.1 * ureg.N * ureg.m,
            sat_inertia=10.0 * ureg.kg * ureg.m**2,
            wheel_inertia=1.0 * ureg.kg * ureg.m**2,
            dt=0.5 * ureg.s,
        )

        self.assertLess(next_state.omega_sat.to(ureg.rad / ureg.s).magnitude, 0.0)
        self.assertGreater(next_state.omega_wheel.to(ureg.rad / ureg.s).magnitude, 0.0)
        self.assertEqual(next_state.theta.units, ureg.rad)
        self.assertEqual(next_state.omega_sat.units, ureg.rad / ureg.s)
        self.assertEqual(next_state.omega_wheel.units, ureg.rad / ureg.s)

    def test_angle_wrap_stays_within_closed_interval(self):
        wrapped = wrap_angle_to_pi(3.5 * ureg.rad)
        wrapped_mag = wrapped.to(ureg.rad).magnitude
        self.assertGreaterEqual(wrapped_mag, -3.141592653589793)
        self.assertLessEqual(wrapped_mag, 3.141592653589793)

    def test_propagation_wraps_theta(self):
        state = AttitudeState2D(
            theta=3.13 * ureg.rad,
            omega_sat=1.0 * ureg.rad / ureg.s,
            omega_wheel=0.0 * ureg.rad / ureg.s,
        )
        next_state = propagate_reaction_wheel_attitude_2d(
            state=state,
            wheel_torque=0.0 * ureg.N * ureg.m,
            sat_inertia=10.0 * ureg.kg * ureg.m**2,
            wheel_inertia=1.0 * ureg.kg * ureg.m**2,
            dt=0.2 * ureg.s,
        )
        wrapped_theta_mag = next_state.theta.to(ureg.rad).magnitude
        self.assertGreaterEqual(wrapped_theta_mag, -3.141592653589793)
        self.assertLessEqual(wrapped_theta_mag, 3.141592653589793)

    def test_rejects_wrong_torque_units(self):
        with self.assertRaises(ValueError):
            propagate_reaction_wheel_attitude_2d(
                state=AttitudeState2D(
                    theta=0.0 * ureg.rad,
                    omega_sat=0.0 * ureg.rad / ureg.s,
                    omega_wheel=0.0 * ureg.rad / ureg.s,
                ),
                wheel_torque=1.0 * ureg.s,
                sat_inertia=10.0 * ureg.kg * ureg.m**2,
                wheel_inertia=1.0 * ureg.kg * ureg.m**2,
                dt=0.5 * ureg.s,
            )


if __name__ == "__main__":
    unittest.main()
