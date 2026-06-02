"""A1: vectorized observation line — parity + timing vs baseline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[4]
EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(EXPERIMENT_ROOT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT_ROOT))

import simulation.camera_2d as camera_2d  # noqa: E402

from _runner_common import (  # noqa: E402
    baseline_cloud_specs,
    bench_sensor_kernels,
    check_observation_line_parity,
    run_coast_episode,
    write_result,
)

RESULTS_DIR = Path(__file__).resolve().parent / "results"
BASELINE_PATH = EXPERIMENT_ROOT / "results" / "baseline.json"


def main() -> None:
    specs = baseline_cloud_specs()
    parity = check_observation_line_parity(camera_module=camera_2d, cloud_arc_specs=specs)
    micro = bench_sensor_kernels(camera_module=camera_2d, cloud_arc_specs=specs)
    episode = run_coast_episode(camera_module=None)

    baseline_wall = None
    if BASELINE_PATH.is_file():
        baseline_wall = float(json.loads(BASELINE_PATH.read_text(encoding="utf-8"))["stats"]["wall_time_s"])

    speedup = None
    if baseline_wall and baseline_wall > 0:
        speedup = baseline_wall / episode["wall_time_s"]

    line_speedup = None
    if BASELINE_PATH.is_file():
        base_micro = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))["stats"]["micro_benchmark"]
        base_line = base_micro["primary_line_s"] + base_micro["secondary_line_s"]
        new_line = micro["primary_line_s"] + micro["secondary_line_s"]
        if new_line > 0:
            line_speedup = base_line / new_line

    verdict = "supported"
    if not parity["parity_ok"]:
        verdict = "falsified"
    elif line_speedup is not None and line_speedup < 5.0:
        verdict = "inconclusive"

    payload = {
        "experiment_id": "a1",
        "verdict": verdict,
        "stats": {
            **episode,
            "micro_benchmark": micro,
            "parity": parity,
            "baseline_wall_time_s": baseline_wall,
            "episode_speedup_vs_baseline": speedup,
            "line_benchmark_speedup_vs_baseline": line_speedup,
        },
    }
    out = RESULTS_DIR / "a1.json"
    write_result(out, payload)
    print(f"Wrote {out}")
    print(f"verdict={verdict} parity_ok={parity['parity_ok']} episode_speedup={speedup}")


if __name__ == "__main__":
    main()
