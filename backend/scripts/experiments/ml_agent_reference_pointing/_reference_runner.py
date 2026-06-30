"""Run Ref0/Ref1/Ref2 agent-reference pointing arms."""

from __future__ import annotations

import importlib.util
import json
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
_PATH_ROOTS = (BACKEND_DIR, S01_DIR, OVERNIGHT_ROOT, EXPERIMENT_ROOT)
for path in reversed(_PATH_ROOTS):
    p = str(path)
    if p in sys.path:
        sys.path.remove(p)
    sys.path.insert(0, p)

from autonomous_control.action_adapter import AttitudeRequestMode  # noqa: E402
from s01_utils import training_workflow as tw  # noqa: E402

from _reference_frozen import (  # noqa: E402
    EXPERIMENT_SEED,
    TRAIN_EPISODES_DEFAULT,
    frozen_training_config,
    sac_mpo_config_overrides,
)
from _reward_fork import activate_reward_fork  # noqa: E402
from _run_guard import acquire_experiment_run_lock  # noqa: E402
from _sim_constants_fork import (  # noqa: E402
    FIXED_REFERENCE_DT,
    apply_experiment_dt_profile,
    get_applied_dt_profile,
    require_dt_profile,
)
from _runner_common import RESULTS_DIR, evaluate_learning_mode, write_hypothesis_result  # noqa: E402
from _warmup_fingerprint_patch import (  # noqa: E402
    activate_warmup_fingerprint_patch,
    set_warmup_fingerprint_extra,
)

EXPERIMENT_LOG = RESULTS_DIR / "reference.log"


def append_log(line: str) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
    with EXPERIMENT_LOG.open("a", encoding="utf-8") as fh:
        fh.write(f"[{stamp}] {line}\n")


@dataclass(frozen=True)
class ReferenceArmSpec:
    arm_id: str
    hypothesis_id: str
    run_id: str
    attitude_request_mode: AttitudeRequestMode
    agent_kind: Literal["sac", "mpo"]
    reward_mode: Literal["sparse", "dense"] = "sparse"


def _load_sac_agent():
    _sac_spec = importlib.util.spec_from_file_location(
        "ml_ref_sac_agent_fork",
        OVERNIGHT_ROOT / "agents" / "sac_agent_fork.py",
    )
    assert _sac_spec and _sac_spec.loader
    _sac_mod = importlib.util.module_from_spec(_sac_spec)
    _sac_spec.loader.exec_module(_sac_mod)
    return _sac_mod.SACAgent


def _patch_run_config(
    run_dir: Path,
    *,
    spec: ReferenceArmSpec,
    dt_profile: dict[str, Any],
) -> None:
    config_path = run_dir / "config.json"
    if not config_path.is_file():
        raise FileNotFoundError(f"Missing run config: {config_path}")
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    payload["experiment"] = {
        "experiment_id": "ml_agent_reference_pointing",
        "arm_id": spec.arm_id,
        "hypothesis_id": spec.hypothesis_id,
        "attitude_request_mode": spec.attitude_request_mode,
        "agent_kind": spec.agent_kind,
        "reward_mode": spec.reward_mode,
        "dt_profile": dt_profile,
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


def _attach_agent(setup: tw.TrainingWorkflowSetup, spec: ReferenceArmSpec) -> tw.TrainingWorkflowSetup:
    env = _make_env(setup)
    if spec.agent_kind == "sac":
        SACAgent = _load_sac_agent()
        return replace(setup, agent=SACAgent(env, config=setup.mpo_config))
    from autonomous_control.controller_agent import MPOAgent

    return replace(setup, agent=MPOAgent(env, config=setup.mpo_config))


def _apply_arm_runtime(spec: ReferenceArmSpec, dt_profile: dict[str, Any]) -> None:
    set_warmup_fingerprint_extra(
        sim_dt_s=dt_profile.get("sim_dt_s"),
        controller_interval_s=dt_profile.get("controller_interval_s"),
        reward_mode=spec.reward_mode,
        reference_arm=spec.arm_id,
        attitude_request_mode=spec.attitude_request_mode,
    )
    activate_warmup_fingerprint_patch()
    activate_reward_fork("sparse", attitude_request_mode=spec.attitude_request_mode)


def _sum_hold_last_count(episodes: list[Any]) -> int:
    return sum(int(getattr(ep, "vector_hold_last_count", 0) or 0) for ep in episodes)


def run_reference_arm(
    spec: ReferenceArmSpec,
    *,
    show_progress: bool = False,
    train_episodes: int | None = None,
    warmup_episodes: int | None = None,
    eval_episodes: int | None = None,
    trim_artifacts: bool = False,
) -> dict[str, Any]:
    acquire_experiment_run_lock(script=f"arm:{spec.arm_id}")
    append_log(
        f"START {spec.arm_id} mode={spec.attitude_request_mode} agent={spec.agent_kind}"
    )

    dt_profile = apply_experiment_dt_profile()
    require_dt_profile(FIXED_REFERENCE_DT, context=f"ml_agent_reference_pointing:{spec.arm_id}")
    applied = get_applied_dt_profile() or {}

    _apply_arm_runtime(spec, dt_profile)
    stamp = datetime.now(timezone.utc).strftime("%H-%M-%S")
    n_train = int(train_episodes if train_episodes is not None else dt_profile.get("train_episodes", TRAIN_EPISODES_DEFAULT))
    cfg = frozen_training_config(
        run_id=f"ml_ref_{spec.run_id}_{stamp}",
        train_episodes=n_train,
        rebuild_warmup_bundle_cache=True,
        experiment_name=f"agent reference {spec.arm_id}",
        attitude_request_mode=spec.attitude_request_mode,
    )
    if warmup_episodes is not None:
        cfg = replace(cfg, warmup_episodes=int(warmup_episodes))
    if eval_episodes is not None:
        cfg = replace(cfg, eval_episodes=int(eval_episodes))
    if trim_artifacts:
        cfg = replace(
            cfg,
            train_episode_videos=0,
            eval_episode_videos=1,
            wait_for_background_artifacts=False,
        )

    setup = tw.build_training_workflow_setup(cfg)
    setup = replace(setup, mpo_config=sac_mpo_config_overrides(setup.mpo_config))
    setup = _attach_agent(setup, spec)

    _patch_run_config(setup.run_dir, spec=spec, dt_profile=applied)

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
    from _runner_common import _learning_stats_summary

    learning_stats = _learning_stats_summary(setup.agent, workflow_result.train_results)
    signal = evaluate_learning_mode(
        train_returns,
        eval_returns,
        learning_stats=learning_stats,
        agent_kind=spec.agent_kind,
    )

    all_eps = (
        list(workflow_result.warmup_results)
        + list(workflow_result.train_results)
        + list(workflow_result.eval_results)
    )
    hold_last_total = _sum_hold_last_count(all_eps)

    kpis = {
        "arm_id": spec.arm_id,
        "hypothesis_id": spec.hypothesis_id,
        "run_id": spec.run_id,
        "run_dir": str(setup.run_dir),
        "attitude_request_mode": spec.attitude_request_mode,
        "agent_kind": spec.agent_kind,
        "reward_mode": spec.reward_mode,
        "wall_s": wall_s,
        "dt_profile": dt_profile,
        "warmup_returns": warmup_returns,
        "train_returns": train_returns,
        "eval_returns": eval_returns,
        "eval_return_mean": signal["eval_return_mean"],
        "learning_signal": signal,
        "hold_last_count": hold_last_total,
        "reference_clamp_count": hold_last_total,
        "safe_mode_takeover_count": None,
    }
    append_log(
        f"DONE {spec.arm_id} learning_mode={signal['learning_mode']} "
        f"hold_last_count={hold_last_total}"
    )
    return kpis


def default_arms(*, include_ref2: bool = False) -> tuple[ReferenceArmSpec, ...]:
    arms = (
        ReferenceArmSpec(
            arm_id="ref0",
            hypothesis_id="agent_ref_torque_control",
            run_id="ref0_torque",
            attitude_request_mode="torque",
            agent_kind="sac",
            reward_mode="sparse",
        ),
        ReferenceArmSpec(
            arm_id="ref1",
            hypothesis_id="agent_ref_vector_pointing",
            run_id="ref1_vector",
            attitude_request_mode="vector",
            agent_kind="sac",
            reward_mode="sparse",
        ),
    )
    if include_ref2:
        arms = (
            *arms,
            ReferenceArmSpec(
                arm_id="ref2",
                hypothesis_id="agent_ref_vector_mpo",
                run_id="ref2_vector_mpo",
                attitude_request_mode="vector",
                agent_kind="mpo",
                reward_mode="dense",
            ),
        )
    return arms


def verdict_for_reference(kpis: dict[str, Any]) -> str:
    signal = kpis.get("learning_signal") or {}
    if signal.get("learning_mode"):
        return "supported"
    train = kpis.get("train_returns") or []
    if train and all(float(r) == 0.0 for r in train):
        return "falsified"
    return "inconclusive"


__all__ = [
    "ReferenceArmSpec",
    "append_log",
    "default_arms",
    "run_reference_arm",
    "verdict_for_reference",
    "RESULTS_DIR",
]
