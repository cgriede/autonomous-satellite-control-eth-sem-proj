"""Warmup baseline quality gates — replay buffer is only as good as the pilot."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from simulation.capture_reward import applied_capture_reward_series, latent_capture_reward_series
from simulation.take_picture import resolve_capture_frame_index

from _episode_loop_fork import Exp14EpisodeResult
from _mission_score import compute_episode_mission_score


@dataclass(frozen=True)
class WarmupBaselineGate:
    """Minimum bar for scripted overflight warmup before MPO trains on its buffer."""

    mission_score_min: float = 1.0
    capture_count_min: int = 4
    mean_peak_efficiency_min: float = 0.75
    """Mean applied/latent at shutter capture frames (1.0 = on-peak timing)."""


DEFAULT_WARMUP_GATE = WarmupBaselineGate()


def assess_warmup_baseline_episode(
    result: Exp14EpisodeResult,
    *,
    gate: WarmupBaselineGate = DEFAULT_WARMUP_GATE,
) -> dict[str, Any]:
    series = result.simulation_series
    cmd_steps = tuple(int(s) for s in result.cmd_steps)
    n = int(series.t_s.shape[0])
    latent = latent_capture_reward_series(series)
    applied = applied_capture_reward_series(series, cmd_steps=cmd_steps)

    peak_ratios: list[float] = []
    for cmd_step in cmd_steps:
        capture_k = resolve_capture_frame_index(
            cmd_step=int(cmd_step),
            n_steps=n,
            capture_latency_steps=0,
        )
        if capture_k is None:
            continue
        lat = float(latent[int(capture_k)])
        app = float(applied[int(capture_k)])
        if lat > 1e-6 and app > 0.0:
            peak_ratios.append(app / lat)

    latent_sum = float(np.sum(latent))
    applied_sum = float(np.sum(applied))
    harvest_ratio = applied_sum / latent_sum if latent_sum > 1e-9 else 0.0
    mission_score = float(result.mission_score)
    mean_peak_efficiency = float(np.mean(peak_ratios)) if peak_ratios else 0.0

    passed = (
        mission_score >= gate.mission_score_min
        and len(cmd_steps) >= gate.capture_count_min
        and mean_peak_efficiency >= gate.mean_peak_efficiency_min
    )

    return {
        "passed": passed,
        "mission_score": mission_score,
        "episode_return": float(result.episode_return),
        "n_shutter_cmds": len(cmd_steps),
        "n_rewarded_captures": len(peak_ratios),
        "mean_peak_efficiency": mean_peak_efficiency,
        "reward_harvest_ratio": harvest_ratio,
        "gate": {
            "mission_score_min": gate.mission_score_min,
            "capture_count_min": gate.capture_count_min,
            "mean_peak_efficiency_min": gate.mean_peak_efficiency_min,
        },
    }


def assess_warmup_baseline_quality(
    results: list[Exp14EpisodeResult],
    *,
    gate: WarmupBaselineGate = DEFAULT_WARMUP_GATE,
) -> dict[str, Any]:
    if not results:
        return {
            "passed": False,
            "reason": "no warmup episodes",
            "episodes": [],
        }

    episodes = [assess_warmup_baseline_episode(r, gate=gate) for r in results]
    scores = [float(e["mission_score"]) for e in episodes]
    efficiencies = [float(e["mean_peak_efficiency"]) for e in episodes]
    captures = [int(e["n_shutter_cmds"]) for e in episodes]

    passed = all(bool(e["passed"]) for e in episodes)
    return {
        "passed": passed,
        "episode_count": len(episodes),
        "mission_score_mean": float(np.mean(scores)),
        "mission_score_min": float(np.min(scores)),
        "mean_peak_efficiency_mean": float(np.mean(efficiencies)),
        "capture_count_mean": float(np.mean(captures)),
        "episodes": episodes,
        "gate": episodes[0]["gate"] if episodes else {},
    }


def require_warmup_baseline_quality(
    results: list[Exp14EpisodeResult],
    *,
    gate: WarmupBaselineGate = DEFAULT_WARMUP_GATE,
    context: str = "warmup",
) -> dict[str, Any]:
    report = assess_warmup_baseline_quality(results, gate=gate)
    if report["passed"]:
        return report
    failed_eps = [i for i, e in enumerate(report.get("episodes", [])) if not e.get("passed")]
    raise RuntimeError(
        f"Warmup baseline quality gate failed ({context}): "
        f"failed_episodes={failed_eps} "
        f"mission_score_min={report.get('mission_score_min')} "
        f"mean_peak_efficiency_mean={report.get('mean_peak_efficiency_mean'):.3f} "
        f"capture_count_mean={report.get('capture_count_mean'):.1f} "
        f"— fix baseline / env / reward fork before training on this buffer."
    )


__all__ = [
    "DEFAULT_WARMUP_GATE",
    "WarmupBaselineGate",
    "assess_warmup_baseline_episode",
    "assess_warmup_baseline_quality",
    "require_warmup_baseline_quality",
]
