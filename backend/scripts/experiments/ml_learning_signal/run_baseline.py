"""Shared production baseline: cached warmup + 3 train episodes (current MPO config)."""

from __future__ import annotations

import sys
from pathlib import Path

EXPERIMENT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = EXPERIMENT_ROOT.parents[2]
S01_DIR = BACKEND_DIR / "notebooks" / "s01"
for path in (BACKEND_DIR, S01_DIR, EXPERIMENT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from _frozen_baseline import EXPERIMENT_SEED, TRAIN_EPISODES, WARMUP_EPISODES  # noqa: E402
from _runner_common import (  # noqa: E402
    RESULTS_DIR,
    run_training_slice,
    write_hypothesis_result,
)

RESULTS_PATH = RESULTS_DIR / "baseline.json"


def main() -> None:
    kpis = run_training_slice(run_id="ml_learning_signal_baseline", show_progress=False)
    signal = kpis["increasing_signal"]
    verdict = "supported" if signal["strong_lead"] else "inconclusive"
    write_hypothesis_result(
        RESULTS_PATH,
        experiment_id="ml_learning_signal",
        hypothesis_id="shared_baseline",
        phase="baseline",
        frozen_input={
            "description": "Production MPO + S01 features; cached baseline warmup",
            "scenario": "s01 notebook-08 training",
            "seed": EXPERIMENT_SEED,
            "tunables": {
                "warmup_episodes": WARMUP_EPISODES,
                "train_episodes": TRAIN_EPISODES,
                "use_warmup_bundle_cache": True,
            },
            "n_items": None,
        },
        control=None,
        treatment={"kpis": kpis},
        delta={
            "primary_kpi": "train_returns_ep1_ep3",
            "baseline_value": None,
            "treatment_value": signal["train_returns_ep1_ep3"],
            "direction": "up" if signal["strong_lead"] else "flat",
            "strong_lead": signal["strong_lead"],
        },
        parity={"required": True, "passed": True, "notes": "production reference path"},
        instrumentation={"hooks_valid": True, "notes": "episode_runner + training_workflow"},
        debug_examples={"train_episodes": kpis["debug_episodes"]},
        files_changed=[],
        verdict=verdict,
        closeout="Shared baseline for ML learning-signal branches.",
    )
    print(f"Wrote {RESULTS_PATH}")
    print(f"  train returns ep1-3: {signal['train_returns_ep1_ep3']}")
    print(f"  strong_lead: {signal['strong_lead']}  verdict={verdict}")


if __name__ == "__main__":
    main()
