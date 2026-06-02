"""Aggregate perf_counter samples into binned simulation timing categories."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Per-step buckets (summed across all simulation steps unless noted).
CATEGORY_LABELS: dict[str, str] = {
    "controller_actuator": "Controller / policy (actuator command)",
    "robotics_dynamics": "Reaction wheel & attitude dynamics",
    "orbit_kinematics": "Orbit position lookup (precomputed ephemeris)",
    "environment_clouds": "Environment: cloud arc / meteo encoding",
    "sensor_camera_rays": "Visual: camera ray kernel",
    "geodesy": "Geodesy transforms (disk to geodetic)",
    "footprint_target": "Target footprint overlap & novelty",
    "reward_ml": "Reward / ML-side scoring",
    "stepper_bookkeeping": "Stepper bookkeeping (residual per step)",
    "render": "Render setup & frame draw",
    "export_video": "Video export / encode",
}

EPISODE_LEVEL_CATEGORIES = frozenset({"render", "export_video"})
PER_STEP_CATEGORIES = frozenset(CATEGORY_LABELS) - EPISODE_LEVEL_CATEGORIES


@dataclass
class TimingCollector:
    """Accumulates wall time per category."""

    totals_s: dict[str, float] = field(default_factory=dict)
    step_count: int = 0
    sim_loop_wall_s: float = 0.0

    def reset(self) -> None:
        self.totals_s.clear()
        self.step_count = 0
        self.sim_loop_wall_s = 0.0

    def snapshot(self) -> dict[str, float]:
        return dict(self.totals_s)

    def add(self, category: str, elapsed_s: float) -> None:
        if elapsed_s <= 0.0:
            return
        self.totals_s[category] = self.totals_s.get(category, 0.0) + float(elapsed_s)

    def delta_since(self, before: dict[str, float]) -> dict[str, float]:
        after = self.totals_s
        keys = set(before) | set(after)
        return {k: after.get(k, 0.0) - before.get(k, 0.0) for k in keys}

    def begin_step(self) -> None:
        self.step_count += 1

    def report(
        self,
        *,
        top_n: int = 7,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build JSON-serializable timing report with top-N consumers."""
        n_steps = max(1, self.step_count)
        sim_wall = max(self.sim_loop_wall_s, 1e-12)

        per_step_sum = sum(self.totals_s.get(c, 0.0) for c in PER_STEP_CATEGORIES)
        episode_sum = sum(self.totals_s.get(c, 0.0) for c in EPISODE_LEVEL_CATEGORIES)
        measured_total = per_step_sum + episode_sum

        categories: list[dict[str, Any]] = []
        for key, label in CATEGORY_LABELS.items():
            total_s = float(self.totals_s.get(key, 0.0))
            if key in EPISODE_LEVEL_CATEGORIES:
                per_step_s = None
            else:
                per_step_s = total_s / n_steps
            categories.append(
                {
                    "key": key,
                    "label": label,
                    "total_s": total_s,
                    "per_step_ms": None if per_step_s is None else 1000.0 * per_step_s,
                    "pct_of_sim_loop": 100.0 * total_s / sim_wall if sim_wall > 0 else 0.0,
                }
            )

        categories.sort(key=lambda row: row["total_s"], reverse=True)
        top = categories[:top_n]

        unaccounted_s = max(0.0, sim_wall - per_step_sum)

        payload: dict[str, Any] = {
            "sim_loop_wall_s": sim_wall,
            "n_steps": n_steps,
            "steps_per_s": n_steps / sim_wall if sim_wall > 0 else 0.0,
            "per_step_wall_ms": 1000.0 * sim_wall / n_steps,
            "measured_in_loop_s": per_step_sum,
            "measured_episode_extra_s": episode_sum,
            "measured_grand_total_s": measured_total,
            "unaccounted_in_loop_s": unaccounted_s,
            "categories": categories,
            f"top_{top_n}_consumers": top,
        }
        if extra:
            payload["context"] = extra
        return payload
