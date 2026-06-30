"""Hypothesis D — verify 1280x720 export on frozen fixture."""

from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[4]
EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
BRANCH_ROOT = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(EXPERIMENT_ROOT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT_ROOT))
if str(BRANCH_ROOT) not in sys.path:
    sys.path.insert(0, str(BRANCH_ROOT))

from render_export_fork import patched_save
from _runner_common import (
    bench_video_export,
    load_frozen_series,
    write_analysis_card,
    write_hypothesis_result,
)

RESULT_PATH = BRANCH_ROOT / "results" / "d1.json"
PREVIEW_PATH = BRANCH_ROOT / "results" / "d1_preview.mp4"
ANALYSIS_PATH = EXPERIMENT_ROOT / "results" / "resolution_720p_analysis.md"


def main() -> None:
    series = load_frozen_series("gate")
    treatment = bench_video_export(
        series,
        PREVIEW_PATH,
        fixture_id="gate",
        export_patch=patched_save,
    )
    video = treatment["video"]
    parity_ok = (
        video.get("width") == 1280
        and video.get("height") == 720
        and video.get("codec") is not None
        and "h264" in str(video.get("codec", "")).lower()
    )
    verdict = "supported" if parity_ok else "falsified"
    write_hypothesis_result(
        RESULT_PATH,
        experiment_id="d1_export_resolution",
        hypothesis_id="export_resolution_720p",
        phase="D1",
        frozen_input={
            "description": "Explicit 1280x720 export via RENDER.export_pixel_width/height",
            "scenario": "gate",
            "tunables": {"width": 1280, "height": 720},
        },
        control=None,
        treatment=treatment,
        delta={"parity_resolution": f"{video.get('width')}x{video.get('height')}"},
        parity={
            "required": True,
            "passed": parity_ok,
            "notes": "ffprobe width=1280 height=720 h264",
        },
        instrumentation={"patch": "save_one_pass_video_30x"},
        debug_examples={"video_probe": video},
        files_changed=["environment_definition/constants/RENDER.py", "render/render_main.py"],
        verdict=verdict,
        closeout="promote" if parity_ok else "keep_as_idea",
    )
    write_analysis_card(ANALYSIS_PATH, hypothesis_id="export_resolution_720p", json_path=RESULT_PATH)
    print(json.dumps({"verdict": verdict, "video": video}, indent=2))


if __name__ == "__main__":
    main()
