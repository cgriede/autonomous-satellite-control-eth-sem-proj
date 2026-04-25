import warnings
import unittest

from simulation.scheduler import resolve_controller_interval_steps


class SchedulerPolicyTest(unittest.TestCase):
    def test_exact_multiple_no_warning(self):
        with warnings.catch_warnings(record=True) as rec:
            warnings.simplefilter("always")
            steps, effective_s = resolve_controller_interval_steps(
                configured_interval_s=0.2,
                sim_dt_s=0.1,
            )
        self.assertEqual(steps, 2)
        self.assertAlmostEqual(effective_s, 0.2)
        self.assertEqual(len(rec), 0)

    def test_round_to_nearest_multiple(self):
        with warnings.catch_warnings(record=True) as rec:
            warnings.simplefilter("always")
            steps, effective_s = resolve_controller_interval_steps(
                configured_interval_s=0.26,
                sim_dt_s=0.1,
            )
        self.assertEqual(steps, 3)
        self.assertAlmostEqual(effective_s, 0.3)
        self.assertGreaterEqual(len(rec), 1)


if __name__ == "__main__":
    unittest.main()
