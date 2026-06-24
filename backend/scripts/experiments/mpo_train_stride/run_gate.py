"""Experiment: train_every_n_steps throughput vs baseline."""

from __future__ import annotations

import json
import sys
import time
from dataclasses import replace
from pathlib import Path

import numpy as np

BACKEND_DIR = Path(__file__).resolve().parents[3]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from autonomous_control.episode_runner import EpisodeRunner  # noqa: E402
from autonomous_control.reward import RewardConfig  # noqa: E402
from simulation.setup_types import SimulationOverrides  # noqa: E402
from s01_utils import take_picture_verification as tpv  # noqa: E402

RESULTS_DIR = Path(__file__).resolve().parent / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


class _SlowTrainAgent:
    def __init__(self) -> None:
        self.train_calls = 0

    def get_action(self, obs, train: bool) -> np.ndarray:
        _ = obs, train
        return np.array([0.0, -1.0], dtype=np.float64)

    def store(self, transition) -> None:
        pass

    def train(self) -> None:
        self.train_calls += 1
        time.sleep(0.001)


def _run(*, stride: int) -> tuple[int, float]:
    reward = RewardConfig(enable_distance_reward=True, enable_image_quality_capture=False)
    setup = replace(
        tpv.build_take_picture_verification_setup(seed=0),
        simulation_overrides=SimulationOverrides(reward_config=reward),
    )
    agent = _SlowTrainAgent()
    runner = EpisodeRunner(setup)
    t0 = time.perf_counter()
    runner.run_serial(
        agent,
        mode="train",
        train_every_n_steps=stride,
        early_stop_on_budget_exhausted=False,
        verbose_print=1,
    )
    return agent.train_calls, time.perf_counter() - t0


def main() -> None:
    calls_1, wall_1 = _run(stride=1)
    calls_4, wall_4 = _run(stride=4)
    ratio = wall_1 / max(wall_4, 1e-6)
    payload = {
        "experiment_id": "mpo_train_stride",
        "train_calls_stride_1": calls_1,
        "train_calls_stride_4": calls_4,
        "wall_s_stride_1": wall_1,
        "wall_s_stride_4": wall_4,
        "speedup": ratio,
        "verdict": "pass" if ratio >= 1.5 and calls_4 < calls_1 else "fail",
    }
    out = RESULTS_DIR / "gate.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {out} speedup={ratio:.2f}x verdict={payload['verdict']}")


if __name__ == "__main__":
    main()
