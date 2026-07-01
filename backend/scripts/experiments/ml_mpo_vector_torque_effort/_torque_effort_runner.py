"""Exp 12: MPO vector sparse with torque-effort penalty forced on (override vector default)."""

from __future__ import annotations

import importlib.util
import json
import math
import sys
import time
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXPERIMENT_ROOT = Path(__file__).resolve().parent
OVERNIGHT_ROOT = EXPERIMENT_ROOT.parent / "ml_algo_overnight"
BACKEND_DIR = EXPERIMENT_ROOT.parents[2]
S01_DIR = BACKEND_DIR / "notebooks" / "s01"
EXPERIMENT_ID = "ml_mpo_vector_torque_effort"


def _ensure_experiment_root_first() -> None:
    experiment = str(EXPERIMENT_ROOT)
    while experiment in sys.path:
        sys.path.remove(experiment)
    sys.path.insert(0, experiment)


for path in (BACKEND_DIR, S01_DIR, OVERNIGHT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
_ensure_experiment_root_first()

import _cpu_budget  # noqa: F401

from autonomous_control.controller_agent import MPOAgent  # noqa: E402
from s01_utils import training_workflow as tw  # noqa: E402

from _profile_baseline import frozen_training_config, profile, shared_mpo_overrides  # noqa: E402
from _reward_fork import activate_reward_fork  # noqa: E402
from _run_guard import acquire_experiment_run_lock  # noqa: E402
from _sim_constants_fork import (  # noqa: E402
    DT_15,
    apply_experiment_dt_profile,
    apply_dt_profile,
    get_applied_dt_profile,
    require_dt_profile,
)
from _warmup_fingerprint_patch import (  # noqa: E402
    activate_warmup_fingerprint_patch,
    set_warmup_fingerprint_extra,
)


def _load_overnight_runner() -> Any:
    saved_path = list(sys.path)
    filtered = [p for p in saved_path if p != str(EXPERIMENT_ROOT)]
    if str(OVERNIGHT_ROOT) not in filtered:
        filtered.insert(0, str(OVERNIGHT_ROOT))
    sys.path[:] = filtered
    try:
        spec = importlib.util.spec_from_file_location(
            "ml_overnight_runner_common_mpo_vector_torque_effort",
            OVERNIGHT_ROOT / "_runner_common.py",
        )
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        return mod
    finally:
        sys.path[:] = saved_path


_overnight_runner = _load_overnight_runner()
_ensure_experiment_root_first()

_episode_debug_row = _overnight_runner._episode_debug_row
_learning_stats_summary = _overnight_runner._learning_stats_summary
evaluate_learning_mode = _overnight_runner.evaluate_learning_mode
write_hypothesis_result = _overnight_runner.write_hypothesis_result

RESULTS_DIR = EXPERIMENT_ROOT / "results"
EXPERIMENT_LOG = RESULTS_DIR / "mpo_vector_torque_effort.log"
ARM_ID = "vector_torque_effort"
HYPOTHESIS_ID = "mpo_vector_torque_effort"


def append_log(line: str) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
    with EXPERIMENT_LOG.open("a", encoding="utf-8") as fh:
        fh.write(f"[{stamp}] {line}\n")


@dataclass(frozen=True)
class TorqueEffortArmSpec:
    arm_id: str = ARM_ID
    hypothesis_id: str = HYPOTHESIS_ID


def _attach_mpo_agent(
    setup: tw.TrainingWorkflowSetup,
    mpo_config: Any,
) -> tw.TrainingWorkflowSetup:
    n_targets = len(setup.mission_setup.resolve(require_camera=True).target_areas or ())
    env = tw.make_attitude_control_env(
        secondary_camera_observation_line_n_bins=setup.secondary_camera_bins,
        reward_config=mpo_config.reward,
        feature_config=setup.feature_config,
        n_mission_targets=n_targets,
        observation_layout=setup.observation_layout,
    )
    return replace(setup, agent=MPOAgent(env, config=mpo_config), mpo_config=mpo_config)


def _apply_torque_effort_reward(
    setup: tw.TrainingWorkflowSetup,
    mpo_config: Any,
) -> tw.TrainingWorkflowSetup:
    """Force enable_torque_effort=True (production disables it for vector mode)."""
    reward = replace(mpo_config.reward, enable_torque_effort=True)
    mpo_config = replace(mpo_config, reward=reward)
    mission = setup.mission_setup
    sim_over = getattr(mission, "simulation_overrides", None)
    if sim_over is not None:
        mission = replace(mission, simulation_overrides=replace(sim_over, reward_config=reward))
    setup = replace(setup, mpo_config=mpo_config, mission_setup=mission)
    return _attach_mpo_agent(setup, mpo_config)


def _sync_run_config_mpo(setup: tw.TrainingWorkflowSetup) -> None:
    from utils.ml_training.training_run_artifacts import write_config_snapshot

    config_path = setup.run_dir / "config.json"
    snapshot = json.loads(config_path.read_text(encoding="utf-8"))
    snapshot["mpo"] = tw._mpo_config_snapshot(setup.mpo_config)
    snapshot["experiment"] = {
        "experiment_id": EXPERIMENT_ID,
        "arm_id": ARM_ID,
        "attitude_request_mode": "vector",
        "reward_mode": "sparse",
        "enable_torque_effort": True,
        "vector_comparator": profile().get("ref_run_id"),
    }
    write_config_snapshot(setup.run_dir, snapshot)


def _verify_dual_agent(agent: MPOAgent) -> dict[str, float]:
    if not hasattr(agent, "log_alpha_mu") or not hasattr(agent, "log_alpha_sigma"):
        raise RuntimeError("MPOAgent missing decoupled dual variables (log_alpha_mu/log_alpha_sigma)")
    return {
        "alpha_mu": float(agent.log_alpha_mu.exp().item()),
        "alpha_sigma": float(agent.log_alpha_sigma.exp().item()),
        "eta": float(agent.log_eta.exp().item()),
    }


def _verify_run_config_dual(run_dir: Path, expected: dict[str, Any]) -> dict[str, Any]:
    config_path = run_dir / "config.json"
    if not config_path.is_file():
        raise FileNotFoundError(f"Missing config.json in {run_dir}")
    snapshot = json.loads(config_path.read_text(encoding="utf-8"))
    mpo = snapshot.get("mpo") or snapshot.get("mpo_config") or {}
    reward = mpo.get("reward") or {}
    if not reward.get("enable_torque_effort"):
        raise RuntimeError(f"enable_torque_effort must be true in {config_path}")
    dual_keys = ("eps_eta", "target_kl_mu", "target_kl_sigma", "learning_rate_alpha")
    for key in dual_keys:
        if key in expected and float(mpo.get(key, -1)) != float(expected[key]):
            raise RuntimeError(
                f"config.json {key}={mpo.get(key)!r} != expected {expected[key]!r} in {config_path}"
            )
    exp = snapshot.get("experiment") or {}
    if exp.get("experiment_id") != EXPERIMENT_ID:
        raise RuntimeError(f"experiment_id mismatch in {config_path}")
    if exp.get("attitude_request_mode") != "vector":
        raise RuntimeError(f"attitude_request_mode must be vector in {config_path}")
    workflow = snapshot.get("workflow") or {}
    if workflow.get("attitude_request_mode") != "vector":
        raise RuntimeError(f"workflow.attitude_request_mode must be vector in {config_path}")
    return mpo


def run_torque_effort_arm(
    *,
    show_progress: bool = False,
    trim_artifacts: bool = False,
    train_episodes: int | None = None,
    smoke: bool = False,
) -> dict[str, Any]:
    if not smoke:
        acquire_experiment_run_lock(script=ARM_ID)
    append_log(f"START arm={ARM_ID} smoke={smoke}")

    dt_profile = apply_experiment_dt_profile()
    apply_dt_profile(DT_15)
    require_dt_profile(DT_15, context=f"{EXPERIMENT_ID}:{ARM_ID}")
    applied = get_applied_dt_profile()
    append_log(
        f"DT arm={ARM_ID} sim_dt_s={applied['sim_dt_s']} "
        f"controller_interval_s={applied['controller_interval_s']}"
    )

    mpo_overrides = shared_mpo_overrides()
    set_warmup_fingerprint_extra(
        sim_dt_s=dt_profile.get("sim_dt_s"),
        controller_interval_s=dt_profile.get("controller_interval_s"),
        reward_mode="sparse",
        mpo_dual_arm=ARM_ID,
        attitude_request_mode="vector",
        enable_torque_effort=True,
        **mpo_overrides,
    )
    activate_warmup_fingerprint_patch()
    activate_reward_fork("sparse")

    stamp = datetime.now(timezone.utc).strftime("%H-%M-%S")
    n_train = 1 if smoke else int(
        train_episodes if train_episodes is not None else profile().get("workflow", {}).get("train_episodes", 50)
    )
    run_suffix = "smoke" if smoke else ARM_ID
    cfg = frozen_training_config(
        run_id=f"ml_mpo_vector_torque_effort_{run_suffix}_{stamp}",
        train_episodes=n_train,
        rebuild_warmup_bundle_cache=True,
    )
    if cfg.attitude_request_mode != "vector":
        raise RuntimeError(f"frozen_training_config attitude_request_mode={cfg.attitude_request_mode!r}, want vector")
    if smoke:
        cfg = replace(
            cfg,
            warmup_episodes=1,
            train_episodes=0,
            eval_episodes=0,
            use_warmup_bundle_cache=False,
            background_artifacts=False,
            train_episode_videos=0,
            eval_episode_videos=0,
        )
    elif trim_artifacts:
        cfg = replace(
            cfg,
            train_episode_videos=0,
            eval_episode_videos=1,
            wait_for_background_artifacts=False,
        )

    setup = tw.build_training_workflow_setup(cfg)
    setup = _apply_torque_effort_reward(setup, replace(setup.mpo_config, **mpo_overrides))
    _sync_run_config_mpo(setup)
    dual_snapshot = _verify_dual_agent(setup.agent)

    if smoke:
        from autonomous_control.config.randomness import derive_seed
        import numpy as np

        warmup = setup.runner.run_serial(
            setup.agent,
            mode="warmup",
            episode_idx=0,
            collect_states=False,
            show_training_context=False,
            train_updates_per_step=0,
            feature_config=setup.feature_config,
            observation_layout=setup.observation_layout,
            np_rng=np.random.default_rng(derive_seed(7, "mpo_vector_torque_effort_smoke", 0)),
        )
        if len(setup.agent.buffer) == 0:
            raise RuntimeError("Smoke warmup produced empty buffer.")
        train_metrics = setup.agent.train()
        if train_metrics is None:
            raise RuntimeError("Smoke train() returned None")
        for key in ("kl", "alpha_mu", "alpha_sigma", "eta"):
            val = float(train_metrics.get(key, float("nan")))
            if not math.isfinite(val):
                raise RuntimeError(f"Smoke train_metrics[{key!r}] not finite: {val}")
        config_mpo = _verify_run_config_dual(setup.run_dir, mpo_overrides)
        return {
            "passed": True,
            "arm_id": ARM_ID,
            "attitude_request_mode": "vector",
            "enable_torque_effort": True,
            "warmup_return": float(warmup.episode_return),
            "warmup_steps": int(warmup.steps),
            "buffer_size": len(setup.agent.buffer),
            "train_metrics": train_metrics,
            "dual_snapshot": dual_snapshot,
            "config_mpo": config_mpo,
            "run_dir": str(setup.run_dir),
            "mpo_overrides": mpo_overrides,
        }

    t0 = time.perf_counter()
    workflow_result = tw.run_training_workflow(setup, show_progress=show_progress)
    wall_s = time.perf_counter() - t0

    config_mpo = _verify_run_config_dual(setup.run_dir, mpo_overrides)

    train_returns = [float(ep.episode_return) for ep in workflow_result.train_results]
    eval_returns = [float(ep.episode_return) for ep in workflow_result.eval_results]
    learning_stats = _learning_stats_summary(setup.agent, workflow_result.train_results)
    signal = evaluate_learning_mode(
        train_returns,
        eval_returns,
        learning_stats=learning_stats,
        agent_kind="mpo",
    )
    debug_eps = [
        _episode_debug_row(ep, episode_idx=i) for i, ep in enumerate(workflow_result.train_results)
    ]

    kpis = {
        "arm_id": ARM_ID,
        "hypothesis_id": HYPOTHESIS_ID,
        "reward_mode": "sparse",
        "attitude_request_mode": "vector",
        "enable_torque_effort": True,
        "mpo_overrides": mpo_overrides,
        "config_mpo": config_mpo,
        "dual_snapshot_end": _verify_dual_agent(setup.agent),
        "run_dir": str(setup.run_dir),
        "wall_s": wall_s,
        "dt_profile": dt_profile,
        "agent_kind": "mpo",
        "encoder_kind": "production",
        "train_returns": train_returns,
        "eval_returns": eval_returns,
        "eval_return_mean": signal["eval_return_mean"],
        "learning_signal": signal,
        "learning_stats": learning_stats,
        "debug_episodes": debug_eps,
        "vector_comparator": profile().get("ref_run_id"),
    }
    append_log(
        f"DONE {ARM_ID} learning_mode={signal['learning_mode']} "
        f"train_best={max(train_returns) if train_returns else 0:.1f} "
        f"eval_mean={signal.get('eval_return_mean', 0):.1f}"
    )
    return kpis


__all__ = [
    "ARM_ID",
    "EXPERIMENT_ID",
    "TorqueEffortArmSpec",
    "append_log",
    "run_torque_effort_arm",
    "write_hypothesis_result",
    "RESULTS_DIR",
]
