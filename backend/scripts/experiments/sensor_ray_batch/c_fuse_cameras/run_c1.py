"""Hypothesis C — run fused SensorKernel.evaluate vs shared baseline."""

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

from sensor_kernel_fork import evaluate_fused
from _frozen_baseline import build_low_cloud_setup
from _runner_common import (
    bench_sensor_kernel_evaluate,
    check_sensor_parity,
    run_coast_episode,
    write_hypothesis_result,
)

BASELINE_PATH = EXPERIMENT_ROOT / "results" / "baseline.json"
RESULT_PATH = BRANCH_ROOT / "results" / "c1.json"


def _load_baseline_kpis() -> dict:
    if not BASELINE_PATH.is_file():
        raise FileNotFoundError(f"Run run_baseline.py first: {BASELINE_PATH}")
    payload = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    return payload["kpis"]


def main() -> None:
    baseline_kpis = _load_baseline_kpis()
    setup = build_low_cloud_setup()

    parity = check_sensor_parity(sensor_eval_fn=evaluate_fused, setup=setup)
    micro = bench_sensor_kernel_evaluate(sensor_eval_fn=evaluate_fused, setup=setup, n_iters=200)
    episode = run_coast_episode(setup, sensor_eval_fn=evaluate_fused)

    baseline_micro = baseline_kpis["low_cloud_dual"]["micro_sensor_evaluate"]
    baseline_episode = baseline_kpis["low_cloud_dual"]["episode"]
    speedup_micro = baseline_micro["total_s"] / max(micro["total_s"], 1e-9)
    speedup_episode = episode["steps_per_s"] / max(baseline_episode["steps_per_s"], 1e-9)

    parity_ok = parity["parity_ok"]
    success_speed = speedup_micro >= 1.5 and speedup_episode >= 1.0
    if parity_ok and success_speed:
        verdict = "supported"
        closeout = "promote"
    elif not parity_ok:
        verdict = "falsified"
        closeout = "delete"
    elif speedup_micro < 1.5:
        verdict = "falsified"
        closeout = "keep_as_idea"
    else:
        verdict = "inconclusive"
        closeout = "keep_as_idea"

    write_hypothesis_result(
        RESULT_PATH,
        experiment_id="c1_fuse_cameras",
        hypothesis_id="fuse_cameras",
        phase="X1",
        frozen_input={
            "description": "low_cloud_dual s01 coast dual-camera",
            "scenario": "s01 coast",
            "seed": 0,
            "tunables": {"camera_pixel_ray_samples": 96, "n_bins": 100, "n_bins_secondary": 200},
            "n_items": len(setup.clouds),
        },
        control={
            "label": "baseline",
            "variant": "production SensorKernel.evaluate",
            "kpis": {"micro": baseline_micro, "episode": baseline_episode},
            "result_path": str(BASELINE_PATH),
        },
        treatment={
            "label": "C1",
            "variant": "fused 396-ray batch in sensor_kernel_fork",
            "kpis": {"micro": micro, "episode": episode, "speedup_micro": speedup_micro, "speedup_episode": speedup_episode},
            "result_path": str(RESULT_PATH),
        },
        delta={
            "primary_kpi": "micro_sensor_evaluate.total_s",
            "baseline_value": baseline_micro["total_s"],
            "treatment_value": micro["total_s"],
            "direction": "better" if speedup_micro >= 1.5 else "flat",
            "relative_change_pct": (speedup_micro - 1.0) * 100.0,
            "within_noise": abs(speedup_micro - 1.0) < 0.05,
        },
        parity={
            "required": True,
            "passed": parity_ok,
            "notes": f"total_mismatches={parity['total_mismatches']}",
        },
        instrumentation={"hooks_valid": True, "notes": "evaluate_fused patched via SensorKernel.evaluate"},
        debug_examples={
            **parity.get("debug_examples", {}),
            "episode_samples": episode["debug_examples"],
        },
        files_changed=["c_fuse_cameras/sensor_kernel_fork.py"],
        verdict=verdict,
        closeout=closeout,
    )

    print(json.dumps({"verdict": verdict, "speedup_micro": speedup_micro, "parity_ok": parity_ok}, indent=2))
    print(f"Wrote {RESULT_PATH}")


if __name__ == "__main__":
    main()
