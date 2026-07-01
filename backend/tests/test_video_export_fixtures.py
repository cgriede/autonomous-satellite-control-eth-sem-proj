"""Tests for frozen video export fixtures (no run_simulation in hot path)."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
VIDEO_EXPORT = BACKEND_DIR / "scripts" / "experiments" / "video_export"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(VIDEO_EXPORT) not in sys.path:
    sys.path.insert(0, str(VIDEO_EXPORT))

from fixtures._series_io import (
    FIXTURE_FILES,
    MANIFEST_PATH,
    _sha256_file,
    load_frozen_series,
    read_manifest,
)
from _runner_common import bench_video_export


class VideoExportFixturesTest(unittest.TestCase):
    def test_manifest_matches_gate_fixture(self):
        if not MANIFEST_PATH.is_file():
            self.skipTest("fixtures not baked; run bake_series_fixtures.py --all")
        manifest = read_manifest()
        gate = manifest["fixtures"]["gate"]
        path = VIDEO_EXPORT / "fixtures" / FIXTURE_FILES["gate"]
        self.assertEqual(_sha256_file(path), gate["sha256_hex"])

    def test_gate_fixture_exports_h264_mp4(self):
        if not MANIFEST_PATH.is_file():
            self.skipTest("fixtures not baked")
        series = load_frozen_series("gate")
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "gate_preview.mp4"
            kpi = bench_video_export(series, out, fixture_id="gate")
            self.assertTrue(out.exists())
            self.assertGreater(out.stat().st_size, 0)
            codec = str(kpi["video"].get("codec", "")).lower()
            self.assertIn("h264", codec)
            self.assertEqual(kpi["video"].get("width"), 1280)
            self.assertEqual(kpi["video"].get("height"), 720)

    def test_runner_common_has_no_sim_import(self):
        import _runner_common as rc

        source = (VIDEO_EXPORT / "_runner_common.py").read_text(encoding="utf-8")
        self.assertNotIn("run_simulation", source)


if __name__ == "__main__":
    unittest.main()
