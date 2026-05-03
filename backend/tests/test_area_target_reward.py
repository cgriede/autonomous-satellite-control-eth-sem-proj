import unittest

from autonomous_control.reward import RewardConfig, RewardSignals, compute_reward
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg


class AreaTargetRewardTest(unittest.TestCase):
    def test_area_intersection_reward_inside_vs_outside(self):
        cfg = RewardConfig(
            enable_distance_reward=False,
            enable_energy=False,
            enable_area_intersection=True,
            enable_area_novelty=False,
            k_area_intersection=100.0,
        )
        outside_signals = RewardSignals(
            distance_to_target=1000.0 * ureg.km,
            picture_taken=True,
            target_visible=False,
            target_area_intersection_ratio=0.0,
        )
        inside_signals = RewardSignals(
            distance_to_target=1000.0 * ureg.km,
            picture_taken=True,
            target_visible=True,
            target_area_intersection_ratio=0.5,
        )
        outside_total, _ = compute_reward(signals=outside_signals, cfg=cfg)
        inside_total, _ = compute_reward(signals=inside_signals, cfg=cfg)
        self.assertEqual(outside_total, 0.0)
        self.assertGreater(inside_total, outside_total)

    def test_area_intersection_monotonicity(self):
        cfg = RewardConfig(
            enable_distance_reward=False,
            enable_energy=False,
            enable_area_intersection=True,
            enable_area_novelty=False,
            k_area_intersection=100.0,
        )
        totals = []
        for ratio in (0.1, 0.3, 0.6):
            total, _ = compute_reward(
                signals=RewardSignals(
                    distance_to_target=1000.0 * ureg.km,
                    picture_taken=True,
                    target_visible=True,
                    target_area_intersection_ratio=ratio,
                ),
                cfg=cfg,
            )
            totals.append(total)
        self.assertGreater(totals[1], totals[0])
        self.assertGreater(totals[2], totals[1])

    def test_area_and_energy_terms_both_applied(self):
        cfg = RewardConfig(
            enable_distance_reward=False,
            enable_energy=True,
            enable_area_intersection=True,
            enable_area_novelty=False,
            k_area_intersection=100.0,
            k_energy=1.0,
        )
        signals = RewardSignals(
            distance_to_target=900.0 * ureg.km,
            picture_taken=True,
            target_visible=True,
            target_area_intersection_ratio=0.5,
            wheel_inertia=2.0 * ureg.kg * ureg.m**2,
            omega_before=0.0 * ureg.rad / ureg.s,
            omega_after=1.0 * ureg.rad / ureg.s,
        )
        total, components = compute_reward(signals=signals, cfg=cfg)
        self.assertAlmostEqual(
            total,
            components["area_intersection_reward"] + components["energy_reward"],
            places=9,
        )
        self.assertGreater(components["area_intersection_reward"], 0.0)
        self.assertLessEqual(components["energy_reward"], 0.0)

    def test_novelty_reward_is_additive(self):
        cfg = RewardConfig(
            enable_distance_reward=False,
            enable_energy=False,
            enable_area_intersection=True,
            enable_area_novelty=True,
            k_area_intersection=100.0,
            k_area_novelty=25.0,
        )
        base_signals = RewardSignals(
            distance_to_target=1000.0 * ureg.km,
            picture_taken=True,
            target_visible=True,
            target_area_intersection_ratio=0.4,
            target_area_novelty_ratio=0.0,
        )
        novelty_signals = RewardSignals(
            distance_to_target=1000.0 * ureg.km,
            picture_taken=True,
            target_visible=True,
            target_area_intersection_ratio=0.4,
            target_area_novelty_ratio=0.4,
        )
        base_total, _ = compute_reward(signals=base_signals, cfg=cfg)
        novelty_total, _ = compute_reward(signals=novelty_signals, cfg=cfg)
        self.assertGreater(novelty_total, base_total)


if __name__ == "__main__":
    unittest.main()
