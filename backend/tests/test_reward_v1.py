import unittest

from environment_definition.constants.UNIT_REGISTRY import UREG as ureg

from autonomous_control.reward import (
    energy_from_wheel_momentum_change,
    reward_v1_slides,
    reward_v1_with_energy,
)


class RewardV1Test(unittest.TestCase):
    def test_outside_viewing_gate_zero(self):
        d_op = 400.0 * ureg.km
        d_th = 1500.0 * ureg.km
        v_t = 2500.0 * ureg.km
        r = reward_v1_slides(
            distance_to_target=3000.0 * ureg.km,
            d_op=d_op,
            d_th=d_th,
            viewing_threshold=v_t,
            picture_taken=False,
            target_visible=False,
        )
        self.assertEqual(r, 0.0)

    def test_inside_gate_no_picture(self):
        d_op = 400.0 * ureg.km
        d_th = 1500.0 * ureg.km
        v_t = 2500.0 * ureg.km
        r = reward_v1_slides(
            distance_to_target=1000.0 * ureg.km,
            d_op=d_op,
            d_th=d_th,
            viewing_threshold=v_t,
            picture_taken=False,
            target_visible=True,
        )
        self.assertEqual(r, -100.0)

    def test_r1_band_matches_formula(self):
        d_op = 400.0 * ureg.km
        d_th = 1500.0 * ureg.km
        v_t = 2500.0 * ureg.km
        d_km = 900.0
        r = reward_v1_slides(
            distance_to_target=d_km * ureg.km,
            d_op=d_op,
            d_th=d_th,
            viewing_threshold=v_t,
            picture_taken=True,
            target_visible=True,
        )
        expected = -100.0 * d_km / (1500.0 - 400.0)
        self.assertAlmostEqual(r, expected, places=6)

    def test_energy_subtracts_k_e_times_joules(self):
        d_op = 400.0 * ureg.km
        d_th = 1500.0 * ureg.km
        v_t = 2500.0 * ureg.km
        d_km = 900.0
        i_w = 2.0 * ureg.kg * ureg.m**2
        w0 = 0.0 * ureg.rad / ureg.s
        w1 = 1.0 * ureg.rad / ureg.s
        e = energy_from_wheel_momentum_change(
            wheel_inertia=i_w, omega_before=w0, omega_after=w1
        )
        r_slide = reward_v1_slides(
            distance_to_target=d_km * ureg.km,
            d_op=d_op,
            d_th=d_th,
            viewing_threshold=v_t,
            picture_taken=True,
            target_visible=True,
        )
        k_e = 1.0
        r_tot = reward_v1_with_energy(
            distance_to_target=d_km * ureg.km,
            d_op=d_op,
            d_th=d_th,
            viewing_threshold=v_t,
            picture_taken=True,
            target_visible=True,
            energy_joules=e,
            k_e=k_e,
        )
        e_j = float(e.to(ureg.joule).magnitude)
        self.assertAlmostEqual(r_tot, r_slide - k_e * e_j, places=9)

    def test_outside_gate_no_energy_term(self):
        d_op = 400.0 * ureg.km
        d_th = 1500.0 * ureg.km
        v_t = 2500.0 * ureg.km
        i_w = 2.0 * ureg.kg * ureg.m**2
        e = energy_from_wheel_momentum_change(
            wheel_inertia=i_w,
            omega_before=0.0 * ureg.rad / ureg.s,
            omega_after=10.0 * ureg.rad / ureg.s,
        )
        r_tot = reward_v1_with_energy(
            distance_to_target=3000.0 * ureg.km,
            d_op=d_op,
            d_th=d_th,
            viewing_threshold=v_t,
            picture_taken=True,
            target_visible=True,
            energy_joules=e,
            k_e=1.0e9,
        )
        self.assertEqual(r_tot, 0.0)


if __name__ == "__main__":
    unittest.main()
