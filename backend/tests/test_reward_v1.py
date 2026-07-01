import unittest

from environment_definition.constants.UNIT_REGISTRY import UREG as ureg

from autonomous_control.reward import (
    RewardConfig,
    RewardSignals,
    canonical_reward,
    energy_from_wheel_momentum_change,
    reward_v1_distance_band_reward,
    reward_v1_with_energy,
)


class RewardV1Test(unittest.TestCase):
    def test_optimal_distance_visible_returns_zero(self):
        d_op = 400.0 * ureg.km
        d_th = 1500.0 * ureg.km
        v_t = 2500.0 * ureg.km
        r = reward_v1_distance_band_reward(
            distance_to_target=d_op,
            d_op=d_op,
            d_th=d_th,
            viewing_threshold=v_t,
            picture_taken=True,
            target_visible=True,
        )
        self.assertEqual(r, 0.0)

    def test_outside_viewing_gate_zero(self):
        d_op = 400.0 * ureg.km
        d_th = 1500.0 * ureg.km
        v_t = 2500.0 * ureg.km
        r = reward_v1_distance_band_reward(
            distance_to_target=3000.0 * ureg.km,
            d_op=d_op,
            d_th=d_th,
            viewing_threshold=v_t,
            picture_taken=False,
            target_visible=False,
        )
        self.assertEqual(r, -100.0)

    def test_inside_gate_no_picture(self):
        d_op = 400.0 * ureg.km
        d_th = 1500.0 * ureg.km
        v_t = 2500.0 * ureg.km
        r = reward_v1_distance_band_reward(
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
        r = reward_v1_distance_band_reward(
            distance_to_target=d_km * ureg.km,
            d_op=d_op,
            d_th=d_th,
            viewing_threshold=v_t,
            picture_taken=True,
            target_visible=True,
        )
        expected = -100.0 + 100.0 * ((1500.0 - d_km) / (1500.0 - 400.0))
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
        r_distance_band_reward = reward_v1_distance_band_reward(
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
        self.assertAlmostEqual(r_tot, r_distance_band_reward - k_e * e_j, places=9)

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


class CanonicalRewardFlagsTest(unittest.TestCase):
    """RewardConfig flag behavior for the canonical entrypoint."""

    def _signals_in_band(self) -> RewardSignals:
        return RewardSignals(
            distance_to_target=900.0 * ureg.km,
            picture_taken=True,
            target_visible=True,
            wheel_inertia=2.0 * ureg.kg * ureg.m**2,
            omega_before=0.0 * ureg.rad / ureg.s,
            omega_after=1.0 * ureg.rad / ureg.s,
        )

    def test_all_on_matches_legacy_helper(self):
        signals = self._signals_in_band()
        cfg = RewardConfig(enable_distance_reward=True)  # explicit: distance terms on
        total, components = canonical_reward(signals=signals, cfg=cfg)

        e = energy_from_wheel_momentum_change(
            wheel_inertia=signals.wheel_inertia,
            omega_before=signals.omega_before,
            omega_after=signals.omega_after,
        )
        expected = reward_v1_with_energy(
            distance_to_target=signals.distance_to_target,
            d_op=400.0 * ureg.km,
            d_th=1500.0 * ureg.km,
            viewing_threshold=2500.0 * ureg.km,
            picture_taken=signals.picture_taken,
            target_visible=signals.target_visible,
            energy_joules=e,
            k_e=cfg.k_energy,
        )
        self.assertAlmostEqual(total, expected, places=6)
        self.assertAlmostEqual(
            components["distance_band_reward"] + components["energy"],
            expected,
            places=6,
        )
        self.assertEqual(components["no_picture_penalty"], 0.0)

    def test_disable_distance_band_reward_zeros_component(self):
        signals = self._signals_in_band()
        cfg = RewardConfig(enable_distance_band_reward=False, enable_energy=False)
        total, components = canonical_reward(signals=signals, cfg=cfg)
        self.assertEqual(components["distance_band_reward"], 0.0)
        self.assertEqual(components["no_picture_penalty"], 0.0)
        self.assertEqual(components["energy"], 0.0)
        self.assertEqual(total, 0.0)

    def test_disable_energy_drops_only_energy_term(self):
        signals = self._signals_in_band()
        cfg = RewardConfig(enable_energy=False, enable_distance_reward=True)
        total, components = canonical_reward(signals=signals, cfg=cfg)
        self.assertEqual(components["energy"], 0.0)
        self.assertNotEqual(components["distance_band_reward"], 0.0)
        self.assertAlmostEqual(total, components["distance_band_reward"], places=9)

    def test_disable_no_picture_penalty_zeros_penalty(self):
        signals = RewardSignals(
            distance_to_target=1000.0 * ureg.km,
            picture_taken=False,
            target_visible=True,
        )
        cfg_on = RewardConfig(enable_energy=False, enable_distance_reward=True)
        total_on, comp_on = canonical_reward(signals=signals, cfg=cfg_on)
        self.assertEqual(comp_on["no_picture_penalty"], -100.0)
        self.assertEqual(total_on, -100.0)

        cfg_off = RewardConfig(enable_energy=False, enable_no_picture_penalty=False)
        total_off, comp_off = canonical_reward(signals=signals, cfg=cfg_off)
        self.assertEqual(comp_off["no_picture_penalty"], 0.0)
        self.assertEqual(total_off, 0.0)

    def test_outer_gate_flag(self):
        signals = RewardSignals(
            distance_to_target=3000.0 * ureg.km,
            picture_taken=True,
            target_visible=True,
        )
        cfg_on = RewardConfig(enable_energy=False, enable_distance_reward=True)
        total_on, _ = canonical_reward(signals=signals, cfg=cfg_on)
        self.assertEqual(total_on, 0.0)

        cfg_off = RewardConfig(enable_energy=False, enable_outer_gate=False)
        total_off, comp_off = canonical_reward(signals=signals, cfg=cfg_off)
        # Outside the distance band, the primary objective contributes 0.
        self.assertEqual(comp_off["no_picture_penalty"], 0.0)
        self.assertEqual(total_off, 0.0)

    def test_reward_varies_with_distance_in_slide_band(self):
        cfg = RewardConfig(enable_energy=False, enable_distance_reward=True)
        r_values = []
        for d_km in (500.0, 800.0, 1100.0, 1400.0):
            signals = RewardSignals(
                distance_to_target=d_km * ureg.km,
                picture_taken=True,
                target_visible=True,
            )
            total, _ = canonical_reward(signals=signals, cfg=cfg)
            r_values.append(total)
        # Distance-band formula is monotonically decreasing inside [d_op, d_th].
        for a, b in zip(r_values, r_values[1:]):
            self.assertGreater(a, b)


if __name__ == "__main__":
    unittest.main()
