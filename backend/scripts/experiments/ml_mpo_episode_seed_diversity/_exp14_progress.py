"""Exp 14 CLI progress: env banners, simulation panels, tqdm (matches training_workflow)."""

from __future__ import annotations

import sys
from typing import Any

from tqdm.auto import tqdm

from autonomous_control.training_progress_display import (
    TrainingProgressConfig,
    TrainingProgressDisplay,
)
from simulation.simulation_info import print_simulation_info

from _exp14_runner_common import EXPERIMENT_ID
from _episode_loop_fork import Exp14EpisodeResult, run_exp14_episode


def _is_safe_progress_terminal() -> bool:
    """Return True when nested tqdm updates are safe for this stdout handle."""
    stdout = sys.stdout
    is_tty = bool(getattr(stdout, "isatty", lambda: False)())
    if not is_tty:
        return False
    encoding = (getattr(stdout, "encoding", "") or "").lower()
    if encoding and "utf" not in encoding:
        return False
    return True


def print_environment_banner(
    *,
    env_index: int | None,
    mission_seed: int,
    cloud_seed: int,
    label: str | None = None,
) -> None:
    """Print env identity before warmup/train on a new setup draw."""
    if env_index is not None:
        head = f"ENV {int(env_index) + 1}"
    else:
        head = label or "ENV (screen fixed)"
    line = (
        f"=== {head} | mission_seed={mission_seed} cloud_seed={cloud_seed} "
        f"| experiment={EXPERIMENT_ID} ==="
    )
    tqdm.write(line)


def make_progress_display(
    agent: Any,
    *,
    show_progress: bool,
    live_feed_interval_steps: int = 400,
) -> TrainingProgressDisplay | None:
    if not show_progress:
        return None
    if not _is_safe_progress_terminal():
        return None
    return TrainingProgressDisplay(
        config=TrainingProgressConfig(
            live_feed_interval_steps=int(live_feed_interval_steps),
            show_live_stats=True,
            show_camera_feed=False,
        ),
        agent=agent,
    )


def print_episode_summary(
    *,
    mode: str,
    episode_idx: int,
    episode_return: float,
    mission_score: float,
    steps: int,
    progress_display: TrainingProgressDisplay | None = None,
) -> None:
    msg = (
        f"[{mode}] ep {episode_idx + 1}: "
        f"return={episode_return:.2f} score={mission_score:.4f} steps={steps}"
    )
    if progress_display is not None:
        progress_display.write(msg)
    else:
        tqdm.write(msg)


def print_simulation_info_panel(
    stepper: Any,
    *,
    simulation_config: Any,
    tau_max_nm: float,
    agent: Any,
    mode: str,
    phase_episode_total: int | None,
    experiment_name: str | None = None,
) -> None:
    print_simulation_info(
        stepper,
        simulation_config=simulation_config,
        tau_max_nm=tau_max_nm,
        agent=agent,
        episode_mode=mode,
        experiment_name=experiment_name or EXPERIMENT_ID,
        phase_episode_total=phase_episode_total,
    )


def run_phase_episodes(
    setup: Any,
    ctx: Any,
    *,
    mode: str,
    episode_count: int,
    progress_display: TrainingProgressDisplay | None,
    show_progress: bool,
    phase_bar_desc: str,
    experiment_name: str | None = None,
) -> list[Exp14EpisodeResult]:
    """Run warmup/train/eval block with phase + step tqdm (training_workflow pattern)."""
    safe_progress = bool(show_progress and _is_safe_progress_terminal())
    results: list[Exp14EpisodeResult] = []
    phase_bar = tqdm(
        total=int(episode_count),
        desc=phase_bar_desc,
        unit="ep",
        disable=not safe_progress,
        position=0,
    )
    if progress_display is not None:
        progress_display.set_phase_bar(phase_bar)
        progress_display.set_phase_episode_total(int(episode_count))
    try:
        for ep in range(int(episode_count)):
            result = run_exp14_episode(
                setup,
                ctx.agent,
                mode=mode,
                feature_config=ctx.feature_config,
                observation_layout=ctx.observation_layout,
                episode_idx=ep,
                reward_config=ctx.reward_config,
                show_progress=safe_progress,
                show_config_panel=ep == 0,
                progress_display=progress_display,
                phase_episode_total=int(episode_count),
                experiment_name=experiment_name,
            )
            results.append(result)
            if mode in {"train", "eval"}:
                postfix = {"reward": f"{result.episode_return:.1f}", "score": f"{result.mission_score:.3f}"}
                phase_bar.set_postfix(**postfix)
                print_episode_summary(
                    mode=mode,
                    episode_idx=ep,
                    episode_return=result.episode_return,
                    mission_score=result.mission_score,
                    steps=result.steps,
                    progress_display=progress_display,
                )
            phase_bar.update(1)
    finally:
        phase_bar.close()
    if progress_display is not None and mode == "warmup" and results:
        progress_display.show_warmup_summary(results)
    return results


__all__ = [
    "make_progress_display",
    "print_environment_banner",
    "print_episode_summary",
    "print_simulation_info_panel",
    "run_phase_episodes",
]
