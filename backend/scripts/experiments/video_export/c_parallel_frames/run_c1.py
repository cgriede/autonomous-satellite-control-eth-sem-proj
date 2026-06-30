"""Hypothesis C — parallel CPU draw + NVENC encode vs serial."""

from __future__ import annotations

import json
import os
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

from c_parallel_frames._export_fork import patched_save
from _runner_common import (
    bench_video_export,
    load_frozen_series,
    write_analysis_card,
    write_hypothesis_result,
)

RESULT_PATH = BRANCH_ROOT / "results" / "c1.json"
PREVIEW_SERIAL = BRANCH_ROOT / "results" / "c1_serial_preview.mp4"
PREVIEW_PARALLEL = BRANCH_ROOT / "results" / "c1_parallel_preview.mp4"
ANALYSIS_PATH = EXPERIMENT_ROOT / "results" / "parallel_frames_analysis.md"


def main() -> None:
    n_workers = int(os.environ.get("VIDEO_EXPORT_WORKERS", min(os.cpu_count() or 4, 8)))
    os.environ["VIDEO_EXPORT_WORKERS"] = str(n_workers)

    series = load_frozen_series("training_sparse")
    control = bench_video_export(
        series,
        PREVIEW_SERIAL,
        fixture_id="training_sparse",
        encoder="ffmpeg",
    )
    treatment = bench_video_export(
        series,
        PREVIEW_PARALLEL,
        fixture_id="training_sparse",
        export_patch=patched_save,
    )

    speedup = control["export_wall_s"] / max(treatment["export_wall_s"], 1e-9)
    speed_gate = 1.5
    parity_ok = treatment["video"].get("codec") is not None and "h264" in str(
        treatment["video"].get("codec", "")
    ).lower()

    if speedup >= speed_gate and parity_ok:
        verdict = "supported"
        closeout = "promote"
    elif speedup < speed_gate:
        verdict = "inconclusive"
        closeout = "keep_as_idea"
    else:
        verdict = "inconclusive"
        closeout = "keep_as_idea"

    write_hypothesis_result(
        RESULT_PATH,
        experiment_id="c1_parallel_frames",
        hypothesis_id="parallel_frames",
        phase="C1",
        frozen_input={
            "description": f"Parallel frame export with {n_workers} CPU workers + NVENC lane",
            "scenario": "training_sparse",
            "tunables": {"n_workers": n_workers},
        },
        control={
            "label": "serial",
            "export_wall_s": control["export_wall_s"],
            "export_frames_per_s": control["export_frames_per_s"],
            "n_frames_drawn": control["n_frames_drawn"],
        },
        treatment={
            "label": "parallel",
            "export_wall_s": treatment["export_wall_s"],
            "export_frames_per_s": treatment["export_frames_per_s"],
            "n_frames_drawn": treatment["n_frames_drawn"],
            "draw_wall_s": treatment.get("draw_wall_s"),
            "encode_wall_s": treatment.get("encode_wall_s"),
            "n_workers": n_workers,
        },
        delta={
            "export_speedup": speedup,
            "speed_gate": speed_gate,
            "speed_gate_met": speedup >= speed_gate,
        },
        parity={"required": True, "passed": parity_ok, "notes": "H.264 required"},
        instrumentation={"patch": "save_one_pass_video_parallel", "n_workers": n_workers},
        debug_examples={"control_video": control.get("video"), "treatment_video": treatment.get("video")},
        files_changed=["c_parallel_frames/_export_fork.py"],
        verdict=verdict,
        closeout=closeout,
    )
    write_analysis_card(ANALYSIS_PATH, hypothesis_id="parallel_frames", json_path=RESULT_PATH)
    print(json.dumps({"speedup": speedup, "verdict": verdict, "n_workers": n_workers}, indent=2))


if __name__ == "__main__":
    main()
