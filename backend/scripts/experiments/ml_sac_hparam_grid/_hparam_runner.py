"""SAC flat-encoder arms: model size (S/M/L) × reward (sparse/dense)."""

from __future__ import annotations

import importlib.util
import sys
import time
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

EXPERIMENT_ROOT = Path(__file__).resolve().parent
MODULAR_ROOT = EXPERIMENT_ROOT.parent / "ml_modular_encoder"
COMPARE_ROOT = EXPERIMENT_ROOT.parent / "ml_sac_mpo_compare"
OVERNIGHT_ROOT = EXPERIMENT_ROOT.parent / "ml_algo_overnight"
BACKEND_DIR = EXPERIMENT_ROOT.parents[2]
S01_DIR = BACKEND_DIR / "notebooks" / "s01"
for path in (BACKEND_DIR, S01_DIR, MODULAR_ROOT, COMPARE_ROOT, OVERNIGHT_ROOT, EXPERIMENT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import _cpu_budget  # noqa: F401

from _encoder_sim import (  # noqa: E402
    DT_15,
    apply_dt_profile,
    apply_experiment_dt_profile,
    get_applied_dt_profile,
    require_dt_profile,
)
from _profile_baseline import frozen_training_config, shared_mpo_overrides, size_preset  # noqa: E402
from _run_guard import acquire_experiment_run_lock  # noqa: E402

from _reward_fork import activate_reward_fork  # noqa: E402  # compare fork: sparse | dense
from _warmup_fingerprint_patch import (  # noqa: E402
    activate_warmup_fingerprint_patch,
    set_warmup_fingerprint_extra,
)
from s01_utils import training_workflow as tw  # noqa: E402


def _load_overnight_runner() -> Any:
    saved_path = list(sys.path)
    filtered = [p for p in saved_path if p != str(EXPERIMENT_ROOT)]
    if str(OVERNIGHT_ROOT) not in filtered:
        filtered.insert(0, str(OVERNIGHT_ROOT))
    sys.path[:] = filtered
    try:
        spec = importlib.util.spec_from_file_location(
            "ml_overnight_runner_common_hparam_isolated",
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

_episode_debug_row = _overnight_runner._episode_debug_row
_learning_stats_summary = _overnight_runner._learning_stats_summary
evaluate_learning_mode = _overnight_runner.evaluate_learning_mode
write_hypothesis_result = _overnight_runner.write_hypothesis_result

RESULTS_DIR = EXPERIMENT_ROOT / "results"
EXPERIMENT_LOG = RESULTS_DIR / "sac_hparam_grid.log"

RewardMode = Literal["sparse", "dense"]
SizeLabel = Literal["S", "M", "L"]


def append_log(line: str) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
    with EXPERIMENT_LOG.open("a", encoding="utf-8") as fh:
        fh.write(f"[{stamp}] {line}\n")


@dataclass(frozen=True)
class HparamArmSpec:
    arm_id: str
    size: SizeLabel
    reward_mode: RewardMode
    hypothesis_id: str


def default_arms() -> tuple[HparamArmSpec, ...]:
    arms: list[HparamArmSpec] = []
    for size in ("S", "M", "L"):
        for reward in ("sparse", "dense"):
            arm_id = f"sac_{size.lower()}_{reward}"
            arms.append(
                HparamArmSpec(
                    arm_id=arm_id,
                    size=size,  # type: ignore[arg-type]
                    reward_mode=reward,  # type: ignore[arg-type]
                    hypothesis_id=f"sac_size_{size.lower()}_{reward}",
                )
            )
    return tuple(arms)


def _attach_sac_agent(setup: tw.TrainingWorkflowSetup, mpo_config: Any) -> tw.TrainingWorkflowSetup:
    n_targets = len(setup.mission_setup.resolve(require_camera=True).target_areas or ())
    env = tw.make_attitude_control_env(
        secondary_camera_observation_line_n_bins=setup.secondary_camera_bins,
        reward_config=mpo_config.reward,
        feature_config=setup.feature_config,
        n_mission_targets=n_targets,
        observation_layout=setup.observation_layout,
    )
    _sac_spec = importlib.util.spec_from_file_location(
        "ml_hparam_sac_agent_fork",
        OVERNIGHT_ROOT / "agents" / "sac_agent_fork.py",
    )
    assert _sac_spec and _sac_spec.loader
    _sac_mod = importlib.util.module_from_spec(_sac_spec)
    _sac_spec.loader.exec_module(_sac_mod)
    return replace(setup, agent=_sac_mod.SACAgent(env, config=mpo_config), mpo_config=mpo_config)


def run_hparam_arm(
    spec: HparamArmSpec,
    *,
    show_progress: bool = False,
    trim_artifacts: bool = False,
) -> dict[str, Any]:
    acquire_experiment_run_lock(script=f"arm:{spec.arm_id}")
    append_log(f"START {spec.arm_id} size={spec.size} reward={spec.reward_mode}")

    profile = apply_experiment_dt_profile()
    apply_dt_profile(DT_15)
    require_dt_profile(DT_15, context=f"ml_sac_hparam_grid:{spec.arm_id}")
    applied = get_applied_dt_profile()
    append_log(
        f"DT arm={spec.arm_id} sim_dt_s={applied['sim_dt_s']} "
        f"controller_interval_s={applied['controller_interval_s']}"
    )

    mpo_overrides = {**shared_mpo_overrides(), **size_preset(spec.size)}
    set_warmup_fingerprint_extra(
        sim_dt_s=profile.get("sim_dt_s"),
        controller_interval_s=profile.get("controller_interval_s"),
        reward_mode=spec.reward_mode,
        hparam_arm=spec.arm_id,
        model_size=spec.size,
        **mpo_overrides,
    )
    activate_warmup_fingerprint_patch()
    activate_reward_fork(spec.reward_mode)

    stamp = datetime.now(timezone.utc).strftime("%H-%M-%S")
    cfg = frozen_training_config(
        run_id=f"ml_sac_hparam_{spec.arm_id}_{stamp}",
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
    setup = _attach_sac_agent(setup, replace(setup.mpo_config, **mpo_overrides))

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
        "size": spec.size,
        "reward_mode": spec.reward_mode,
        "hypothesis_id": spec.hypothesis_id,
        "mpo_overrides": mpo_overrides,
        "run_dir": str(setup.run_dir),
        "wall_s": wall_s,
        "dt_profile": profile,
        "agent_kind": "sac",
        "encoder_kind": "flat",
        "train_returns": train_returns,
        "eval_returns": eval_returns,
        "eval_return_mean": signal["eval_return_mean"],
        "learning_signal": signal,
        "learning_stats": learning_stats,
        "debug_episodes": debug_eps,
    }
    append_log(
        f"DONE {spec.arm_id} learning_mode={signal['learning_mode']} "
        f"train_best={max(train_returns) if train_returns else 0:.1f} "
        f"eval_mean={signal.get('eval_return_mean', 0):.1f}"
    )
    out_path = RESULTS_DIR / "arm_kpis" / f"{spec.arm_id}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_hypothesis_result(out_path, experiment_id="ml_sac_hparam_grid", **kpis)
    return kpis


__all__ = [
    "HparamArmSpec",
    "append_log",
    "default_arms",
    "run_hparam_arm",
    "write_hypothesis_result",
    "RESULTS_DIR",
]
