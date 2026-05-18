from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import numpy as np

@dataclass
class EpisodeArtifact:
    stage: str
    index: int
    total_reward: float
    average_reward: float
    steps: int
    video_path: Path | None = None

def _episode_metrics(result) -> tuple[float, float, int]:
    total = float(result.episode_return)
    steps = int(result.steps)
    avg = total / max(1, steps)
    return total, avg, steps


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    import csv

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

def _warmup_peak_index(episode_results: list) -> int:
    def _rank(ep_idx: int) -> float:
        total, _, _ = _episode_metrics(episode_results[ep_idx])
        t = float(total)
        return t if t == t else float("-inf")

    return max(range(len(episode_results)), key=_rank)

def _aggregate(rows: list[dict[str, object]]) -> dict[str, float]:
    totals = [float(r["total_reward"]) for r in rows]
    avgs = [float(r["average_reward"]) for r in rows]
    return {
        "episodes": float(len(rows)),
        "total_reward_mean": float(np.mean(totals)) if totals else 0.0,
        "total_reward_std": float(np.std(totals)) if totals else 0.0,
        "avg_reward_mean": float(np.mean(avgs)) if avgs else 0.0,
    }