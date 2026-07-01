"""Run Exp 9 shutter reward split arms — SAC sparse vector."""

from __future__ import annotations

import importlib.util
import json
import sys
import time
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import _cpu_budget  # noqa: F401

EXPERIMENT_ROOT = Path(__file__).resolve().parent
OVERNIGHT_ROOT = EXPERIMENT_ROOT.parent / "ml_algo_overnight"
BACKEND_DIR = EXPERIMENT_ROOT.parents[2]
S01_DIR = BACKEND_DIR / "notebooks" / "s01"
_PATH_ROOTS = (BACKEND_DIR, S01_DIR, OVERNIGHT_ROOT, EXPERIMENT_ROOT)
for path in reversed(_PATH_ROOTS):
    p = str(path)
    if p in sys.path:
        sys.path.remove(p)
    sys.path.insert(0, p)

from s01_utils import training_workflow as tw  # noqa: E402

from _reward_fork import activate_reward_fork  # noqa: E402
from _run_guard import acquire_experiment_run_lock  # noqa: E402
from _sim_constants_fork import (  # noqa: E402
    FIXED_SPLIT_DT,
    apply_experiment_dt_profile,
    get_applied_dt_profile,
    require_dt_profile,
)
from _split_frozen import (  # noqa: E402
    EXPERIMENT_SEED,
    TRAIN_EPISODES_DEFAULT,
    frozen_training_config,
    reward_flags_snapshot,
    reward_waste_off_budget_on,
    sac_mpo_config_overrides,
)
from _runner_common import (  # noqa: E402
    RESULTS_DIR,
    baseline_exp7_metadata,
    count_post_budget_shutter_cmds,
    evaluate_learning_mode,
    _learning_stats_summary,
)
from _warmup_fingerprint_patch import (  # noqa: E402
    activate_warmup_fingerprint_patch,
    set_warmup_fingerprint_extra,
)

import numpy as np  # noqa: E402

EXPERIMENT_ID = "ml_sac_shutter_reward_split"
HYPOTHESIS_ID = "sac_shutter_reward_split"
EXPERIMENT_LOG = RESULTS_DIR / "shutter_reward_split.log"

ARM_WASTE_OFF = "waste_off_budget_on"


def append_log(line: str) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
    with EXPERIMENT_LOG.open("a", encoding="utf-8") as fh:
        fh.write(f"[{stamp}] {line}\n")


def _load_sac_agent():
    _sac_spec = importlib.util.spec_from_file_location(
        "ml_split_sac_agent_fork",
        OVERNIGHT_ROOT / "agents" / "sac_agent_fork.py",
    )
    assert _sac_spec and _sac_spec.loader
    _sac_mod = importlib.util.module_from_spec(_sac_spec)
    _sac_spec.loader.exec_module(_sac_mod)
    return _sac_mod.SACAgent


def _patch_run_config(
    run_dir: Path,
    *,
    arm_id: str,
    reward_flags: dict[str, bool],
    dt_profile: dict[str, Any],
    enable_tensorboard: bool,
) -> None:
    config_path = run_dir / "config.json"
    if not config_path.is_file():
        raise FileNotFoundError(f"Missing run config: {config_path}")
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    payload["experiment"] = {
        "experiment_id": EXPERIMENT_ID,
        "arm_id": arm_id,
        "hypothesis_id": HYPOTHESIS_ID,
        "attitude_request_mode": "vector",
        "agent_kind": "sac",
        "reward_mode": "sparse",
        "reward_flags": reward_flags,
        "baseline_comparison": baseline_exp7_metadata(),
        "dt_profile": dt_profile,
        "enable_tensorboard": bool(enable_tensorboard),
    }
    config_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _make_env(setup: tw.TrainingWorkflowSetup) -> Any:
    n_targets = len(setup.mission_setup.resolve(require_camera=True).target_areas or ())
    return tw.make_attitude_control_env(
        secondary_camera_observation_line_n_bins=setup.secondary_camera_bins,
        reward_config=setup.mpo_config.reward,
        feature_config=setup.feature_config,
        n_mission_targets=n_targets,
        observation_layout=setup.observation_layout,
    )


def run_waste_off_budget_on(
    *,
    show_progress: bool = False,
    train_episodes: int | None = None,
    trim_artifacts: bool = False,
    enable_tensorboard: bool = True,
) -> dict[str, Any]:
    """Treatment: waste penalty off, budget-exhausted penalty on."""
    arm_id = ARM_WASTE_OFF
    acquire_experiment_run_lock(script=arm_id)
    append_log(f"START {arm_id} tensorboard={enable_tensorboard}")

    dt_profile = apply_experiment_dt_profile()
    require_dt_profile(FIXED_SPLIT_DT, context=f"{EXPERIMENT_ID}:{arm_id}")
    applied = get_applied_dt_profile() or {}

    set_warmup_fingerprint_extra(
        sim_dt_s=dt_profile.get("sim_dt_s"),
        controller_interval_s=dt_profile.get("controller_interval_s"),
        reward_mode="sparse",
        budget_arm=arm_id,
        attitude_request_mode="vector",
        enable_shutter_waste_penalty=False,
        enable_budget_exhausted_shutter_penalty=True,
    )
    activate_warmup_fingerprint_patch()
    activate_reward_fork()

    n_train = int(
        train_episodes if train_episodes is not None else dt_profile.get("train_episodes", TRAIN_EPISODES_DEFAULT)
    )
    stamp = datetime.now(timezone.utc).strftime("%H-%M-%S")
    cfg = frozen_training_config(
        run_id=f"ml_sac_shutter_split_{stamp}",
        train_episodes=n_train,
        rebuild_warmup_bundle_cache=True,
        experiment_name="sac shutter reward split waste_off",
    )
    if trim_artifacts:
        cfg = replace(
            cfg,
            train_episode_videos=0,
            eval_episode_videos=1,
            wait_for_background_artifacts=False,
        )
    if enable_tensorboard:
        cfg = replace(cfg, enable_tensorboard=True)

    setup = tw.build_training_workflow_setup(cfg)
    mpo = sac_mpo_config_overrides(setup.mpo_config)
    mpo = reward_waste_off_budget_on(mpo)
    setup = replace(setup, mpo_config=mpo)
    reward_flags = reward_flags_snapshot(mpo.reward)

    env = _make_env(setup)
    SACAgent = _load_sac_agent()
    setup = replace(setup, agent=SACAgent(env, config=setup.mpo_config))

    _patch_run_config(
        setup.run_dir,
        arm_id=arm_id,
        reward_flags=reward_flags,
        dt_profile=applied,
        enable_tensorboard=enable_tensorboard,
    )

    t0 = time.perf_counter()
    ctx = tw.open_training_workflow(setup, show_progress=show_progress)
    try:
        tw.run_warmup(ctx)
        tw.run_training(ctx)
        workflow_result = tw.run_eval(ctx)
    except Exception:
        if ctx.worker is not None and ctx.config.background_artifacts:
            ctx.worker.shutdown(wait=False)
        raise
    finally:
        ctx.close()

    wall_s = time.perf_counter() - t0
    train_returns = [float(ep.episode_return) for ep in workflow_result.train_results]
    eval_returns = [float(ep.episode_return) for ep in workflow_result.eval_results]
    warmup_returns = [float(ep.episode_return) for ep in workflow_result.warmup_results]
    learning_stats = _learning_stats_summary(setup.agent, workflow_result.train_results)
    signal = evaluate_learning_mode(train_returns, eval_returns, learning_stats=learning_stats)
    shutter_stats = count_post_budget_shutter_cmds(workflow_result.train_results)

    tb_dir = setup.run_dir / "tensorboard"
    tensorboard_ok = bool(
        enable_tensorboard
        and tb_dir.is_dir()
        and any(tb_dir.glob("events.out.tfevents.*"))
    )

    kpis = {
        "arm_id": arm_id,
        "hypothesis_id": HYPOTHESIS_ID,
        "run_dir": str(setup.run_dir),
        "tensorboard_dir": str(tb_dir) if enable_tensorboard else None,
        "tensorboard_ok": tensorboard_ok,
        "attitude_request_mode": "vector",
        "agent_kind": "sac",
        "reward_mode": "sparse",
        "reward_flags": reward_flags,
        "wall_s": wall_s,
        "dt_profile": dt_profile,
        "warmup_returns": warmup_returns,
        "train_returns": train_returns,
        "eval_returns": eval_returns,
        "eval_return_mean": signal["eval_return_mean"],
        "learning_signal": signal,
        "post_budget_shutter_cmds": shutter_stats,
        "baseline_exp7": baseline_exp7_metadata(),
        "seed": EXPERIMENT_SEED,
    }
    append_log(
        f"DONE {arm_id} learning_mode={signal['learning_mode']} "
        f"eval_mean={signal['eval_return_mean']} post_budget_cmds={shutter_stats['total']}"
    )
    return kpis


__all__ = ["ARM_WASTE_OFF", "EXPERIMENT_ID", "append_log", "run_waste_off_budget_on"]
