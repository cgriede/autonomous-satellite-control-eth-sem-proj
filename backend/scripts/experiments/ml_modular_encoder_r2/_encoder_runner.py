"""Run SAC arms with flat (A0) vs compressed (A1) encoder — Exp 6 r2."""

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
    p = str(path)
    if p in sys.path:
        sys.path.remove(p)
    sys.path.insert(0, p)

from _encoder_sim import (  # noqa: E402
    DT_15,
    apply_dt_profile,
    apply_experiment_dt_profile,
    get_applied_dt_profile,
    require_dt_profile,
    write_dt_profile,
)
from _run_guard import acquire_experiment_run_lock  # noqa: E402

from _profile_baseline import (  # noqa: E402
    frozen_training_config,
    profile_reward_mode,
    shared_mpo_overrides,
)
from _reward_fork import activate_reward_fork  # noqa: E402
from _warmup_fingerprint_patch import (  # noqa: E402
    activate_warmup_fingerprint_patch,
    set_warmup_fingerprint_extra,
)
from s01_utils import training_workflow as tw  # noqa: E402

_overnight_spec = importlib.util.spec_from_file_location(
    "ml_overnight_runner_common_encoder_r2",
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
EXPERIMENT_LOG = RESULTS_DIR / "modular_encoder_r2.log"
EXPERIMENT_ID = "ml_modular_encoder_r2"

EncoderArmKind = Literal["flat", "compress"]


def append_log(line: str) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
    with EXPERIMENT_LOG.open("a", encoding="utf-8") as fh:
        fh.write(f"[{stamp}] {line}\n")


@dataclass(frozen=True)
class ArmSpec:
    arm_id: str
    encoder_kind: EncoderArmKind
    hypothesis_id: str
    vector_embed_dim: int = 8


def _make_sac_env(setup: tw.TrainingWorkflowSetup, mpo_config: Any) -> Any:
    n_targets = len(setup.mission_setup.resolve(require_camera=True).target_areas or ())
    return tw.make_attitude_control_env(
        secondary_camera_observation_line_n_bins=setup.secondary_camera_bins,
        reward_config=mpo_config.reward,
        feature_config=setup.feature_config,
        n_mission_targets=n_targets,
        observation_layout=setup.observation_layout,
    )


def _replace_agent(setup: tw.TrainingWorkflowSetup, agent: Any) -> tw.TrainingWorkflowSetup:
    return replace(setup, agent=agent)


def _attach_sac_agent(
    setup: tw.TrainingWorkflowSetup,
    spec: ArmSpec,
    mpo_config: Any,
) -> tw.TrainingWorkflowSetup:
    env = _make_sac_env(setup, mpo_config)
    if spec.encoder_kind == "flat":
        _sac_spec = importlib.util.spec_from_file_location(
            "ml_encoder_r2_sac_agent_fork",
            OVERNIGHT_ROOT / "agents" / "sac_agent_fork.py",
        )
        assert _sac_spec and _sac_spec.loader
        _sac_mod = importlib.util.module_from_spec(_sac_spec)
        _sac_spec.loader.exec_module(_sac_mod)
        return _replace_agent(setup, _sac_mod.SACAgent(env, config=mpo_config))
    from encoder_agents.sac_modular_agent import SACModularAgent

    return _replace_agent(
        setup,
        SACModularAgent(
            env,
            config=mpo_config,
            encoder_mode="compress",
            vector_embed_dim=spec.vector_embed_dim,
        ),
    )


def run_sac_arm(spec: ArmSpec, *, show_progress: bool = False, trim_artifacts: bool = False) -> dict[str, Any]:
    acquire_experiment_run_lock(script=f"arm:{spec.arm_id}")
    append_log(f"START {spec.arm_id} encoder={spec.encoder_kind}")

    profile = apply_experiment_dt_profile()
    apply_dt_profile(DT_15)
    require_dt_profile(DT_15, context=f"{EXPERIMENT_ID}:{spec.arm_id}")
    applied = get_applied_dt_profile()
    append_log(
        f"DT profile arm={spec.arm_id} "
        f"sim_dt_s={applied['sim_dt_s']} controller_interval_s={applied['controller_interval_s']}"
    )

    reward_mode = profile_reward_mode()
    mpo_overrides = shared_mpo_overrides()
    set_warmup_fingerprint_extra(
        sim_dt_s=profile.get("sim_dt_s"),
        controller_interval_s=profile.get("controller_interval_s"),
        reward_mode=reward_mode,
        encoder_arm=spec.arm_id,
        vector_embed_dim=spec.vector_embed_dim if spec.encoder_kind == "compress" else None,
        **mpo_overrides,
    )
    activate_warmup_fingerprint_patch()
    activate_reward_fork(reward_mode)

    stamp = datetime.now(timezone.utc).strftime("%H-%M-%S")
    cfg = frozen_training_config(
        run_id=f"ml_encoder_r2_{spec.arm_id}_{stamp}",
        train_episodes=int(profile.get("train_episodes", 50)),
        rebuild_warmup_bundle_cache=True,
    )
    if trim_artifacts:
        cfg = replace(
            cfg,
            train_episode_videos=0,
            eval_episode_videos=1,
            wait_for_background_artifacts=False,
        )

    setup = tw.build_training_workflow_setup(cfg)
    setup = replace(setup, mpo_config=replace(setup.mpo_config, **mpo_overrides))
    setup = _attach_sac_agent(setup, spec, setup.mpo_config)

    t0 = time.perf_counter()
    workflow_result = tw.run_training_workflow(setup, show_progress=show_progress)
    wall_s = time.perf_counter() - t0

    train_returns = [float(ep.episode_return) for ep in workflow_result.train_results]
    eval_returns = [float(ep.episode_return) for ep in workflow_result.eval_results]
    learning_stats = _learning_stats_summary(setup.agent, workflow_result.train_results)
    signal = evaluate_learning_mode(
        train_returns,
        eval_returns,
        learning_stats=learning_stats,
        agent_kind="sac",
    )
    debug_eps = [
        _episode_debug_row(ep, episode_idx=i) for i, ep in enumerate(workflow_result.train_results)
    ]

    kpis = {
        "arm_id": spec.arm_id,
        "encoder_kind": spec.encoder_kind,
        "vector_embed_dim": spec.vector_embed_dim,
        "hypothesis_id": spec.hypothesis_id,
        "run_dir": str(setup.run_dir),
        "wall_s": wall_s,
        "dt_profile": profile,
        "reward_mode": reward_mode,
        "mpo_overrides": mpo_overrides,
        "agent_kind": "sac",
        "train_returns": train_returns,
        "eval_returns": eval_returns,
        "eval_return_mean": signal["eval_return_mean"],
        "learning_signal": signal,
        "learning_stats": learning_stats,
        "debug_episodes": debug_eps,
    }
    append_log(
        f"DONE {spec.arm_id} learning_mode={signal['learning_mode']} "
        f"train_mean={signal.get('train_return_mean', 0):.1f}"
    )
    return kpis


def verdict_for_arm(kpis: dict[str, Any], *, baseline: dict[str, Any] | None) -> str:
    signal = kpis.get("learning_signal") or {}
    if signal.get("learning_mode"):
        if baseline is None:
            return "supported"
        base_signal = baseline.get("learning_signal") or {}
        base_train = baseline.get("train_returns") or []
        train = kpis.get("train_returns") or []
        if train and base_train and max(train) > max(base_train):
            return "supported"
        if signal.get("learning_mode") and not base_signal.get("learning_mode"):
            return "supported"
        return "inconclusive"
    return "inconclusive"


__all__ = [
    "ArmSpec",
    "EXPERIMENT_ID",
    "append_log",
    "run_sac_arm",
    "verdict_for_arm",
    "write_analysis_card",
    "write_hypothesis_result",
    "write_dt_profile",
    "RESULTS_DIR",
]
