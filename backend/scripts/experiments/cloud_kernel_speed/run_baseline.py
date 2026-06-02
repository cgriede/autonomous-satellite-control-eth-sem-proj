"""Run production baseline timing for cloud kernel speed experiment."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[3]
EXPERIMENT_ROOT = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(EXPERIMENT_ROOT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT_ROOT))

import simulation.camera_2d as camera_2d  # noqa: E402

from _runner_common import (  # noqa: E402
    RESULTS_DIR,
    baseline_cloud_specs,
    bench_sensor_kernels,
    run_coast_episode,
    write_result,
)


def main() -> None:
    specs = baseline_cloud_specs()
    episode = run_coast_episode(camera_module=None)
    micro = bench_sensor_kernels(camera_module=camera_2d, cloud_arc_specs=specs)

    payload = {
        "experiment_id": "baseline",
        "verdict": "baseline",
        "stats": {
            **episode,
            "micro_benchmark": micro,
            "n_cloud_specs": len(specs),
        },
    }
    out = RESULTS_DIR / "baseline.json"
    write_result(out, payload)
    print(f"Wrote {out}")
    print(f"wall_time_s={episode['wall_time_s']:.2f} steps_per_s={episode['steps_per_s']:.1f}")


if __name__ == "__main__":
    main()
