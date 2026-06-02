"""Hypothesis D — run tensorized cloud×ray intersection vs shared baseline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

BACKEND_DIR = Path(__file__).resolve().parents[4]
EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
BRANCH_ROOT = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(EXPERIMENT_ROOT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT_ROOT))
if str(BRANCH_ROOT) not in sys.path:
    sys.path.insert(0, str(BRANCH_ROOT))

import simulation.camera_2d as camera_2d_mod
from camera_2d_fork import apply_tensor_patch, remove_tensor_patch
from environment_definition.constants import EARTH_RADIUS, UREG as ureg
from simulation.camera_2d import observation_codes_to_ascii_line, simulate_camera_observation_line_1d

from _frozen_baseline import build_high_cloud_setup, build_low_cloud_setup
from _runner_common import (
    bench_line_python_vs_accelerated,
    bench_sensor_kernels_legacy,
    cloud_specs_for_setup,
    write_hypothesis_result,
)

BASELINE_PATH = EXPERIMENT_ROOT / "results" / "baseline.json"
RESULT_PATH = BRANCH_ROOT / "results" / "d1.json"


def _load_baseline_kpis() -> dict:
    if not BASELINE_PATH.is_file():
        raise FileNotFoundError(f"Run run_baseline.py first: {BASELINE_PATH}")
    payload = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    return payload["kpis"]


def _line_parity_cases(*, original_fn) -> tuple[int, list[dict]]:
    low_setup = build_low_cloud_setup()
    high_setup = build_high_cloud_setup()
    earth_r = float(EARTH_RADIUS.to(ureg.km).magnitude)
    sat_xy = np.array([6800.0, 200.0], dtype=float)
    bore = np.array([-1.0, 0.0], dtype=float)
    total_mismatches = 0
    cases: list[dict] = []

    for label, setup, specs in (
        ("low", low_setup, cloud_specs_for_setup(low_setup)),
        ("high", high_setup, cloud_specs_for_setup(high_setup)),
    ):
        altitude = setup.resolve().altitude
        kwargs = dict(
            sat_pos_xy_km=sat_xy,
            boresight_dir_unit_xy=bore,
            altitude=altitude,
            earth_radius_km=earth_r,
            sim_time_s=20.0,
            sim_total_s=200.0,
            n_bins=100,
            cloud_arc_specs=specs,
            kernel_backend="accelerated",
        )
        ref = simulate_camera_observation_line_1d(**kwargs)
        apply_tensor_patch()
        try:
            cand = simulate_camera_observation_line_1d(**kwargs)
        finally:
            remove_tensor_patch(original_fn)
        mm = int(np.count_nonzero(ref.observation_types != cand.observation_types))
        total_mismatches += mm
        cases.append(
            {
                "fixture": label,
                "mismatches": mm,
                "ref_ascii": observation_codes_to_ascii_line(ref.observation_types),
                "cand_ascii": observation_codes_to_ascii_line(cand.observation_types),
            }
        )
    return total_mismatches, cases


def main() -> None:
    baseline_kpis = _load_baseline_kpis()
    low_setup = build_low_cloud_setup()
    high_setup = build_high_cloud_setup()
    low_specs = cloud_specs_for_setup(low_setup)
    high_specs = cloud_specs_for_setup(high_setup)

    original_fn = camera_2d_mod._batch_cloud_hits_t_best
    total_mismatches, parity_cases = _line_parity_cases(original_fn=original_fn)

    apply_tensor_patch()
    try:
        high_line = bench_line_python_vs_accelerated(
            camera_module=camera_2d_mod,
            cloud_arc_specs=high_specs,
            iters_python=5,
            iters_accelerated=50,
        )
        low_micro = bench_sensor_kernels_legacy(camera_module=camera_2d_mod, cloud_arc_specs=low_specs, n_iters=200)
    finally:
        remove_tensor_patch(original_fn)

    baseline_high_line = baseline_kpis["high_cloud_notebook"]["line_benchmark"]
    baseline_low_micro = baseline_kpis["low_cloud_dual"]["micro_legacy_three_calls"]

    prod_line_per_call = baseline_high_line["production_line_s_per_call"]
    tensor_line_per_call = high_line["accelerated_line_s_per_call"]
    line_speedup = prod_line_per_call / max(tensor_line_per_call, 1e-9)
    low_regression = low_micro["per_call_s"] / max(baseline_low_micro["per_call_s"], 1e-9)

    parity_ok = total_mismatches == 0
    if parity_ok and line_speedup >= 2.0 and low_regression <= 1.05:
        verdict = "supported"
        closeout = "promote"
    elif not parity_ok:
        verdict = "falsified"
        closeout = "delete"
    elif line_speedup < 2.0:
        verdict = "falsified"
        closeout = "keep_as_idea"
    else:
        verdict = "inconclusive"
        closeout = "keep_as_idea"

    write_hypothesis_result(
        RESULT_PATH,
        experiment_id="d1_tensor_clouds",
        hypothesis_id="tensor_clouds",
        phase="X1",
        frozen_input={
            "description": "tensor (C×N) cloud hits on high_cloud_notebook fixture",
            "scenario": "high_cloud_notebook + low_cloud guardrail",
            "seed": 42,
            "tunables": {},
            "n_items": {"low": len(low_setup.clouds), "high": len(high_setup.clouds)},
        },
        control={
            "label": "baseline",
            "variant": "production _batch_cloud_hits_t_best loop",
            "kpis": {"high_line": baseline_high_line, "low_micro": baseline_low_micro},
            "result_path": str(BASELINE_PATH),
        },
        treatment={
            "label": "D1",
            "variant": "tensor _batch_cloud_hits_t_best",
            "kpis": {"high_line": high_line, "low_micro": low_micro, "line_speedup": line_speedup},
            "result_path": str(RESULT_PATH),
        },
        delta={
            "primary_kpi": "line_speedup_per_call",
            "baseline_value": 1.0,
            "treatment_value": line_speedup,
            "direction": "better" if line_speedup >= 2.0 else "flat",
            "relative_change_pct": (line_speedup - 1.0) * 100.0,
            "within_noise": abs(line_speedup - 1.0) < 0.05,
        },
        parity={"required": True, "passed": parity_ok, "notes": f"total_mismatches={total_mismatches}"},
        instrumentation={"hooks_valid": True, "notes": "patched camera_2d._batch_cloud_hits_t_best"},
        debug_examples={"parity_cases": parity_cases, "low_regression_factor": low_regression},
        files_changed=["d_tensor_clouds/camera_2d_fork.py"],
        verdict=verdict,
        closeout=closeout,
    )

    print(json.dumps({"verdict": verdict, "line_speedup": line_speedup, "parity_ok": parity_ok}, indent=2))
    print(f"Wrote {RESULT_PATH}")


if __name__ == "__main__":
    main()
