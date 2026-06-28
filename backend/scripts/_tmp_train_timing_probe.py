"""One-off timing probe: sim vs MPO train() for current S01 config."""
from __future__ import annotations

import sys
import time
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
S01 = BACKEND / "notebooks" / "s01"
EXPERIMENT = BACKEND / "scripts" / "experiments" / "ml_learning_signal"
for path in (BACKEND, S01, EXPERIMENT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import _cpu_budget  # noqa: F401

from autonomous_control.notebook_warmup_bundle_cache import preload_warmup_buffer_from_episodes  # noqa: E402
from s01_utils import training_workflow as tw  # noqa: E402
from _frozen_baseline import frozen_training_config  # noqa: E402


def main() -> None:
    cfg = frozen_training_config(run_id=None)
    setup = tw.build_training_workflow_setup(cfg)
    agent = setup.agent
    runner = setup.runner
    env = tw._warmup_cache_env_adapter(setup)
    resolved = setup.mission_setup.resolve(require_camera=True)

    warmup_eps, from_cache = tw.load_or_build_s01_training_warmup_episodes(setup, show_progress=False)
    if not from_cache:
        preload_warmup_buffer_from_episodes(agent, warmup_eps)
    print(f"device={agent.device} buffer={len(agent.buffer)} clouds={len(resolved.clouds or ())}")

    n = 50
    t0 = time.perf_counter()
    for _ in range(n):
        agent.train()
    train_s = time.perf_counter() - t0
    ms_per_update = train_s / n * 1000.0
    print(f"train() x{n}: {train_s:.3f}s -> {ms_per_update:.2f} ms/update")

    t0 = time.perf_counter()
    res = runner.run_serial(
        agent,
        mode="train",
        train_updates_per_step=1,
        train_every_n_steps=1,
        feature_config=cfg.feature_config,
        episode_idx=0,
        collect_states=False,
    )
    ep_s = time.perf_counter() - t0
    steps = res.steps
    n_updates = res.learning_stats["n_train_updates"] if res.learning_stats else None
    ms_per_step_wall = ep_s / steps * 1000.0
    sim_ref_ms = 2.78  # high_cloud sim_timing coast profile (today)
    sim_only_s = steps * sim_ref_ms / 1000.0
    train_only_est_s = steps * ms_per_update / 1000.0
    print(f"1 train episode: {ep_s:.2f}s steps={steps} n_updates={n_updates}")
    print(f"  wall ms/step: {ms_per_step_wall:.2f}")
    print(f"  est sim-only @ {sim_ref_ms} ms/step: {sim_only_s:.2f}s ({sim_only_s/ep_s*100:.1f}%)")
    print(f"  est train-only @ {ms_per_update:.2f} ms/update: {train_only_est_s:.2f}s ({train_only_est_s/ep_s*100:.1f}%)")
    print(f"  est sum (sim+train sequential): {sim_only_s + train_only_est_s:.2f}s")


if __name__ == "__main__":
    main()
