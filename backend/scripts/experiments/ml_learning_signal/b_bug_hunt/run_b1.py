"""Branch B run 1: test lower shutter threshold fork (experiment-only)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = EXPERIMENT_ROOT.parents[2]
S01_DIR = BACKEND_DIR / "notebooks" / "s01"
for path in (BACKEND_DIR, S01_DIR, EXPERIMENT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import autonomous_control.action_adapter as action_adapter  # noqa: E402
import autonomous_control.episode_runner as episode_runner  # noqa: E402

from _runner_common import RESULTS_DIR, run_training_slice, write_analysis_card, write_hypothesis_result  # noqa: E402

# Experiment fork: lower shutter threshold so exploratory samples fire more often.
_FORK_THRESHOLD = 0.35
_orig_threshold = action_adapter.DEFAULT_SHUTTER_THRESHOLD
_orig_policy_output = episode_runner.policy_output_to_gym_action


def _patched_policy_output(raw, *, tau_limit=None, active_threshold=_FORK_THRESHOLD):
    return _orig_policy_output(raw, tau_limit=tau_limit, active_threshold=active_threshold)


def main() -> None:
    action_adapter.DEFAULT_SHUTTER_THRESHOLD = _FORK_THRESHOLD
    episode_runner.policy_output_to_gym_action = _patched_policy_output
    try:
        kpis = run_training_slice(run_id="ml_ls_b1_lower_threshold", show_progress=False)
    finally:
        action_adapter.DEFAULT_SHUTTER_THRESHOLD = _orig_threshold
        episode_runner.policy_output_to_gym_action = _orig_policy_output

    signal = kpis["increasing_signal"]
    verdict = "supported" if signal["strong_lead"] else "inconclusive"
    out = RESULTS_DIR / "b1_lower_threshold.json"
    write_hypothesis_result(
        out,
        experiment_id="ml_learning_signal",
        hypothesis_id="bug_hunt_lower_threshold",
        phase="B1",
        frozen_input={"fork": f"DEFAULT_SHUTTER_THRESHOLD={_FORK_THRESHOLD}"},
        control=None,
        treatment={"kpis": kpis},
        delta={"strong_lead": signal["strong_lead"]},
        parity={"required": True, "passed": False, "notes": "threshold fork — not production parity"},
        instrumentation={"hooks_valid": True},
        debug_examples={"train_episodes": kpis["debug_episodes"]},
        files_changed=[str(Path(__file__))],
        verdict=verdict,
        closeout="Bug-hunt: lower shutter threshold fork.",
    )
    write_analysis_card(
        RESULTS_DIR / "bug_hunt_analysis.md",
        hypothesis_id="bug_hunt_lower_threshold",
        json_path=out,
        sections={
            "1 Intervention": f"Shutter threshold {_orig_threshold} → {_FORK_THRESHOLD}",
            "2 Train returns": str(signal["train_returns_ep1_ep3"]),
            "3 Verdict": verdict,
        },
    )
    print(f"Wrote {out} returns={signal['train_returns_ep1_ep3']} strong_lead={signal['strong_lead']}")


if __name__ == "__main__":
    main()
