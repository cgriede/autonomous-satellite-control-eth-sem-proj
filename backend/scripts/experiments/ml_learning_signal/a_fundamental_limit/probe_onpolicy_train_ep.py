"""One train episode diagnostic: on-policy shutter cmds vs positive rewards."""

from __future__ import annotations

import json
import sys
import time
from dataclasses import asdict, is_dataclass
from pathlib import Path

EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = EXPERIMENT_ROOT.parents[2]
S01_DIR = BACKEND_DIR / "notebooks" / "s01"
for path in (BACKEND_DIR, S01_DIR, EXPERIMENT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import _cpu_budget  # noqa: F401

import numpy as np

from autonomous_control.notebook_warmup_bundle_cache import preload_warmup_buffer_from_episodes  # noqa: E402
from s01_utils.training_workflow import build_training_workflow_setup, load_or_build_s01_training_warmup_episodes  # noqa: E402
from _frozen_baseline import frozen_training_config  # noqa: E402

_DEBUG_LOG = EXPERIMENT_ROOT / "results" / "ml_learning_signal_fundamental.ndjson"


def main() -> None:
    cfg = frozen_training_config(run_id=f"onpolicy_probe_{int(time.time())}")
    setup = build_training_workflow_setup(cfg)
    agent = setup.agent
    warmup_eps, from_cache = load_or_build_s01_training_warmup_episodes(setup, show_progress=False)
    if not from_cache or len(agent.buffer) == 0:
        preload_warmup_buffer_from_episodes(agent, warmup_eps)

    result = setup.runner.run_serial(
        agent,
        mode="train",
        episode_idx=0,
        collect_states=False,
        train_updates_per_step=1,
        train_every_n_steps=1,
        feature_config=setup.feature_config,
        observation_layout=setup.observation_layout,
        np_rng=np.random.default_rng(setup.config.seed),
    )
    series = result.simulation_series
    meta = series.metadata
    shutter_steps = list(getattr(meta, "take_picture_cmd_steps", ()) or ())
    rewards = np.asarray(series.simulation_reward[1 : result.steps + 1], dtype=float)
    positive_idx = np.where(rewards > 0.0)[0]

    kl = result.learning_stats
    kl_serial = asdict(kl) if kl is not None and is_dataclass(kl) else {}
    payload = {
        "ts": int(time.time() * 1000),
        "episode_return": float(result.episode_return),
        "steps": int(result.steps),
        "n_shutter_cmds": len(shutter_steps),
        "shutter_cmd_rate": len(shutter_steps) / max(1, result.steps),
        "positive_reward_steps": int(positive_idx.size),
        "max_step_reward": float(np.max(rewards)) if rewards.size else 0.0,
        "warmup_shutter_cmds_ep0": len(
            getattr(warmup_eps[0].simulation_series.metadata, "take_picture_cmd_steps", ()) or ()
        ),
        "learning_stats": kl_serial,
        "buffer_size_after": len(agent.buffer),
    }
    _DEBUG_LOG.parent.mkdir(parents=True, exist_ok=True)
    _DEBUG_LOG.open("a", encoding="utf-8").write(json.dumps(payload) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
