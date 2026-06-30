"""Pre-flight smoke: CUDA, imports, mini rollout, train(), video encode."""

from __future__ import annotations

import sys
import time
import traceback
from dataclasses import replace
from pathlib import Path
from typing import Any

import _cpu_budget  # noqa: F401

import numpy as np
import torch

EXPERIMENT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = EXPERIMENT_ROOT.parents[2]
S01_DIR = BACKEND_DIR / "notebooks" / "s01"
for path in (BACKEND_DIR, S01_DIR, EXPERIMENT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from autonomous_control.config.randomness import derive_seed
from s01_utils import training_workflow as tw
from utils.ml_training.ml_training_utils import remove_run_dirs_for_slug
from utils.ml_training.training_run_artifacts import export_training_episode_video_sync

from _frozen_baseline import EXPERIMENT_SEED, frozen_training_config
from _reward_fork import activate_reward_fork
from _runner_common import RESULTS_DIR, append_overnight_log, write_hypothesis_result
from _sim_constants_fork import DT_CANDIDATES, apply_dt_profile
from _warmup_fingerprint_patch import activate_warmup_fingerprint_patch, set_warmup_fingerprint_extra

SMOKE_JSON = RESULTS_DIR / "smoke.json"
SMOKE_VIDEO = RESULTS_DIR / "smoke_test.mp4"
SMOKE_RUN_ID = "ml_overnight_smoke"


def phase_smoke(*, allow_cpu: bool = False) -> dict[str, Any]:
    """Validate GPU, imports, mini rollout, one train() step, and ffmpeg video."""
    t0 = time.perf_counter()
    timings: dict[str, float] = {}

    cuda_ok = torch.cuda.is_available()
    if not cuda_ok and not allow_cpu:
        payload = {
            "passed": False,
            "cuda_available": False,
            "error": "CUDA required; pass --allow-cpu for debug only.",
        }
        write_hypothesis_result(SMOKE_JSON, phase="smoke", **payload)
        append_overnight_log("SMOKE FAIL: no CUDA")
        raise RuntimeError(payload["error"])

    try:
        from autonomous_control.controller_agent import MPOAgent  # noqa: F401

        _ = MPOAgent
    except Exception as exc:
        write_hypothesis_result(
            SMOKE_JSON,
            phase="smoke",
            passed=False,
            import_error=str(exc),
            traceback=traceback.format_exc(),
        )
        raise

    ref = DT_CANDIDATES[0]
    apply_dt_profile(ref)
    set_warmup_fingerprint_extra(
        sim_dt_s=ref.sim_dt_s,
        controller_interval_s=ref.controller_interval_s,
        reward_mode="sparse",
    )
    activate_warmup_fingerprint_patch()
    activate_reward_fork("sparse")

    cfg = frozen_training_config(
        run_id=SMOKE_RUN_ID,
        train_episodes=0,
        rebuild_warmup_bundle_cache=False,
    )
    remove_run_dirs_for_slug(SMOKE_RUN_ID)
    cfg = replace(
        cfg,
        warmup_episodes=1,
        use_warmup_bundle_cache=False,
        eval_episodes=0,
        background_artifacts=False,
    )
    t_build = time.perf_counter()
    setup = tw.build_training_workflow_setup(cfg)
    timings["build_setup_s"] = time.perf_counter() - t_build

    t_warmup = time.perf_counter()
    warmup = setup.runner.run_serial(
        setup.agent,
        mode="warmup",
        episode_idx=0,
        collect_states=False,
        show_training_context=False,
        train_updates_per_step=0,
        feature_config=setup.feature_config,
        observation_layout=setup.observation_layout,
        np_rng=np.random.default_rng(derive_seed(EXPERIMENT_SEED, "smoke/warmup", 0)),
    )
    timings["warmup_s"] = time.perf_counter() - t_warmup
    buffer_size = len(setup.agent.buffer)
    if buffer_size == 0:
        raise RuntimeError(
            "Warmup produced an empty replay buffer; cannot run train() smoke step."
        )

    t_train = time.perf_counter()
    train_stats = setup.agent.train()
    timings["train_s"] = time.perf_counter() - t_train

    t_replay = time.perf_counter()
    replay = setup.runner.run_serial(
        setup.agent,
        mode="eval",
        episode_idx=0,
        collect_states=True,
        show_training_context=False,
        train_updates_per_step=0,
        feature_config=setup.feature_config,
        observation_layout=setup.observation_layout,
        np_rng=np.random.default_rng(derive_seed(EXPERIMENT_SEED, "smoke/video", 0)),
    )
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    export_training_episode_video_sync(replay.simulation_series, SMOKE_VIDEO)
    timings["video_s"] = time.perf_counter() - t_replay

    timings["total_s"] = time.perf_counter() - t0
    payload = {
        "passed": True,
        "cuda_available": cuda_ok,
        "device": str(getattr(setup.agent, "device", "unknown")),
        "warmup_return": float(warmup.episode_return),
        "warmup_steps": int(warmup.steps),
        "train_stats": train_stats,
        "buffer_size": len(setup.agent.buffer),
        "video_path": str(SMOKE_VIDEO),
        "timings": timings,
        "errors": [],
    }
    write_hypothesis_result(SMOKE_JSON, phase="smoke", **payload)
    append_overnight_log(f"SMOKE OK total_s={timings['total_s']:.1f}")
    return payload
