"""Run one instrumented train episode after warmup (replay buffer primed)."""

from __future__ import annotations

import time
from typing import Any

import torch

from autonomous_control.episode_timing import EpisodeTimingCollector

from _fixtures import (
    build_profile_setup,
    get_applied_dt_profile,
    train_seed,
    warmup_seed,
)


def _learning_update_count(result: Any) -> int:
    stats = result.learning_stats or {}
    if hasattr(stats, "n_train_updates"):
        return int(stats.n_train_updates)
    if isinstance(stats, dict):
        return int(stats.get("n_train_updates", 0))
    return 0


def profile_train_episode(
    *,
    run_slug: str = "train_timing_profile",
    dt_label: str = "dt_1.5s",
    updates_per_step: int = 1,
    train_every_n_steps: int = 1,
    batch_size: int | None = None,
    rebuild_warmup_bundle_cache: bool = False,
    skip_warmup: bool = False,
) -> dict[str, Any]:
    """Warmup (optional) + one timed train episode. Returns JSON-serializable report."""
    setup = build_profile_setup(
        run_slug=run_slug,
        dt_label=dt_label,
        updates_per_step=updates_per_step,
        train_every_n_steps=train_every_n_steps,
        batch_size=batch_size,
        rebuild_warmup_bundle_cache=rebuild_warmup_bundle_cache,
    )

    warmup_wall_s = 0.0
    if not skip_warmup:
        t0 = time.perf_counter()
        setup.runner.run_serial(
            setup.agent,
            mode="warmup",
            episode_idx=0,
            collect_states=False,
            show_training_context=False,
            train_updates_per_step=0,
            feature_config=setup.feature_config,
            observation_layout=setup.observation_layout,
            np_rng=warmup_seed(0),
        )
        warmup_wall_s = time.perf_counter() - t0

    buffer_size = len(setup.agent.buffer) if hasattr(setup.agent, "buffer") else 0
    if buffer_size == 0:
        raise RuntimeError("Replay buffer empty after warmup; cannot profile train episode.")

    timing = EpisodeTimingCollector()
    result = setup.runner.run_serial(
        setup.agent,
        mode="train",
        episode_idx=0,
        collect_states=False,
        show_training_context=False,
        train_updates_per_step=int(updates_per_step),
        train_every_n_steps=int(train_every_n_steps),
        feature_config=setup.feature_config,
        observation_layout=setup.observation_layout,
        np_rng=train_seed(0),
        timing=timing,
    )

    dt_info = get_applied_dt_profile() or {}
    device = str(getattr(setup.agent, "device", "unknown"))
    cuda_available = bool(torch.cuda.is_available())
    if cuda_available:
        device_name = torch.cuda.get_device_name(0)
    else:
        device_name = "cpu"

    report = timing.report(
        extra={
            "run_slug": run_slug,
            "mode": "train",
            "dt_label": dt_label,
            "sim_dt_s": dt_info.get("sim_dt_s"),
            "controller_interval_s": dt_info.get("controller_interval_s"),
            "updates_per_step": int(updates_per_step),
            "train_every_n_steps": int(train_every_n_steps),
            "batch_size": int(setup.mpo_config.batch_size),
            "buffer_size_before_train": int(buffer_size),
            "warmup_wall_s": float(warmup_wall_s),
            "episode_return": float(result.episode_return),
            "n_train_updates_reported": _learning_update_count(result),
            "device": device,
            "cuda_available": cuda_available,
            "device_name": device_name,
            "num_samples_q": int(setup.mpo_config.num_samples_q),
            "num_samples_pi": int(setup.mpo_config.num_samples_pi),
        }
    )
    return report
