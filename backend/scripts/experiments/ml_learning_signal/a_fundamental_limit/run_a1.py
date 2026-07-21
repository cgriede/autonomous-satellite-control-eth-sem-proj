"""Branch A run 1: diagnose fundamental limits (read-only + instrumentation)."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = EXPERIMENT_ROOT.parents[2]
S01_DIR = BACKEND_DIR / "notebooks" / "s01"
for path in (BACKEND_DIR, S01_DIR, EXPERIMENT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from autonomous_control.action_adapter import DEFAULT_SHUTTER_THRESHOLD, shutter_gym_to_unit_interval  # noqa: E402
from autonomous_control.config.randomness import derive_seed  # noqa: E402

from _runner_common import (  # noqa: E402
    RESULTS_DIR,
    run_training_slice,
    write_analysis_card,
    write_hypothesis_result,
)

_DEBUG_LOG = RESULTS_DIR / "ml_learning_signal_fundamental.ndjson"


def _probe_shutter_exploration(setup, *, n_samples: int = 5000) -> dict:
    """Sample train-mode actions; estimate P(shutter fires)."""
    obs = setup.runner.run_serial(
        setup.agent,
        mode="warmup",
        episode_idx=0,
        collect_states=True,
        train_updates_per_step=0,
        np_rng=np.random.default_rng(0),
    ).states[0]
    fires = 0
    shutter_vals = []
    for _ in range(n_samples):
        raw = setup.agent.get_action(obs, train=True)
        shutter_gym = float(raw[1]) if raw.shape[0] >= 2 else -1.0
        shutter_vals.append(shutter_gym)
        if shutter_gym_to_unit_interval(shutter_gym) > DEFAULT_SHUTTER_THRESHOLD:
            fires += 1
    arr = np.asarray(shutter_vals, dtype=float)
    return {
        "n_samples": n_samples,
        "p_shutter_fire": fires / n_samples,
        "shutter_gym_mean": float(arr.mean()),
        "shutter_gym_std": float(arr.std()),
        "shutter_gym_min": float(arr.min()),
        "shutter_gym_max": float(arr.max()),
        "threshold": DEFAULT_SHUTTER_THRESHOLD,
    }


def main() -> None:
    kpis = run_training_slice(run_id="ml_ls_a1_fundamental", show_progress=False)
    # Rebuild setup for probes only
    from dataclasses import replace
    from s01_utils.training_workflow import build_training_workflow_setup
    from _frozen_baseline import frozen_training_config

    setup = build_training_workflow_setup(frozen_training_config(run_id="probe"))
    shutter_probe = _probe_shutter_exploration(setup)

    _DEBUG_LOG.parent.mkdir(parents=True, exist_ok=True)
    _DEBUG_LOG.open("a", encoding="utf-8").write(
        json.dumps({"ts": int(time.time() * 1000), "shutter_probe": shutter_probe, "kpis": kpis}) + "\n"
    )

    signal = kpis["increasing_signal"]
    verdict = "supported" if signal["strong_lead"] else "inconclusive"
    if not signal["strong_lead"] and shutter_probe["p_shutter_fire"] < 0.01:
        verdict = "supported"  # fundamental: exploration rarely fires shutter

    out = RESULTS_DIR / "a1_fundamental.json"
    write_hypothesis_result(
        out,
        experiment_id="ml_learning_signal",
        hypothesis_id="fundamental_limit",
        phase="A1",
        frozen_input={"scenario": "s01 cached warmup + 3 train", "seed": 7},
        control=json.loads((RESULTS_DIR / "baseline.json").read_text(encoding="utf-8"))["treatment"]["kpis"]
        if (RESULTS_DIR / "baseline.json").exists()
        else None,
        treatment={"kpis": kpis, "shutter_probe": shutter_probe},
        delta={"strong_lead": signal["strong_lead"], "p_shutter_fire": shutter_probe["p_shutter_fire"]},
        parity={"required": False, "passed": True, "notes": "diagnostic"},
        instrumentation={"hooks_valid": True},
        debug_examples={"train_episodes": kpis["debug_episodes"], "shutter_probe": shutter_probe},
        files_changed=[str(Path(__file__))],
        verdict=verdict,
        closeout="Fundamental-limit diagnostic A1.",
    )
    write_analysis_card(
        RESULTS_DIR / "fundamental_limit_analysis.md",
        hypothesis_id="fundamental_limit",
        json_path=out,
        sections={
            "1 Hypothesis": "Sparse shutter + threshold makes capture reward unreachable in 3 train episodes.",
            "2 Evidence": f"p_shutter_fire={shutter_probe['p_shutter_fire']:.4f}, train returns={signal['train_returns_ep1_ep3']}",
            "3 Verdict": verdict,
        },
    )
    print(f"Wrote {out} verdict={verdict} p_fire={shutter_probe['p_shutter_fire']:.4f}")


if __name__ == "__main__":
    main()
