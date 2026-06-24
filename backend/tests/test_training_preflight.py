"""Every registered training feature check must pass."""

from __future__ import annotations

import unittest
from pathlib import Path

from autonomous_control.feature_selection import ControllerFeatureConfig
from autonomous_control.training_preflight import (
    TRAINING_FEATURE_CHECKS,
    TrainingPreflightError,
    digest_for_training_preflight_fingerprint,
    run_training_gate,
    training_preflight_fingerprint_payload,
    run_training_preflight,
)


class TrainingPreflightRegistryTest(unittest.TestCase):
    def test_registry_is_non_empty(self):
        self.assertGreater(len(TRAINING_FEATURE_CHECKS), 0)

    def test_registry_names_unique(self):
        names = [item.name for item in TRAINING_FEATURE_CHECKS]
        self.assertEqual(len(names), len(set(names)))

    def test_each_registered_check_passes(self):
        for item in TRAINING_FEATURE_CHECKS:
            with self.subTest(check=item.name):
                item.check()

    def test_run_training_preflight_passes(self):
        run_training_preflight()

    def test_run_training_preflight_reports_failures(self):
        from autonomous_control.training_preflight import TrainingFeatureCheck

        def _fail() -> None:
            raise ValueError("boom")

        with self.assertRaises(TrainingPreflightError) as ctx:
            run_training_preflight(
                checks=(
                    TrainingFeatureCheck("bad", "intentional failure", _fail),
                )
            )
        self.assertIn("bad", str(ctx.exception))


class TrainingPreflightCacheTest(unittest.TestCase):
    def test_fingerprint_stable_for_identical_inputs(self):
        root = Path(__file__).resolve().parents[2]
        fp = training_preflight_fingerprint_payload(repo_root=root)
        self.assertEqual(
            digest_for_training_preflight_fingerprint(fp),
            digest_for_training_preflight_fingerprint(fp),
        )

    def test_fingerprint_changes_when_feature_config_changes(self):
        root = Path(__file__).resolve().parents[2]
        fp1 = training_preflight_fingerprint_payload(repo_root=root)
        fp2 = training_preflight_fingerprint_payload(
            feature_config=ControllerFeatureConfig(attitude_keys=("body_z_angle_rad",)),
            repo_root=root,
        )
        self.assertNotEqual(
            digest_for_training_preflight_fingerprint(fp1),
            digest_for_training_preflight_fingerprint(fp2),
        )

    def test_run_training_gate_cache_hit_skips_checks(self):
        root = Path(__file__).resolve().parents[2]
        cache_path = root / "backend" / "autonomous_control" / "models" / ".cache" / (
            "test_training_preflight_gate.json"
        )
        if cache_path.is_file():
            cache_path.unlink()
        try:
            self.assertTrue(
                run_training_gate(
                    skip_pytest=True,
                    use_cache=True,
                    cache_path=cache_path,
                )
            )
            self.assertFalse(
                run_training_gate(
                    skip_pytest=True,
                    use_cache=True,
                    cache_path=cache_path,
                )
            )
        finally:
            if cache_path.is_file():
                cache_path.unlink()


if __name__ == "__main__":
    unittest.main()
