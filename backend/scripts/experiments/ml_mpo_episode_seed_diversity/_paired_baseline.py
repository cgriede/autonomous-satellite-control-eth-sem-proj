"""Deterministic PD baseline score on a given EnvironmentSetup."""

from __future__ import annotations

from typing import Any

from _mission_score import compute_episode_mission_score
from s01_utils.baseline_overflight import run_baseline_overflight_rollout


def run_baseline_score_on_setup(
    setup,
    *,
    show_progress: bool = False,
) -> dict[str, Any]:
    rollout = run_baseline_overflight_rollout(
        setup,
        show_progress=show_progress,
        attitude_request_mode="torque",
    )
    score = float(compute_episode_mission_score(rollout.series, rollout.cmd_steps))
    return {
        "score_ep": score,
        "n_cmd_steps": len(rollout.cmd_steps),
    }


__all__ = ["run_baseline_score_on_setup"]
