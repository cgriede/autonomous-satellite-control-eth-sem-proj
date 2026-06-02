"""Shared production baseline for sensor ray batch hypothesis cycle."""

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

import simulation.camera_2d as camera_2d
from simulation.sensor_kernel import SensorKernel

from _frozen_baseline import build_high_cloud_setup, build_low_cloud_setup
from _runner_common import (
    bench_line_python_vs_accelerated,
    bench_sensor_kernel_evaluate,
    bench_sensor_kernels_legacy,
    cloud_specs_for_setup,
    run_coast_episode,
    write_hypothesis_result,
)

RESULTS_PATH = EXPERIMENT_ROOT / "results" / "baseline.json"


def main() -> None:
    low_setup = build_low_cloud_setup()
    high_setup = build_high_cloud_setup()
    low_specs = cloud_specs_for_setup(low_setup)
    high_specs = cloud_specs_for_setup(high_setup)

    low_episode = run_coast_episode(low_setup)
    high_episode = run_coast_episode(high_setup)

    low_micro_legacy = bench_sensor_kernels_legacy(
        camera_module=camera_2d, cloud_arc_specs=low_specs, n_iters=200
    )
    high_micro_legacy = bench_sensor_kernels_legacy(
        camera_module=camera_2d, cloud_arc_specs=high_specs, n_iters=50
    )
    low_micro_eval = bench_sensor_kernel_evaluate(
        sensor_eval_fn=SensorKernel.evaluate, setup=low_setup, n_iters=200
    )
    high_micro_eval = bench_sensor_kernel_evaluate(
        sensor_eval_fn=SensorKernel.evaluate, setup=high_setup, n_iters=50
    )
    high_line_bench = bench_line_python_vs_accelerated(
        camera_module=camera_2d, cloud_arc_specs=high_specs, iters_python=5, iters_accelerated=50
    )

    kpis = {
        "low_cloud_dual": {
            "episode": low_episode,
            "micro_legacy_three_calls": low_micro_legacy,
            "micro_sensor_evaluate": low_micro_eval,
            "n_clouds": len(low_setup.clouds),
        },
        "high_cloud_notebook": {
            "episode": high_episode,
            "micro_legacy_three_calls": high_micro_legacy,
            "micro_sensor_evaluate": high_micro_eval,
            "line_benchmark": high_line_bench,
            "n_clouds": len(high_setup.clouds),
        },
    }

    write_hypothesis_result(
        RESULTS_PATH,
        experiment_id="baseline",
        hypothesis_id="shared_baseline",
        phase="baseline",
        frozen_input={
            "description": "Production SensorKernel + accelerated camera_2d",
            "scenario": "s01 coast dual-camera",
            "seed": 0,
            "tunables": {
                "camera_pixel_ray_samples": 96,
                "camera_observation_line_n_bins": 100,
                "secondary_camera_observation_line_n_bins": 200,
            },
            "n_items": {"low_clouds": len(low_setup.clouds), "high_clouds": len(high_setup.clouds)},
        },
        control=None,
        treatment=None,
        delta={
            "primary_kpi": "micro_sensor_evaluate.total_s",
            "baseline_value": low_micro_eval["total_s"],
            "treatment_value": None,
            "direction": "flat",
            "relative_change_pct": None,
            "within_noise": True,
        },
        parity={"required": False, "passed": True, "notes": "production reference"},
        instrumentation={"hooks_valid": True, "notes": "no patch"},
        debug_examples={
            "low_cloud_episode_samples": low_episode["debug_examples"],
            "high_cloud_episode_samples": high_episode["debug_examples"],
        },
        files_changed=[],
        verdict="baseline",
        closeout="keep_as_idea",
    )

    # Also embed kpis at top level for branch scripts
    payload = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    payload["kpis"] = kpis
    RESULTS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(json.dumps(kpis, indent=2))
    print(f"Wrote {RESULTS_PATH}")


if __name__ == "__main__":
    main()
