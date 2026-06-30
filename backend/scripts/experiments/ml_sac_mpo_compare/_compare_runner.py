"""Run SAC sparse vs MPO dense compare arms with patience early abort."""

from __future__ import annotations

import importlib.util
import sys
import time
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import _cpu_budget  # noqa: F401

EXPERIMENT_ROOT = Path(__file__).resolve().parent
OVERNIGHT_ROOT = EXPERIMENT_ROOT.parent / "ml_algo_overnight"
BACKEND_DIR = EXPERIMENT_ROOT.parents[2]
S01_DIR = BACKEND_DIR / "notebooks" / "s01"
_PATH_ROOTS = (BACKEND_DIR, S01_DIR, EXPERIMENT_ROOT, OVERNIGHT_ROOT)
for path in reversed(_PATH_ROOTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from autonomous_control.controller_agent import MPOAgent  # noqa: E402
from s01_utils import training_workflow as tw  # noqa: E402

from _compare_sim import (  # noqa: E402
    FIXED_COMPARE_PROFILE,
    apply_experiment_dt_profile,
    get_applied_dt_profile,
    require_dt_profile,
)
from _compare_frozen import (  # noqa: E402
    COMPARE_TRAIN_EPISODES_DEFAULT,
    PATIENCE_EPISODES_DEFAULT,
    frozen_training_config,
)
from _reward_fork import RewardForkMode, activate_reward_fork  # noqa: E402
from _run_guard import acquire_experiment_run_lock  # noqa: E402
from _training_loop_fork import run_training_with_patience  # noqa: E402
from _warmup_fingerprint_patch import (  # noqa: E402
    activate_warmup_fingerprint_patch,
    set_warmup_fingerprint_extra,
)

_overnight_spec = importlib.util.spec_from_file_location(
    "ml_overnight_runner_common_compare",
    OVERNIGHT_ROOT / "_runner_common.py",
)
assert _overnight_spec and _overnight_spec.loader
_overnight_runner = importlib.util.module_from_spec(_overnight_spec)
sys.modules[_overnight_spec.name] = _overnight_runner
_overnight_spec.loader.exec_module(_overnight_runner)

_episode_debug_row = _overnight_runner._episode_debug_row
_learning_stats_summary = _overnight_runner._learning_stats_summary
evaluate_learning_mode = _overnight_runner.evaluate_learning_mode
write_analysis_card = _overnight_runner.write_analysis_card
write_hypothesis_result = _overnight_runner.write_hypothesis_result

RESULTS_DIR = EXPERIMENT_ROOT / "results"
EXPERIMENT_LOG = RESULTS_DIR / "compare.log"


def append_log(line: str) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
    with EXPERIMENT_LOG.open("a", encoding="utf-8") as fh:
        fh.write(f"[{stamp}] {line}\n")


@dataclass(frozen=True)
class CompareArmSpec:
    arm_id: str
    hypothesis_id: str
    run_id: str
    agent_kind: Literal["sac", "mpo"]
    reward_mode: RewardForkMode


def _load_sac_agent():
    _sac_spec = importlib.util.spec_from_file_location(
        "ml_compare_sac_agent_fork",
        OVERNIGHT_ROOT / "agents" / "sac_agent_fork.py",
    )
    assert _sac_spec and _sac_spec.loader
    _sac_mod = importlib.util.module_from_spec(_sac_spec)
    _sac_spec.loader.exec_module(_sac_mod)
    return _sac_mod.SACAgent


def _make_env(setup: tw.TrainingWorkflowSetup) -> Any:
    n_targets = len(setup.mission_setup.resolve(require_camera=True).target_areas or ())
    return tw.make_attitude_control_env(
        secondary_camera_observation_line_n_bins=setup.secondary_camera_bins,
        reward_config=setup.mpo_config.reward,
        feature_config=setup.feature_config,
        n_mission_targets=n_targets,
        observation_layout=setup.observation_layout,
    )


def _replace_agent(setup: tw.TrainingWorkflowSetup, agent: Any) -> tw.TrainingWorkflowSetup:
    return replace(setup, agent=agent)


def _attach_agent(setup: tw.TrainingWorkflowSetup, spec: CompareArmSpec) -> tw.TrainingWorkflowSetup:
    env = _make_env(setup)
    if spec.agent_kind == "sac":
        SACAgent = _load_sac_agent()
        return _replace_agent(setup, SACAgent(env, config=setup.mpo_config))
    return _replace_agent(setup, MPOAgent(env, config=setup.mpo_config))


def run_compare_arm(
    spec: CompareArmSpec,
    *,
    show_progress: bool = False,
    trim_artifacts: bool = False,
    max_train_episodes: int | None = None,
    patience_episodes: int = PATIENCE_EPISODES_DEFAULT,
    enable_tensorboard: bool = False,
) -> dict[str, Any]:
    acquire_experiment_run_lock(script=f"arm:{spec.arm_id}")
    append_log(f"START {spec.arm_id} agent={spec.agent_kind} reward={spec.reward_mode}")

    profile = apply_experiment_dt_profile()
    require_dt_profile(FIXED_COMPARE_PROFILE, context=f"ml_sac_mpo_compare:{spec.arm_id}")
    applied = get_applied_dt_profile()
    append_log(
        f"DT arm={spec.arm_id} sim_dt_s={applied['sim_dt_s']} "
        f"controller_interval_s={applied['controller_interval_s']}"
    )

    set_warmup_fingerprint_extra(
        sim_dt_s=profile.get("sim_dt_s"),
        controller_interval_s=profile.get("controller_interval_s"),
        reward_mode=spec.reward_mode,
        compare_arm=spec.arm_id,
    )
    activate_warmup_fingerprint_patch()
    activate_reward_fork(spec.reward_mode)

    train_cap = int(max_train_episodes or profile.get("train_episodes", COMPARE_TRAIN_EPISODES_DEFAULT))
    stamp = datetime.now(timezone.utc).strftime("%H-%M-%S")
    cfg = frozen_training_config(
        run_id=f"ml_compare_{spec.run_id}_{stamp}",
        train_episodes=train_cap,
        rebuild_warmup_bundle_cache=True,
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
    setup = _attach_agent(setup, spec)

    t0 = time.perf_counter()
    ctx = tw.open_training_workflow(setup, show_progress=show_progress)
    try:
        tw.run_warmup(ctx)
        abort_meta = run_training_with_patience(
            ctx,
            max_train_episodes=train_cap,
            patience_episodes=int(patience_episodes),
        )
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
    signal = evaluate_learning_mode(
        train_returns,
        eval_returns,
        learning_stats=learning_stats,
        agent_kind=spec.agent_kind,
    )
    debug_eps = [
        _episode_debug_row(ep, episode_idx=i) for i, ep in enumerate(workflow_result.train_results)
    ]
    videos = [
        {
            "kind": entry["phase"],
            "episode_idx": entry["episode_idx"],
            "rank": entry.get("rank"),
            "path": entry["video"],
        }
        for entry in workflow_result.artifact_manifest
        if entry.get("video")
    ]

    kpis = {
        "arm_id": spec.arm_id,
        "hypothesis_id": spec.hypothesis_id,
        "run_id": spec.run_id,
        "run_dir": str(setup.run_dir),
        "wall_s": wall_s,
        "dt_profile": profile,
        "reward_mode": spec.reward_mode,
        "agent_kind": spec.agent_kind,
        "warmup_returns": warmup_returns,
        "warmup_return_mean": float(sum(warmup_returns) / len(warmup_returns)) if warmup_returns else 0.0,
        "train_returns": train_returns,
        "eval_returns": eval_returns,
        "train_return_mean": float(sum(train_returns) / len(train_returns)) if train_returns else 0.0,
        "eval_return_mean": signal["eval_return_mean"],
        "learning_signal": signal,
        "learning_stats": learning_stats,
        "debug_episodes": debug_eps,
        "early_abort": abort_meta,
        "artifacts": {"videos": videos},
        "last_train_kpis": workflow_result.train_kpis,
    }
    append_log(
        f"DONE {spec.arm_id} learning_mode={signal['learning_mode']} "
        f"train_eps={abort_meta['train_episodes_completed']} "
        f"early_aborted={abort_meta['early_aborted']}"
    )
    return kpis


def default_arms() -> tuple[CompareArmSpec, ...]:
    return (
        CompareArmSpec(
            arm_id="compare_sac",
            hypothesis_id="sac_sparse_compare",
            run_id="compare_sac",
            agent_kind="sac",
            reward_mode="sparse",
        ),
        CompareArmSpec(
            arm_id="compare_mpo",
            hypothesis_id="mpo_dense_compare",
            run_id="compare_mpo",
            agent_kind="mpo",
            reward_mode="dense",
        ),
    )


def verdict_for_compare(kpis: dict[str, Any]) -> str:
    signal = kpis.get("learning_signal") or {}
    if signal.get("learning_mode"):
        return "supported"
    train = kpis.get("train_returns") or []
    if train and all(float(r) == 0.0 for r in train):
        return "falsified"
    return "inconclusive"


__all__ = [
    "CompareArmSpec",
    "append_log",
    "default_arms",
    "run_compare_arm",
    "verdict_for_compare",
    "write_analysis_card",
    "write_hypothesis_result",
    "RESULTS_DIR",
]
