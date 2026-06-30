"""Run Exp 7 penalty_on arm — SAC sparse vector + budget-exhausted shutter penalty."""

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

from _budget_frozen import (  # noqa: E402
    EXPERIMENT_SEED,
    TRAIN_EPISODES_DEFAULT,
    frozen_training_config,
    sac_mpo_config_overrides,
)
from _reward_fork import activate_reward_fork, budget_penalty_enabled  # noqa: E402
from _run_guard import acquire_experiment_run_lock  # noqa: E402
from _sim_constants_fork import (  # noqa: E402
    FIXED_BUDGET_DT,
    apply_experiment_dt_profile,
    get_applied_dt_profile,
    require_dt_profile,
)
from _runner_common import (  # noqa: E402
    RESULTS_DIR,
    baseline_ref1_metadata,
    count_post_budget_shutter_cmds,
    evaluate_learning_mode,
    _learning_stats_summary,
)
from environment_definition.constants.SATELLITE import MAX_PRIMARY_CAPTURES_PER_ORBIT  # noqa: E402

import numpy as np  # noqa: E402
from _warmup_fingerprint_patch import (  # noqa: E402
    activate_warmup_fingerprint_patch,
    set_warmup_fingerprint_extra,
)

EXPERIMENT_ID = "ml_sac_vector_budget_penalty"
ARM_ID = "penalty_on"
HYPOTHESIS_ID = "sac_vector_budget_penalty"
EXPERIMENT_LOG = RESULTS_DIR / "budget_penalty.log"


def append_log(line: str) -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
    with EXPERIMENT_LOG.open("a", encoding="utf-8") as fh:
        fh.write(f"[{stamp}] {line}\n")


def _load_sac_agent():
    _sac_spec = importlib.util.spec_from_file_location(
        "ml_budget_sac_agent_fork",
        OVERNIGHT_ROOT / "agents" / "sac_agent_fork.py",
    )
    assert _sac_spec and _sac_spec.loader
    _sac_mod = importlib.util.module_from_spec(_sac_spec)
    _sac_spec.loader.exec_module(_sac_mod)
    return _sac_mod.SACAgent


def _patch_run_config(
    run_dir: Path,
    *,
    dt_profile: dict[str, Any],
    enable_tensorboard: bool,
) -> None:
    config_path = run_dir / "config.json"
    if not config_path.is_file():
        raise FileNotFoundError(f"Missing run config: {config_path}")
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    payload["experiment"] = {
        "experiment_id": EXPERIMENT_ID,
        "arm_id": ARM_ID,
        "hypothesis_id": HYPOTHESIS_ID,
        "attitude_request_mode": "vector",
        "agent_kind": "sac",
        "reward_mode": "sparse",
        "budget_exhausted_shutter_penalty": budget_penalty_enabled(),
        "baseline_comparison": baseline_ref1_metadata(),
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


def run_penalty_on(
    *,
    show_progress: bool = False,
    train_episodes: int | None = None,
    trim_artifacts: bool = False,
    enable_tensorboard: bool = True,
) -> dict[str, Any]:
    """Single treatment arm; compare KPIs to Exp 4 Ref1 baseline (read-only)."""
    acquire_experiment_run_lock(script=ARM_ID)
    append_log(f"START {ARM_ID} tensorboard={enable_tensorboard}")

    dt_profile = apply_experiment_dt_profile()
    require_dt_profile(FIXED_BUDGET_DT, context=f"{EXPERIMENT_ID}:{ARM_ID}")
    applied = get_applied_dt_profile() or {}

    set_warmup_fingerprint_extra(
        sim_dt_s=dt_profile.get("sim_dt_s"),
        controller_interval_s=dt_profile.get("controller_interval_s"),
        reward_mode="sparse",
        budget_arm=ARM_ID,
        attitude_request_mode="vector",
        budget_exhausted_shutter_penalty=True,
    )
    activate_warmup_fingerprint_patch()
    activate_reward_fork(budget_exhausted_shutter_penalty=True)

    n_train = int(
        train_episodes if train_episodes is not None else dt_profile.get("train_episodes", TRAIN_EPISODES_DEFAULT)
    )
    stamp = datetime.now(timezone.utc).strftime("%H-%M-%S")
    cfg = frozen_training_config(
        run_id=f"ml_sac_vector_budget_{stamp}",
        train_episodes=n_train,
        rebuild_warmup_bundle_cache=True,
        experiment_name="sac vector budget penalty",
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
    setup = replace(setup, mpo_config=sac_mpo_config_overrides(setup.mpo_config))
    env = _make_env(setup)
    SACAgent = _load_sac_agent()
    setup = replace(setup, agent=SACAgent(env, config=setup.mpo_config))

    _patch_run_config(setup.run_dir, dt_profile=applied, enable_tensorboard=enable_tensorboard)

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
    if enable_tensorboard and not tensorboard_ok:
        raise RuntimeError(f"TensorBoard logging failed: missing event files in {tb_dir}")
    if enable_tensorboard:
        from utils.ml_training.tensorboard_run_writer import verify_train_return_parity

        verify_train_return_parity(setup.run_dir)

    kpis = {
        "arm_id": ARM_ID,
        "hypothesis_id": HYPOTHESIS_ID,
        "run_dir": str(setup.run_dir),
        "tensorboard_dir": str(tb_dir) if enable_tensorboard else None,
        "tensorboard_ok": tensorboard_ok,
        "attitude_request_mode": "vector",
        "agent_kind": "sac",
        "reward_mode": "sparse",
        "budget_exhausted_shutter_penalty": True,
        "wall_s": wall_s,
        "dt_profile": dt_profile,
        "warmup_returns": warmup_returns,
        "train_returns": train_returns,
        "eval_returns": eval_returns,
        "eval_return_mean": signal["eval_return_mean"],
        "learning_signal": signal,
        "post_budget_shutter_cmds": shutter_stats,
        "baseline_ref1": baseline_ref1_metadata(),
        "seed": EXPERIMENT_SEED,
    }
    append_log(
        f"DONE {ARM_ID} learning_mode={signal['learning_mode']} "
        f"eval_mean={signal['eval_return_mean']} post_budget_cmds={shutter_stats['total']}"
    )
    return kpis


def finalize_penalty_on_from_run(
    run_dir: Path,
    *,
    show_progress: bool = False,
    export_videos: bool = True,
    replay_train_for_shutter_stats: bool = False,
) -> dict[str, Any]:
    """Recover KPI JSON (and optional MP4s) when training finished but post-processing crashed."""
    from utils.ml_training.training_run_artifacts import read_episodes_csv

    run_dir = run_dir.resolve()
    ckpt = tw.checkpoint_path(run_dir)
    if not ckpt.is_file():
        raise FileNotFoundError(f"Missing checkpoint: {ckpt}")
    if not (run_dir / "episodes.csv").is_file():
        raise FileNotFoundError(f"Missing episodes.csv in {run_dir}")

    append_log(f"FINALIZE {ARM_ID} run_dir={run_dir}")

    apply_experiment_dt_profile()
    require_dt_profile(FIXED_BUDGET_DT, context=f"{EXPERIMENT_ID}:finalize")
    activate_warmup_fingerprint_patch()
    activate_reward_fork(budget_exhausted_shutter_penalty=True)

    episode_rows = read_episodes_csv(run_dir)
    train_returns = [float(r["episode_return"]) for r in episode_rows if r.get("phase") == "train"]
    eval_returns = [float(r["episode_return"]) for r in episode_rows if r.get("phase") == "eval"]
    warmup_returns = [float(r["episode_return"]) for r in episode_rows if r.get("phase") == "warmup"]

    summary_path = run_dir / "summary_metrics.json"
    summary_metrics = (
        json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.is_file() else {}
    )
    train_shutter_cmd_count = (
        summary_metrics.get("action_diagnostics", {})
        .get("train", {})
        .get("shutter_cmd_count")
    )

    train_results: list[Any] = []
    if replay_train_for_shutter_stats:
        from autonomous_control.config.randomness import derive_seed

        setup = tw.build_training_workflow_setup(existing_run_dir=run_dir)
        setup = replace(setup, mpo_config=sac_mpo_config_overrides(setup.mpo_config))
        env = _make_env(setup)
        SACAgent = _load_sac_agent()
        setup = replace(setup, agent=SACAgent(env, config=setup.mpo_config))
        tw.load_agent_checkpoint(setup.agent, ckpt)

        train_rows = [r for r in episode_rows if r.get("phase") == "train"]
        for row in train_rows:
            ep_idx = int(row["episode_idx"])
            if show_progress:
                print(f"Replay train ep {ep_idx + 1}/{len(train_rows)} for shutter stats...")
            train_results.append(
                setup.runner.run_serial(
                    setup.agent,
                    mode="train",
                    feature_config=setup.feature_config,
                    observation_layout=setup.observation_layout,
                    episode_idx=ep_idx,
                    collect_states=False,
                    train_updates_per_step=0,
                    early_stop_on_budget_exhausted=False,
                    show_simulation_info=False,
                    np_rng=np.random.default_rng(derive_seed(setup.config.seed, "train_episode", ep_idx)),
                )
            )

    if train_results:
        shutter_stats = count_post_budget_shutter_cmds(train_results)
        learning_stats = _learning_stats_summary(setup.agent, train_results)
    else:
        shutter_stats = {
            "total": None,
            "per_episode": {},
            "budget_per_episode": int(MAX_PRIMARY_CAPTURES_PER_ORBIT),
            "train_shutter_cmd_count": train_shutter_cmd_count,
            "note": "post_budget counts need train simulation_series; set replay_train_for_shutter_stats=True to recompute.",
        }
        learning_stats = {}
    signal = evaluate_learning_mode(train_returns, eval_returns, learning_stats=learning_stats)

    tb_dir = run_dir / "tensorboard"
    tensorboard_ok = tb_dir.is_dir() and any(tb_dir.glob("events.out.tfevents.*"))

    if export_videos:
        workflow_cfg = json.loads((run_dir / "config.json").read_text(encoding="utf-8")).get(
            "workflow", {}
        )
        tw.export_artifacts_from_checkpoint(
            run_dir,
            train_episode_videos=int(workflow_cfg.get("train_episode_videos", 3)),
            eval_episode_videos=int(workflow_cfg.get("eval_episode_videos", 2)),
            export_episode_reward_plots=bool(workflow_cfg.get("export_episode_reward_plots", True)),
            show_progress=show_progress,
        )

    kpis = {
        "arm_id": ARM_ID,
        "hypothesis_id": HYPOTHESIS_ID,
        "run_dir": str(run_dir),
        "tensorboard_dir": str(tb_dir),
        "tensorboard_ok": tensorboard_ok,
        "attitude_request_mode": "vector",
        "agent_kind": "sac",
        "reward_mode": "sparse",
        "budget_exhausted_shutter_penalty": True,
        "wall_s": None,
        "dt_profile": get_applied_dt_profile() or {},
        "warmup_returns": warmup_returns,
        "train_returns": train_returns,
        "eval_returns": eval_returns,
        "eval_return_mean": signal["eval_return_mean"],
        "learning_signal": signal,
        "post_budget_shutter_cmds": shutter_stats,
        "baseline_ref1": baseline_ref1_metadata(),
        "seed": EXPERIMENT_SEED,
        "finalized_from_crash": True,
    }
    append_log(
        f"FINALIZED {ARM_ID} learning_mode={signal['learning_mode']} "
        f"eval_mean={signal['eval_return_mean']} post_budget_cmds={shutter_stats['total']}"
    )
    return kpis


__all__ = ["ARM_ID", "EXPERIMENT_ID", "append_log", "finalize_penalty_on_from_run", "run_penalty_on"]
