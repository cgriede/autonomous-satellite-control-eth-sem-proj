"""Wall-time buckets for serial episode rollouts (train / warmup / eval)."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any

CATEGORY_LABELS: dict[str, str] = {
    "sim_step": "Simulation step (integrate + shutter capture)",
    "obs_build": "Controller observation build",
    "state_copy": "Per-step state copy (collect_states)",
    "get_action": "Policy inference (get_action)",
    "controller_baseline": "Warmup baseline controller tick",
    "store": "Replay buffer store",
    "train": "Learner update (train)",
    "progress": "Progress display / live feed",
}


@dataclass
class EpisodeTimingCollector:
    """Accumulates perf_counter samples for one episode rollout."""

    totals_s: dict[str, float] = field(default_factory=dict)
    wall_t0: float = 0.0
    n_sim_steps: int = 0
    n_controller_stores: int = 0
    n_train_updates: int = 0

    def begin_episode(self) -> None:
        self.totals_s = {key: 0.0 for key in CATEGORY_LABELS}
        self.wall_t0 = time.perf_counter()
        self.n_sim_steps = 0
        self.n_controller_stores = 0
        self.n_train_updates = 0

    def add(self, category: str, elapsed_s: float) -> None:
        if elapsed_s <= 0.0:
            return
        if category not in CATEGORY_LABELS:
            raise KeyError(f"Unknown timing category: {category!r}")
        self.totals_s[category] = self.totals_s.get(category, 0.0) + float(elapsed_s)

    def note_sim_step(self) -> None:
        self.n_sim_steps += 1

    def note_controller_store(self) -> None:
        self.n_controller_stores += 1

    def note_train_update(self) -> None:
        self.n_train_updates += 1

    def report(
        self,
        *,
        top_n: int = 7,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        wall_s = max(time.perf_counter() - self.wall_t0, 1e-12)
        n_steps = max(1, self.n_sim_steps)
        measured_s = sum(self.totals_s.values())
        unaccounted_s = max(0.0, wall_s - measured_s)

        categories: list[dict[str, Any]] = []
        for key, label in CATEGORY_LABELS.items():
            total_s = float(self.totals_s.get(key, 0.0))
            categories.append(
                {
                    "key": key,
                    "label": label,
                    "total_s": total_s,
                    "per_step_ms": 1000.0 * total_s / n_steps,
                    "pct_of_wall": 100.0 * total_s / wall_s,
                }
            )
        categories.sort(key=lambda row: row["total_s"], reverse=True)
        top = categories[:top_n]

        payload: dict[str, Any] = {
            "episode_wall_s": wall_s,
            "n_sim_steps": self.n_sim_steps,
            "n_controller_stores": self.n_controller_stores,
            "n_train_updates": self.n_train_updates,
            "steps_per_s": self.n_sim_steps / wall_s,
            "per_step_wall_ms": 1000.0 * wall_s / n_steps,
            "measured_s": measured_s,
            "unaccounted_s": unaccounted_s,
            "categories": categories,
            f"top_{top_n}_consumers": top,
            "thread_env": {
                k: os.environ.get(k)
                for k in (
                    "OMP_NUM_THREADS",
                    "MKL_NUM_THREADS",
                    "OPENBLAS_NUM_THREADS",
                    "ASC_CPU_THREADS",
                )
            },
        }
        if extra:
            payload["context"] = extra
        return payload
