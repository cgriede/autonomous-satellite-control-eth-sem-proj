"""Exp 13 runner: cadence arms + optional hparam overrides on Exp 8 MPO protocol."""

from __future__ import annotations

import importlib.util
import json
import sys
import time
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXPERIMENT_ROOT = Path(__file__).resolve().parent
OVERNIGHT_ROOT = EXPERIMENT_ROOT.parent / "ml_algo_overnight"
BACKEND_DIR = EXPERIMENT_ROOT.parents[2]
S01_DIR = BACKEND_DIR / "notebooks" / "s01"


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
from autonomous_control.episode_timing import EpisodeTimingCollector  # noqa: E402
from s01_utils import training_workflow as tw  # noqa: E402

from _cadence_profiles import CadenceArmSpec, expected_train_updates  # noqa: E402
from _hparam_profiles import HparamArmSpec  # noqa: E402
from _profile_baseline import frozen_training_config, profile, shared_mpo_overrides  # noqa: E402
from _reward_fork import activate_reward_fork  # noqa: E402
from _run_guard import acquire_experiment_run_lock  # noqa: E402
from _sim_constants_fork import (  # noqa: E402
    DT_15,
    DT_15_AP2,
    apply_dt_profile,
    apply_experiment_dt_profile,
    dt_profile_for_arm,
    get_applied_dt_profile,
    require_dt_profile,
    write_dt_profile,
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
            "ml_overnight_runner_common_exp13",
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
EXPERIMENT_LOG = RESULTS_DIR / "learn_cadence_hparams.log"
EXPERIMENT_ID = "ml_mpo_learn_cadence_hparams"


def append_log(line: str) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
    with EXPERIMENT_LOG.open("a", encoding="utf-8") as fh:
        fh.write(f"[{stamp}] {line}\n")


def _dt_profile_for_cadence(arm: CadenceArmSpec) -> Any:
    if arm.controller_interval_s == 1.5:
        return DT_15
    if arm.controller_interval_s == 3.0 and arm.sim_dt_s == 1.5:
        return DT_15_AP2
    return dt_profile_for_arm(
        sim_dt_s=arm.sim_dt_s,
        controller_interval_s=arm.controller_interval_s,
        label=arm.dt_label(),
    )


def _apply_arm_dt(arm: CadenceArmSpec, *, train_episodes: int) -> dict[str, Any]:
    write_dt_profile(
        train_episodes=train_episodes,
        sim_dt_s=arm.sim_dt_s,
        controller_interval_s=arm.controller_interval_s,
        label=arm.dt_label(),
    )
    apply_experiment_dt_profile()
    dt_profile = _dt_profile_for_cadence(arm)
    apply_dt_profile(dt_profile)
    require_dt_profile(dt_profile, context=f"{EXPERIMENT_ID}:{arm.arm_id}")
    return get_applied_dt_profile() or {}


def _merged_mpo_overrides(*, hparam: HparamArmSpec | None = None) -> dict[str, Any]:
    merged = dict(shared_mpo_overrides())
    if hparam is not None:
        merged.update(hparam.mpo_overrides)
    return merged


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


def _sync_run_config(
    setup: tw.TrainingWorkflowSetup,
    *,
    arm_id: str,
    cadence: CadenceArmSpec,
    hparam: HparamArmSpec | None,
    mpo_overrides: dict[str, Any],
) -> None:
    from utils.ml_training.training_run_artifacts import write_config_snapshot

    config_path = setup.run_dir / "config.json"
    snapshot = json.loads(config_path.read_text(encoding="utf-8"))
    snapshot["mpo"] = tw._mpo_config_snapshot(setup.mpo_config)
    snapshot["experiment"] = {
        "experiment_id": EXPERIMENT_ID,
        "arm_id": arm_id,
        "attitude_request_mode": "torque",
        "reward_mode": "sparse",
        "cadence_ratio": cadence.ratio_label,
        "train_every_n_steps": cadence.train_every_n_steps,
        "updates_per_step": cadence.updates_per_step,
        "controller_interval_s": cadence.controller_interval_s,
        "hparam_arm": hparam.arm_id if hparam else None,
        "pre_fix_comparator": profile().get("ref_run_id"),
    }
    write_config_snapshot(setup.run_dir, snapshot)


def _learning_update_count(result: Any) -> int:
    stats = result.learning_stats or {}
    if hasattr(stats, "n_train_updates"):
        return int(stats.n_train_updates)
    if isinstance(stats, dict):
        return int(stats.get("n_train_updates", 0))
    return 0


def _build_setup(
    *,
    cadence: CadenceArmSpec,
    hparam: HparamArmSpec | None = None,
    run_id: str,
    train_episodes: int,
    smoke: bool,
    trim_artifacts: bool,
) -> tw.TrainingWorkflowSetup:
    mpo_overrides = _merged_mpo_overrides(hparam=hparam)
    dt_payload = _apply_arm_dt(cadence, train_episodes=train_episodes)

    set_warmup_fingerprint_extra(
        sim_dt_s=dt_payload.get("sim_dt_s"),
        controller_interval_s=dt_payload.get("controller_interval_s"),
        reward_mode="sparse",
        cadence_arm=cadence.arm_id,
        cadence_ratio=cadence.ratio_label,
        train_every_n_steps=cadence.train_every_n_steps,
        updates_per_step=cadence.updates_per_step,
        attitude_request_mode="torque",
        **mpo_overrides,
    )
    activate_warmup_fingerprint_patch()
    activate_reward_fork("sparse")

    cfg = frozen_training_config(
        run_id=run_id,
        train_episodes=train_episodes,
        rebuild_warmup_bundle_cache=True,
        train_every_n_steps=cadence.train_every_n_steps,
        updates_per_step=cadence.updates_per_step,
    )
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
    setup = _attach_mpo_agent(setup, replace(setup.mpo_config, **mpo_overrides))
    _sync_run_config(
        setup,
        arm_id=cadence.arm_id if hparam is None else hparam.arm_id,
        cadence=cadence,
        hparam=hparam,
        mpo_overrides=mpo_overrides,
    )
    return setup


def run_timing_episode(
    cadence: CadenceArmSpec,
    *,
    rebuild_warmup_cache: bool = False,
) -> dict[str, Any]:
    """One timed train episode after warmup (Track A0 micro-benchmark)."""
    stamp = datetime.now(timezone.utc).strftime("%H-%M-%S")
    setup = _build_setup(
        cadence=cadence,
        run_id=f"ml_mpo_learn_cadence_timing_{cadence.arm_id}_{stamp}",
        train_episodes=1,
        smoke=False,
        trim_artifacts=True,
    )
    if rebuild_warmup_cache:
        pass  # rebuild already requested in _build_setup

    from autonomous_control.config.randomness import derive_seed
    import numpy as np

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
        np_rng=np.random.default_rng(derive_seed(7, f"exp13/warmup/{cadence.arm_id}", 0)),
    )
    warmup_wall_s = time.perf_counter() - t0

    if len(setup.agent.buffer) == 0:
        raise RuntimeError(f"Empty buffer after warmup for {cadence.arm_id}")

    timing = EpisodeTimingCollector()
    t1 = time.perf_counter()
    result = setup.runner.run_serial(
        setup.agent,
        mode="train",
        episode_idx=0,
        collect_states=False,
        show_training_context=False,
        train_updates_per_step=cadence.updates_per_step,
        train_every_n_steps=cadence.train_every_n_steps,
        feature_config=setup.feature_config,
        observation_layout=setup.observation_layout,
        np_rng=np.random.default_rng(derive_seed(7, f"exp13/train/{cadence.arm_id}", 0)),
        timing=timing,
    )
    episode_wall_s = time.perf_counter() - t1
    n_updates = _learning_update_count(result)
    report = timing.report(
        extra={
            "arm_id": cadence.arm_id,
            "ratio_label": cadence.ratio_label,
            "warmup_wall_s": warmup_wall_s,
            "episode_wall_s": episode_wall_s,
            "n_train_updates": n_updates,
            "n_sim_steps": int(result.steps),
            "episode_return": float(result.episode_return),
            "train_every_n_steps": cadence.train_every_n_steps,
            "updates_per_step": cadence.updates_per_step,
            "controller_interval_s": cadence.controller_interval_s,
            "run_dir": str(setup.run_dir),
        }
    )
    report["expected_train_updates"] = expected_train_updates(
        int(timing.n_controller_stores or 0),
        train_every=cadence.train_every_n_steps,
        updates=cadence.updates_per_step,
    )
    return report


def run_cadence_arm(
    cadence: CadenceArmSpec,
    *,
    hparam: HparamArmSpec | None = None,
    show_progress: bool = False,
    trim_artifacts: bool = False,
    train_episodes: int | None = None,
    smoke: bool = False,
) -> dict[str, Any]:
    arm_id = hparam.arm_id if hparam is not None else cadence.arm_id
    if not smoke:
        acquire_experiment_run_lock(script=arm_id)
    append_log(f"START arm={arm_id} cadence={cadence.ratio_label} smoke={smoke}")

    n_train = 1 if smoke else int(
        train_episodes if train_episodes is not None else profile().get("workflow", {}).get("train_episodes", 50)
    )
    stamp = datetime.now(timezone.utc).strftime("%H-%M-%S")
    run_suffix = "smoke" if smoke else arm_id
    setup = _build_setup(
        cadence=cadence,
        hparam=hparam,
        run_id=f"ml_mpo_learn_cadence_{run_suffix}_{stamp}",
        train_episodes=n_train,
        smoke=smoke,
        trim_artifacts=trim_artifacts,
    )
    mpo_overrides = _merged_mpo_overrides(hparam=hparam)
    applied = get_applied_dt_profile() or {}

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
            np_rng=np.random.default_rng(derive_seed(7, f"exp13/smoke/{arm_id}", 0)),
        )
        if len(setup.agent.buffer) == 0:
            raise RuntimeError("Smoke warmup produced empty buffer.")

        timing = EpisodeTimingCollector()
        train_result = setup.runner.run_serial(
            setup.agent,
            mode="train",
            episode_idx=0,
            collect_states=False,
            show_training_context=False,
            train_updates_per_step=cadence.updates_per_step,
            train_every_n_steps=cadence.train_every_n_steps,
            feature_config=setup.feature_config,
            observation_layout=setup.observation_layout,
            np_rng=np.random.default_rng(derive_seed(7, f"exp13/smoke_train/{arm_id}", 0)),
            timing=timing,
        )
        n_updates = _learning_update_count(train_result)
        if n_updates <= 0:
            raise RuntimeError(f"Smoke train episode produced n_train_updates={n_updates}")

        timing_report = timing.report()
        return {
            "passed": True,
            "arm_id": arm_id,
            "cadence_arm": cadence.arm_id,
            "ratio_label": cadence.ratio_label,
            "warmup_return": float(warmup.episode_return),
            "train_return": float(train_result.episode_return),
            "train_steps": int(train_result.steps),
            "n_train_updates": n_updates,
            "expected_train_updates_approx": expected_train_updates(
                int(timing.n_controller_stores or 0),
                train_every=cadence.train_every_n_steps,
                updates=cadence.updates_per_step,
            ),
            "timing": timing_report,
            "cadence": {
                "train_every_n_steps": cadence.train_every_n_steps,
                "updates_per_step": cadence.updates_per_step,
                "controller_interval_s": cadence.controller_interval_s,
            },
            "dt_profile": applied,
            "mpo_overrides": mpo_overrides,
            "run_dir": str(setup.run_dir),
        }

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
        agent_kind="mpo",
    )
    debug_eps = [
        _episode_debug_row(ep, episode_idx=i) for i, ep in enumerate(workflow_result.train_results)
    ]
    last_updates = int(_stat_val(workflow_result.train_results[-1].learning_stats, "n_train_updates") or 0)

    kpis = {
        "arm_id": arm_id,
        "cadence_arm": cadence.arm_id,
        "ratio_label": cadence.ratio_label,
        "hypothesis_id": "learn_cadence_hparams",
        "reward_mode": "sparse",
        "attitude_request_mode": "torque",
        "cadence": {
            "train_every_n_steps": cadence.train_every_n_steps,
            "updates_per_step": cadence.updates_per_step,
            "controller_interval_s": cadence.controller_interval_s,
        },
        "hparam_arm": hparam.arm_id if hparam else None,
        "mpo_overrides": mpo_overrides,
        "run_dir": str(setup.run_dir),
        "wall_s": wall_s,
        "dt_profile": applied,
        "agent_kind": "mpo",
        "train_returns": train_returns,
        "eval_returns": eval_returns,
        "eval_return_mean": signal["eval_return_mean"],
        "learning_signal": signal,
        "learning_stats": learning_stats,
        "n_train_updates_last_ep": last_updates,
        "debug_episodes": debug_eps,
        "pre_fix_comparator": profile().get("ref_run_id"),
    }
    append_log(
        f"DONE {arm_id} learning_mode={signal['learning_mode']} "
        f"train_best={max(train_returns) if train_returns else 0:.1f} "
        f"eval_mean={signal.get('eval_return_mean', 0):.1f} wall_s={wall_s:.1f}"
    )
    return kpis


def _stat_val(stats: Any, key: str) -> Any:
    if stats is None:
        return None
    if hasattr(stats, key):
        return getattr(stats, key)
    if isinstance(stats, dict):
        return stats.get(key)
    return None


__all__ = [
    "EXPERIMENT_ID",
    "RESULTS_DIR",
    "append_log",
    "run_cadence_arm",
    "run_timing_episode",
    "write_hypothesis_result",
]
