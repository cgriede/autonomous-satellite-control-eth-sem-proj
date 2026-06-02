"""B1: FOV cloud cull — parity + cull stats + timing vs A1."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

BACKEND_DIR = Path(__file__).resolve().parents[4]
EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(EXPERIMENT_ROOT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT_ROOT))

import simulation.camera_2d as camera_2d  # noqa: E402
import cloud_fov_cull as cloud_fov_cull  # noqa: E402

from _runner_common import (  # noqa: E402
    baseline_cloud_specs,
    check_observation_line_parity,
    run_coast_episode,
    write_result,
)
from environment_definition.constants import EARTH_RADIUS, UREG as ureg  # noqa: E402
from environment_definition.mission_profiles.s00_simulation_build_sample_fl import SATELLITE_ALTITUDE  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parent / "results"
A1_PATH = EXPERIMENT_ROOT / "a_vectorized_line" / "results" / "a1.json"


def _sample_cull_stats(cloud_arc_specs: list[dict[str, float]], *, n_samples: int = 500) -> dict[str, float]:
    sat_xy = np.array([6800.0, 200.0], dtype=float)
    bore = np.array([-1.0, 0.0], dtype=float)
    n_bins = 100
    half_fov = 0.05
    angles = np.linspace(-half_fov, half_fov, n_bins)
    cos_a, sin_a = np.cos(angles), np.sin(angles)
    x, y = float(bore[0]), float(bore[1])
    ray_dirs = np.stack([cos_a * x - sin_a * y, sin_a * x + cos_a * y], axis=1)

    t0 = time.perf_counter()
    total_culled = 0
    for _ in range(n_samples):
        _, stats = cloud_fov_cull.filter_cloud_specs_for_camera_fov(sat_xy, ray_dirs, cloud_arc_specs)
        total_culled += int(stats["clouds_culled"])
    overhead_us = (time.perf_counter() - t0) / n_samples * 1e6
    return {
        "clouds_total": len(cloud_arc_specs),
        "mean_clouds_culled_per_call": total_culled / n_samples,
        "cull_overhead_us_per_call": overhead_us,
    }


def main() -> None:
    specs = baseline_cloud_specs()
    parity = check_observation_line_parity(camera_module=camera_2d, cloud_arc_specs=specs)
    cull_stats = _sample_cull_stats(specs)
    episode = run_coast_episode(camera_module=None)

    a1_wall = None
    if A1_PATH.is_file():
        a1_wall = float(json.loads(A1_PATH.read_text(encoding="utf-8"))["stats"]["wall_time_s"])

    verdict = "supported"
    if not parity["parity_ok"]:
        verdict = "falsified"
    elif cull_stats["mean_clouds_culled_per_call"] <= 0:
        verdict = "inconclusive"

    payload = {
        "experiment_id": "b1",
        "verdict": verdict,
        "stats": {
            **episode,
            "parity": parity,
            "cull_stats": cull_stats,
            "a1_wall_time_s": a1_wall,
        },
    }
    out = RESULTS_DIR / "b1.json"
    write_result(out, payload)
    print(f"Wrote {out}")
    print(f"verdict={verdict} mean_clouds_culled={cull_stats['mean_clouds_culled_per_call']:.2f}")


if __name__ == "__main__":
    main()
