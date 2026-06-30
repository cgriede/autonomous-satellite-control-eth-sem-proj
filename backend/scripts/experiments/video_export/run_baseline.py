"""Shared production baseline for video export hypothesis cycle."""

from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[3]
EXPERIMENT_ROOT = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(EXPERIMENT_ROOT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT_ROOT))

from _runner_common import (
    RESULTS_DIR,
    bench_video_export,
    load_frozen_series,
    write_hypothesis_result,
)
from fixtures._series_io import read_manifest

RESULTS_PATH = RESULTS_DIR / "baseline.json"
PREVIEW_PATH = RESULTS_DIR / "baseline_preview.mp4"


def main() -> None:
    series = load_frozen_series("high_cloud")
    manifest = read_manifest()
    entry = (manifest.get("fixtures") or {}).get("high_cloud") or {}
    export_kpi = bench_video_export(series, PREVIEW_PATH, fixture_id="high_cloud")

    write_hypothesis_result(
        RESULTS_PATH,
        experiment_id="baseline",
        hypothesis_id="shared_baseline",
        phase="baseline",
        frozen_input={
            "description": "Production render export (frozen high_cloud fixture, no sim)",
            "scenario": "high_cloud_notebook",
            "fixture_id": "high_cloud",
            "seed": 0,
            "tunables": {
                "export_dpi": 120,
                "export_fps": 20,
                "export_speed_multiplier": 30.0,
                "export_pixel_width": 1280,
                "export_pixel_height": 720,
            },
            "n_items": entry.get("n_clouds"),
        },
        control=None,
        treatment=None,
        delta={
            "primary_kpi": "export_wall_s",
            "baseline_value": export_kpi["export_wall_s"],
            "treatment_value": None,
            "direction": "flat",
            "relative_change_pct": None,
            "within_noise": True,
        },
        parity={"required": False, "passed": True, "notes": "production reference"},
        instrumentation={"hooks_valid": True, "notes": "frozen fixture loader"},
        debug_examples={"video_probe": export_kpi["video"]},
        files_changed=[],
        verdict="baseline",
        closeout="keep_as_idea",
    )

    payload = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    payload["kpis"] = {"high_cloud_export": export_kpi}
    payload["sim_n_steps"] = int(series.camera_observation_line_codes.shape[0])
    RESULTS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(json.dumps(export_kpi, indent=2))
    print(f"Wrote {RESULTS_PATH}")


if __name__ == "__main__":
    main()
