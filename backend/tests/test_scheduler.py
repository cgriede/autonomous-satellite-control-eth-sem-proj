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
        import simulation.scheduler as scheduler_module

        scheduler_module._SCHEDULER_WARNED = False
        with warnings.catch_warnings(record=True) as rec:
            warnings.simplefilter("always")
            steps, effective_s = resolve_controller_interval_steps(
                configured_interval_s=0.26,
                sim_dt_s=0.1,
            )
        self.assertEqual(steps, 3)
        self.assertAlmostEqual(effective_s, 0.3)
        self.assertEqual(len(rec), 1)
        msg = str(rec[0].message)
        self.assertIn("0.26 s", msg)
        self.assertIn("0.1 s", msg)
        self.assertIn("0.3 s", msg)
        self.assertIn("3 sim steps", msg)


if __name__ == "__main__":
    unittest.main()
