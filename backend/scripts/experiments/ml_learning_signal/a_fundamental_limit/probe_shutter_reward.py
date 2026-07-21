"""Fast diagnostic: shutter fire probability + warmup buffer reward stats (no full train run)."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import _cpu_budget  # noqa: F401

import numpy as np

EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = EXPERIMENT_ROOT.parents[2]
S01_DIR = BACKEND_DIR / "notebooks" / "s01"
for path in (BACKEND_DIR, S01_DIR, EXPERIMENT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from autonomous_control.action_adapter import DEFAULT_SHUTTER_THRESHOLD, shutter_gym_to_unit_interval  # noqa: E402
from autonomous_control.notebook_warmup_bundle_cache import preload_warmup_buffer_from_episodes  # noqa: E402
from s01_utils.training_workflow import build_training_workflow_setup, load_or_build_s01_training_warmup_episodes  # noqa: E402
from _frozen_baseline import frozen_training_config  # noqa: E402

_DEBUG_LOG = EXPERIMENT_ROOT / "results" / "ml_learning_signal_fundamental.ndjson"


def _p_fire(agent, obs, *, n: int = 5000) -> dict:
    fires = 0
    vals = []
    for _ in range(n):
        raw = agent.get_action(obs, train=True)
        sg = float(raw[1]) if raw.shape[0] >= 2 else -1.0
        vals.append(sg)
        if shutter_gym_to_unit_interval(sg) > DEFAULT_SHUTTER_THRESHOLD:
            fires += 1
    arr = np.asarray(vals, dtype=float)
    unit = 0.5 * (np.clip(arr, -1.0, 1.0) + 1.0)
    return {
        "n_samples": n,
        "p_shutter_fire": fires / n,
        "shutter_gym_mean": float(arr.mean()),
        "shutter_gym_std": float(arr.std()),
        "shutter_unit_mean": float(unit.mean()),
        "shutter_unit_std": float(unit.std()),
        "frac_unit_above_threshold": float(np.mean(unit > DEFAULT_SHUTTER_THRESHOLD)),
        "threshold": DEFAULT_SHUTTER_THRESHOLD,
    }


def _buffer_reward_stats(agent) -> dict:
    buf = agent.buffer
    n = len(buf)
    if n == 0:
        return {"buffer_size": 0}
    rewards = np.asarray(buf.rewards[:n], dtype=float)
    pos = rewards > 0.0
    actions = np.asarray(buf.actions[:n], dtype=float)
    shutter_fires_in_buf = 0
    if actions.shape[1] >= 2:
        unit = 0.5 * (np.clip(actions[:, 1], -1.0, 1.0) + 1.0)
        shutter_fires_in_buf = int(np.sum(unit > DEFAULT_SHUTTER_THRESHOLD))
    return {
        "buffer_size": n,
        "positive_reward_transitions": int(np.sum(pos)),
        "positive_reward_fraction": float(np.mean(pos)),
        "max_reward": float(np.max(rewards)),
        "mean_reward": float(np.mean(rewards)),
        "buffer_shutter_fire_actions": shutter_fires_in_buf,
        "buffer_shutter_fire_fraction": shutter_fires_in_buf / n if n else 0.0,
    }


def main() -> None:
    import time
    cfg = frozen_training_config(run_id=f"probe_only_{int(time.time())}")
    setup = build_training_workflow_setup(cfg)
    agent = setup.agent
    warmup_eps, from_cache = load_or_build_s01_training_warmup_episodes(setup, show_progress=False)
    obs = warmup_eps[0].states[0]

    pre = _p_fire(agent, obs)
    if not from_cache or len(agent.buffer) == 0:
        preload_warmup_buffer_from_episodes(agent, warmup_eps)
    post = _p_fire(agent, obs)
    buf_stats = _buffer_reward_stats(agent)

    warmup_returns = [float(ep.episode_return) for ep in warmup_eps]
    warmup_shutter_cmds = [
        len(getattr(ep.simulation_series.metadata, "take_picture_cmd_steps", ()) or ())
        for ep in warmup_eps
    ]

    payload = {
        "ts": int(time.time() * 1000),
        "warmup_from_cache": from_cache,
        "warmup_returns": warmup_returns,
        "warmup_shutter_cmds_per_ep": warmup_shutter_cmds,
        "p_fire_pre_buffer": pre,
        "p_fire_post_buffer": post,
        "buffer_stats": buf_stats,
    }
    _DEBUG_LOG.parent.mkdir(parents=True, exist_ok=True)
    _DEBUG_LOG.open("a", encoding="utf-8").write(json.dumps(payload) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
