"""One-time bake of frozen SimulationStateSeries fixtures (sole sim entry for video_export)."""

from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import numpy as np

BACKEND_DIR = Path(__file__).resolve().parents[3]
EXPERIMENT_ROOT = Path(__file__).resolve().parent
S01_DIR = BACKEND_DIR / "notebooks" / "s01"
FIXTURES_DIR = EXPERIMENT_ROOT / "fixtures"

for path in (BACKEND_DIR, S01_DIR, EXPERIMENT_ROOT, FIXTURES_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from environment_definition.constants.SIMULATION import RenderMode, SimulationConfig
from environment_definition.mission_profiles.s01_multiple_targets_fwd_fish import build_setup
from simulation.run_simulation import run_simulation

from _frozen_baseline import build_baseline_sim_config, build_high_cloud_setup
from fixtures._series_io import (
    FIXTURE_FILES,
    compute_export_frame_counts,
    save_series_fixture,
    write_manifest,
)


def _git_head() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=BACKEND_DIR.parent,
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout.strip()[:12]
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def _apply_training_dt_profile() -> None:
    overnight = EXPERIMENT_ROOT.parent / "ml_algo_overnight"
    spec = importlib.util.spec_from_file_location("bake_sim_fork", overnight / "_sim_constants_fork.py")
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    dt_15 = next(p for p in mod.DT_CANDIDATES if p.label == "dt_1.5s")
    mod.apply_dt_profile(dt_15)


def bake_gate() -> dict:
    from tests.test_training_run_artifacts import _minimal_series

    series = _minimal_series(n=5)
    path = FIXTURES_DIR / FIXTURE_FILES["gate"]
    meta = save_series_fixture(path, series)
    meta["fixture_id"] = "gate"
    meta["baked_from"] = "tests.test_training_run_artifacts._minimal_series(n=5)"
    meta.update(compute_export_frame_counts(float(series.metadata.sim_total_s)))
    return meta


def bake_high_cloud() -> dict:
    setup = build_high_cloud_setup()
    sim_cfg = build_baseline_sim_config()
    series = run_simulation(setup=setup, simulation_config=sim_cfg)
    path = FIXTURES_DIR / FIXTURE_FILES["high_cloud"]
    meta = save_series_fixture(path, series)
    meta["fixture_id"] = "high_cloud"
    meta["baked_from"] = "build_high_cloud_setup + run_simulation"
    meta["n_items"] = len(setup.clouds)
    meta.update(compute_export_frame_counts(float(series.metadata.sim_total_s)))
    return meta


def bake_training_sparse() -> dict:
    _apply_training_dt_profile()
    setup = build_setup(seed=7, include_cameras=True)
    sim_cfg = SimulationConfig(render_mode=RenderMode.HEADLESS, builtin_torque_policy="random")
    series = run_simulation(setup=setup, simulation_config=sim_cfg)
    path = FIXTURES_DIR / FIXTURE_FILES["training_sparse"]
    meta = save_series_fixture(path, series)
    meta["fixture_id"] = "training_sparse"
    meta["baked_from"] = "S01 build_setup(seed=7) + DT_1.5s + run_simulation"
    meta.update(compute_export_frame_counts(float(series.metadata.sim_total_s)))
    return meta


def main() -> None:
    parser = argparse.ArgumentParser(description="Bake frozen SimulationStateSeries fixtures")
    parser.add_argument(
        "--fixture",
        choices=("training_sparse", "high_cloud", "gate", "all"),
        default="all",
    )
    args = parser.parse_args()

    bakers = {
        "gate": bake_gate,
        "high_cloud": bake_high_cloud,
        "training_sparse": bake_training_sparse,
    }
    selected = list(bakers) if args.fixture == "all" else [args.fixture]
    baked: dict[str, dict] = {}
    manifest_path = FIXTURES_DIR / "manifest.json"
    if manifest_path.is_file() and args.fixture != "all":
        import json

        existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        baked.update(existing.get("fixtures") or {})
    for name in selected:
        print(f"Baking {name}...")
        baked[name] = bakers[name]()
        print(f"  -> {baked[name]['path']} ({baked[name]['bytes']} bytes, sha256={baked[name]['sha256_hex'][:12]}...)")

    stamp = datetime.now(timezone.utc).isoformat()
    write_manifest(
        baked,
        baked_from=f"bake_series_fixtures.py @ {stamp} git={_git_head()}",
    )
    print(f"Wrote {FIXTURES_DIR / 'manifest.json'}")


if __name__ == "__main__":
    main()
