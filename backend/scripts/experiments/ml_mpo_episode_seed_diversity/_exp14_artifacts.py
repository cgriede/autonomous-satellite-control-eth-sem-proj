"""Export warmup/train/eval videos and latent/applied reward plots for Exp 14."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tqdm.auto import tqdm

from _episode_loop_fork import Exp14EpisodeResult
from _exp14_runner_common import RESULTS_DIR, append_log

_BACKEND = Path(__file__).resolve().parents[3]
if str(_BACKEND) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(_BACKEND))

from utils.ml_training.training_run_artifacts import (  # noqa: E402
    ensure_run_layout,
    export_episode_diagnostics_plots,
    export_training_episode_video_sync,
    plan_standard_training_artifacts,
    rank_episodes_by_return,
    write_artifacts_manifest,
)


def artifact_root(*, arm_id: str | None = None, label: str = "screen") -> Path:
    root = RESULTS_DIR / "artifacts" / label
    if arm_id:
        return root / arm_id
    return root


def export_latent_applied_reward_plot(
    result: Exp14EpisodeResult,
    out_path: Path,
    *,
    title: str,
) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from render._plot_style import save_dashboard_figure, set_dashboard_xlabel, style_dashboard_figure
    from render.episode_series_plotting import draw_episode_reward_axes

    series = result.simulation_series
    if series is None:
        raise ValueError("Episode result has no simulation_series")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(1, 1, figsize=(10.0, 3.2))
    style_dashboard_figure(fig, title=title)
    draw_episode_reward_axes(ax, series, title=None, show_legend=True)
    set_dashboard_xlabel(ax, "time [s]")
    save_dashboard_figure(fig, out_path, dpi=120)
    plt.close(fig)
    return out_path


def export_warmup_artifacts(
    warmup_results: list[Exp14EpisodeResult],
    out_dir: Path,
    *,
    warmup_videos: int = 1,
    export_reward_plots: bool = True,
    show_progress: bool = False,
) -> dict[str, Any]:
    """Export top warmup episode video(s) and latent/applied reward plot(s)."""
    if not warmup_results:
        return {"artifacts": [], "errors": []}

    out_dir.mkdir(parents=True, exist_ok=True)
    layout = ensure_run_layout(out_dir)
    video_limit = max(0, int(warmup_videos))
    ranked_for_video = rank_episodes_by_return(
        warmup_results, phase="warmup", limit=video_limit if video_limit > 0 else 0
    )
    ranked_for_plot = rank_episodes_by_return(warmup_results, phase="warmup", limit=1)
    plot_indices = {r.episode_idx for r in ranked_for_plot}
    video_indices = {r.episode_idx for r in ranked_for_video}
    work_indices = plot_indices | video_indices
    ranked_all = rank_episodes_by_return(warmup_results, phase="warmup", limit=len(warmup_results))
    work_ranked = [r for r in ranked_all if r.episode_idx in work_indices]
    artifacts: list[dict[str, Any]] = []
    errors: list[str] = []

    for item in work_ranked:
        result = warmup_results[item.episode_idx]
        series = result.simulation_series
        if series is None:
            errors.append(f"warmup ep {item.episode_idx + 1}: missing simulation_series")
            continue

        video_path = layout["videos"] / f"warmup_ep_{item.episode_idx}_rank{item.rank}.mp4"
        reward_path = layout["episodes"] / f"warmup_ep_{item.episode_idx}_rank{item.rank}_latent_applied.png"
        label = f"warmup ep {item.episode_idx + 1} (rank {item.rank}, return={item.episode_return:.1f})"

        if export_reward_plots and item.episode_idx in plot_indices:
            try:
                export_latent_applied_reward_plot(result, reward_path, title=label)
                artifacts.append(
                    {
                        "phase": "warmup",
                        "kind": "reward_plot",
                        "episode_idx": item.episode_idx,
                        "rank": item.rank,
                        "path": str(reward_path),
                    }
                )
                if show_progress:
                    tqdm.write(f"  reward plot → {reward_path}")
            except Exception as exc:
                errors.append(f"{label} reward plot: {exc}")

        if item.episode_idx in video_indices:
            try:
                if show_progress:
                    tqdm.write(f"  encoding video → {video_path} (slow)")
                export_training_episode_video_sync(series, video_path)
                artifacts.append(
                    {
                        "phase": "warmup",
                        "kind": "video",
                        "episode_idx": item.episode_idx,
                        "rank": item.rank,
                        "path": str(video_path),
                    }
                )
                if show_progress:
                    tqdm.write(f"  video → {video_path}")
            except Exception as exc:
                errors.append(f"{label} video: {exc}")

    return {"artifacts": artifacts, "errors": errors, "out_dir": str(out_dir)}


def export_screen_arm_artifacts(
    *,
    arm_id: str,
    warmup_results: list[Exp14EpisodeResult] | None = None,
    train_results: list[Exp14EpisodeResult] | None = None,
    eval_results: list[Exp14EpisodeResult] | None = None,
    train_episode_videos: int = 3,
    eval_episode_videos: int = 2,
    warmup_episode_videos: int = 1,
    export_episode_reward_plots: bool = True,
    show_progress: bool = False,
) -> dict[str, Any]:
    """Export warmup + top train/eval artifacts for one screen arm."""
    out_dir = artifact_root(arm_id=arm_id, label="screen")
    all_artifacts: list[dict[str, Any]] = []
    errors: list[str] = []

    if warmup_results:
        warmup_out = export_warmup_artifacts(
            warmup_results,
            out_dir,
            warmup_videos=warmup_episode_videos,
            export_reward_plots=export_episode_reward_plots,
            show_progress=show_progress,
        )
        all_artifacts.extend(warmup_out.get("artifacts", []))
        errors.extend(warmup_out.get("errors", []))

        if export_episode_reward_plots:
            try:
                diag = export_episode_diagnostics_plots(
                    out_dir,
                    warmup_results=warmup_results,
                    train_results=train_results,
                    eval_results=eval_results,
                )
                for path in diag.get("warmup", []):
                    all_artifacts.append({"phase": "warmup", "kind": "diagnostics", "path": str(path)})
            except Exception as exc:
                errors.append(f"warmup diagnostics page: {exc}")

    train_list = list(train_results or [])
    eval_list = list(eval_results or [])
    if train_list or eval_list:
        reward_jobs, video_jobs, manifest = plan_standard_training_artifacts(
            out_dir,
            train_results=train_list,
            eval_results=eval_list,
            train_episode_videos=int(train_episode_videos),
            eval_episode_videos=int(eval_episode_videos),
            export_episode_reward_plots=bool(export_episode_reward_plots),
        )
        from utils.ml_training.training_run_artifacts import plot_episode_reward_timeline

        for series, label, reward_path in reward_jobs:
            try:
                plot_episode_reward_timeline(series, label=label, out_path=reward_path)
                if show_progress:
                    tqdm.write(f"  reward timeline → {reward_path}")
            except Exception as exc:
                errors.append(f"{label} timeline: {exc}")

        for series, video_path in video_jobs:
            try:
                if show_progress:
                    tqdm.write(f"  encoding video → {video_path} (slow)")
                export_training_episode_video_sync(series, video_path)
                if show_progress:
                    tqdm.write(f"  video → {video_path}")
            except Exception as exc:
                errors.append(f"{video_path.name} video: {exc}")

        all_artifacts.extend(manifest)
        write_artifacts_manifest(out_dir, manifest)

    payload = {"arm_id": arm_id, "out_dir": str(out_dir), "artifacts": all_artifacts, "errors": errors}
    if show_progress and all_artifacts:
        append_log(f"Artifacts exported → {out_dir} ({len(all_artifacts)} files)")
    if errors and show_progress:
        append_log(f"Artifact export errors ({len(errors)}): {errors[0]}")
    return payload


__all__ = [
    "artifact_root",
    "export_latent_applied_reward_plot",
    "export_screen_arm_artifacts",
    "export_warmup_artifacts",
]
