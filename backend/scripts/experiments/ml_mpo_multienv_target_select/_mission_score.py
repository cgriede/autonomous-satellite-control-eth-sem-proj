"""Mission score KPI (quality × coverage) decoupled from RL return."""

from __future__ import annotations

import numpy as np

from simulation.capture_reward import applied_capture_reward_series
from simulation.state_types import SimulationStateSeries


def compute_episode_mission_score(
    series: SimulationStateSeries,
    cmd_steps: tuple[int, ...],
) -> float:
    """Sum quality × coverage on budget-eligible applied captures (k_capture=1)."""
    arr = applied_capture_reward_series(series, cmd_steps=cmd_steps, k_capture=1.0)
    return float(np.sum(arr))


def aggregate_eval_scores(scores: list[float]) -> dict[str, object]:
    if not scores:
        return {
            "score_mean": 0.0,
            "score_std": 0.0,
            "score_min": 0.0,
            "score_max": 0.0,
            "score_ep": [],
        }
    arr = np.asarray(scores, dtype=float)
    return {
        "score_mean": float(np.mean(arr)),
        "score_std": float(np.std(arr)),
        "score_min": float(np.min(arr)),
        "score_max": float(np.max(arr)),
        "score_ep": [float(x) for x in arr],
    }


__all__ = ["aggregate_eval_scores", "compute_episode_mission_score"]
