"""Experiment: train/warmup early stop when capture budget exhausted."""

from __future__ import annotations

import json
import sys
import time
from dataclasses import replace
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[3]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from autonomous_control.episode_runner import EpisodeRunner  # noqa: E402
from autonomous_control.reward import RewardConfig  # noqa: E402
from simulation.setup_types import SimulationOverrides  # noqa: E402
from s01_utils import take_picture_verification as tpv  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parent / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


class _ShutterAgent:
    def get_action(self, obs, train: bool) -> list[float]:
        _ = obs, train
        return [0.0, 1.0]

    def store(self, transition) -> None:
        pass

    def train(self) -> None:
        pass


def _run(mode: str, *, early_stop: bool) -> tuple[int, float]:
    reward = RewardConfig(enable_distance_reward=True, enable_image_quality_capture=True)
    setup = replace(
        tpv.build_take_picture_verification_setup(seed=0),
        simulation_overrides=SimulationOverrides(reward_config=reward),
    )
    runner = EpisodeRunner(setup)
    t0 = time.perf_counter()
    result = runner.run_serial(
        _ShutterAgent(),
        mode=mode,
        early_stop_on_budget_exhausted=early_stop,
        verbose_print=1,
    )
    return int(result.steps), time.perf_counter() - t0


def main() -> None:
    eval_steps, eval_wall = _run("eval", early_stop=False)
    train_steps, train_wall = _run("train", early_stop=True)
    speed_ratio = eval_wall / max(train_wall, 1e-6)
    payload = {
        "experiment_id": "episode_budget_early_stop",
        "eval_steps": eval_steps,
        "train_steps": train_steps,
        "eval_wall_s": eval_wall,
        "train_wall_s": train_wall,
        "speed_ratio_eval_over_train": speed_ratio,
        "verdict": "pass" if train_steps < eval_steps else "fail",
    }
    out = RESULTS_DIR / "gate.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {out} verdict={payload['verdict']}")
    if payload["verdict"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
