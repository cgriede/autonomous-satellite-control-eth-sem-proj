"""Hypothesis B — lite export layout vs shared baseline."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Callable

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
    patch_lite_export_panels,
    write_analysis_card,
    write_hypothesis_result,
)
from fixtures._series_io import read_manifest

BASELINE_PATH = EXPERIMENT_ROOT / "results" / "baseline.json"
RESULT_PATH = BRANCH_ROOT / "results" / "b1.json"
PREVIEW_PATH = BRANCH_ROOT / "results" / "b1_preview.mp4"
ANALYSIS_PATH = EXPERIMENT_ROOT / "results" / "lite_layout_analysis.md"


def _load_baseline_export() -> dict:
    payload = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    return payload["kpis"]["high_cloud_export"]


def _lite_pre_hook() -> Callable[[], None]:
    _, restore = patch_lite_export_panels()
    return restore


def main() -> None:
    if not BASELINE_PATH.is_file():
        raise FileNotFoundError(f"Run run_baseline.py first: {BASELINE_PATH}")

    baseline = _load_baseline_export()
    series = load_frozen_series("high_cloud")
    entry = (read_manifest().get("fixtures") or {}).get("high_cloud") or {}
    treatment = bench_video_export(
        series,
        PREVIEW_PATH,
        export_patch=patched_save,
        render_pre_hook=_lite_pre_hook,
    )

    speedup = baseline["export_wall_s"] / max(treatment["export_wall_s"], 1e-9)
    wall_reduction_pct = 100.0 * (1.0 - 1.0 / max(speedup, 1e-9))
    speed_gate = 1.2
    parity_ok = treatment["video"].get("codec") is not None and "h264" in str(
        treatment["video"].get("codec", "")
    ).lower()

    if speedup >= speed_gate and parity_ok:
        verdict = "supported"
        closeout = "promote"
    elif speedup < speed_gate:
        verdict = "falsified"
        closeout = "keep_as_idea"
    else:
        verdict = "inconclusive"
        closeout = "keep_as_idea"

    write_hypothesis_result(
        RESULT_PATH,
        experiment_id="b1_lite_layout",
        hypothesis_id="lite_layout",
        phase="B1",
        frozen_input={
            "description": "Export without telemetry/reward/torque/secondary cam panels",
            "scenario": "high_cloud_notebook",
            "seed": 0,
            "tunables": {"lite_panels": True},
            "n_items": entry.get("n_clouds"),
        },
        control={
            "label": "baseline",
            "export_wall_s": baseline["export_wall_s"],
            "export_frames_per_s": baseline["export_frames_per_s"],
            "n_frames_drawn": baseline["n_frames_drawn"],
        },
        treatment={
            "label": "lite_layout",
            "export_wall_s": treatment["export_wall_s"],
            "export_frames_per_s": treatment["export_frames_per_s"],
            "n_frames_drawn": treatment["n_frames_drawn"],
        },
        delta={
            "primary_kpi": "export_wall_s",
            "export_speedup": speedup,
            "relative_wall_reduction_pct": wall_reduction_pct,
            "speed_gate": speed_gate,
            "speed_gate_met": speedup >= speed_gate,
        },
        parity={
            "required": True,
            "passed": parity_ok,
            "notes": "H.264 required; layout differs by design (orbit+closeup retained)",
        },
        instrumentation={"patch": "SHOW_* flags before render_from_series"},
        debug_examples={"baseline_video": baseline.get("video"), "treatment_video": treatment["video"]},
        files_changed=["b_lite_layout/render_export_fork.py"],
        verdict=verdict,
        closeout=closeout,
    )
    write_analysis_card(ANALYSIS_PATH, hypothesis_id="lite_layout", json_path=RESULT_PATH)
    print(json.dumps({"speedup": speedup, "verdict": verdict}, indent=2))
    print(f"Wrote {RESULT_PATH}, {ANALYSIS_PATH}")


if __name__ == "__main__":
    main()
