"""Episode-level aggregation of MPO train() metrics from agent.metrics lists."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from simulation.simulation_info import exploration_status_for_rollout

_METRIC_KEYS: tuple[str, ...] = (
    "qloss",
    "piloss",
    "kl",
    "kl_mu",
    "kl_sigma",
    "eta",
    "etaloss",
)


@dataclass(frozen=True)
class MetricsSliceStart:
    """Lengths of agent.metrics lists recorded before an episode."""

    lengths: dict[str, int]


@dataclass(frozen=True)
class EpisodeLearningStats:
    phase: str
    episode_idx: int
    episode_return: float
    steps: int
    n_train_updates: int
    q_loss_mean: float
    pi_loss_mean: float
    kl_mean: float
    kl_mu_mean: float
    kl_sigma_mean: float
    eta_mean: float
    buffer_size: int
    in_exploration: bool


def snapshot_metrics_start(agent: Any) -> MetricsSliceStart | None:
    metrics = getattr(agent, "metrics", None)
    if not isinstance(metrics, dict):
        return None
    return MetricsSliceStart(
        lengths={key: len(metrics[key]) for key in _METRIC_KEYS if key in metrics}
    )


def _mean_slice(values: list[float], start: int) -> float:
    if len(values) <= start:
        return float("nan")
    chunk = values[start:]
    if not chunk:
        return float("nan")
    return float(np.mean(np.asarray(chunk, dtype=np.float64)))


def collect_episode_learning_stats(
    agent: Any,
    *,
    phase: str,
    episode_idx: int,
    episode_return: float,
    steps: int,
    mode: str,
    metrics_start: MetricsSliceStart | None,
) -> EpisodeLearningStats | None:
    if mode != "train" or metrics_start is None:
        return None
    metrics = getattr(agent, "metrics", None)
    if not isinstance(metrics, dict):
        return None

    starts = metrics_start.lengths
    n_q = len(metrics.get("qloss", [])) - starts.get("qloss", 0)
    n_pi = len(metrics.get("piloss", [])) - starts.get("piloss", 0)
    n_train_updates = max(n_q, n_pi, 0)

    buffer = getattr(agent, "buffer", None)
    buffer_size = int(len(buffer)) if buffer is not None else 0
    _, in_exploration = exploration_status_for_rollout(mode=mode)

    return EpisodeLearningStats(
        phase=phase,
        episode_idx=int(episode_idx),
        episode_return=float(episode_return),
        steps=int(steps),
        n_train_updates=int(n_train_updates),
        q_loss_mean=_mean_slice(metrics.get("qloss", []), starts.get("qloss", 0)),
        pi_loss_mean=_mean_slice(metrics.get("piloss", []), starts.get("piloss", 0)),
        kl_mean=_mean_slice(metrics.get("kl", []), starts.get("kl", 0)),
        kl_mu_mean=_mean_slice(metrics.get("kl_mu", []), starts.get("kl_mu", 0)),
        kl_sigma_mean=_mean_slice(metrics.get("kl_sigma", []), starts.get("kl_sigma", 0)),
        eta_mean=_mean_slice(metrics.get("eta", []), starts.get("eta", 0)),
        buffer_size=buffer_size,
        in_exploration=in_exploration,
    )


def learning_stats_to_row(stats: EpisodeLearningStats | None) -> dict[str, float | int | str | bool]:
    if stats is None:
        return {
            "n_train_updates": 0,
            "q_loss_mean": float("nan"),
            "pi_loss_mean": float("nan"),
            "kl_mean": float("nan"),
            "kl_mu_mean": float("nan"),
            "kl_sigma_mean": float("nan"),
            "eta_mean": float("nan"),
            "buffer_size": 0,
            "in_exploration": False,
        }
    return {
        "n_train_updates": stats.n_train_updates,
        "q_loss_mean": stats.q_loss_mean,
        "pi_loss_mean": stats.pi_loss_mean,
        "kl_mean": stats.kl_mean,
        "kl_mu_mean": stats.kl_mu_mean,
        "kl_sigma_mean": stats.kl_sigma_mean,
        "eta_mean": stats.eta_mean,
        "buffer_size": stats.buffer_size,
        "in_exploration": stats.in_exploration,
    }
