"""Run-directory layout, CSV/JSON snapshots, and matplotlib training artifacts."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any, Literal

import numpy as np

from utils.ml_training.ml_training_utils import telemetry_dir

EpisodePhase = Literal["warmup", "train", "eval"]

EPISODES_PER_DIAGNOSTICS_PAGE = 10

EPISODE_CSV_FIELDS: tuple[str, ...] = (
    "global_idx",
    "phase",
    "episode_idx",
    "episode_return",
    "avg_reward",
    "steps",
    "n_train_updates",
    "q_loss_mean",
    "pi_loss_mean",
    "kl_mean",
    "kl_mu_mean",
    "kl_sigma_mean",
    "eta_mean",
    "buffer_size",
    "in_exploration",
)


def ensure_run_layout(run_dir: Path) -> dict[str, Path]:
    """Create standard subdirs; return path map."""
    run_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "root": run_dir,
        "plots": run_dir / "plots",
        "episodes": run_dir / "episodes",
        "videos": run_dir / "videos",
        "telemetry": telemetry_dir(run_dir),
    }
    for key in ("plots", "episodes", "videos"):
        paths[key].mkdir(parents=True, exist_ok=True)
    return paths


def artifact_paths_map(run_dir: Path) -> dict[str, Path]:
    layout = ensure_run_layout(run_dir)
    return {
        "config": run_dir / "config.json",
        "episodes_csv": run_dir / "episodes.csv",
        "summary_json": run_dir / "summary_metrics.json",
        "artifacts_manifest": run_dir / "artifacts_manifest.json",
        "returns_plot": layout["plots"] / "returns_by_episode.png",
        "learning_curves_plot": layout["plots"] / "learning_curves.png",
        # Legacy notebook aliases (rank-1 train / best eval reward timelines).
        "train_last_reward_plot": layout["episodes"] / "train_last_reward.png",
        "eval_best_reward_plot": layout["episodes"] / "eval_best_reward.png",
        "eval_best_video": layout["videos"] / "eval_best.mp4",
    }


@dataclass(frozen=True)
class EpisodeDiagnosticSpec:
    phase: str
    episode_idx: int
    label: str
    series: Any


def _episode_series(result: Any) -> Any | None:
    return getattr(result, "simulation_series", None)


def plan_episode_diagnostic_specs(
    *,
    warmup_results: list[Any] | None = None,
    train_results: list[Any] | None = None,
    eval_results: list[Any] | None = None,
) -> dict[str, list[EpisodeDiagnosticSpec]]:
    """Warmup: last episode only; train/eval: all episodes with series."""
    specs: dict[str, list[EpisodeDiagnosticSpec]] = {
        "warmup": [],
        "train": [],
        "eval": [],
    }

    warmup = list(warmup_results or [])
    if warmup:
        for idx, result in enumerate(warmup):
            series = _episode_series(result)
            if series is None:
                continue
            spec = EpisodeDiagnosticSpec(
                phase="warmup",
                episode_idx=idx,
                label=f"warmup ep {idx + 1}",
                series=series,
            )
            specs["warmup"].append(spec)
        if len(specs["warmup"]) > 1:
            specs["warmup"] = [specs["warmup"][-1]]

    for phase, results in (("train", train_results), ("eval", eval_results)):
        for idx, result in enumerate(list(results or [])):
            series = _episode_series(result)
            if series is None:
                continue
            specs[phase].append(
                EpisodeDiagnosticSpec(
                    phase=phase,
                    episode_idx=idx,
                    label=f"{phase} ep {idx + 1}",
                    series=series,
                )
            )
    return specs


def plot_episode_diagnostics_page(
    specs: list[EpisodeDiagnosticSpec],
    out_path: Path,
    *,
    page_title: str,
) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from render._plot_style import save_dashboard_figure, set_dashboard_xlabel, style_dashboard_figure
    from render.episode_series_plotting import draw_episode_reward_axes, draw_episode_torque_axes

    if not specs:
        raise ValueError("No episode diagnostic specs to plot.")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    n = len(specs)
    fig, axes = plt.subplots(n, 2, figsize=(12.0, max(2.2, 1.9 * n)), squeeze=False)
    style_dashboard_figure(fig, title=page_title)

    for row, spec in enumerate(specs):
        reward_ax = axes[row, 0]
        torque_ax = axes[row, 1]
        show_legend = row == 0
        draw_episode_reward_axes(
            reward_ax,
            spec.series,
            title=spec.label,
            show_legend=show_legend,
        )
        draw_episode_torque_axes(
            torque_ax,
            spec.series,
            title=spec.label,
            show_legend=show_legend,
        )
        if row < n - 1:
            reward_ax.tick_params(labelbottom=False)
            torque_ax.tick_params(labelbottom=False)
        else:
            set_dashboard_xlabel(reward_ax, "time [s]")
            set_dashboard_xlabel(torque_ax, "time [s]")

    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.98))
    save_dashboard_figure(fig, out_path, dpi=120)
    plt.close(fig)
    return out_path


def export_episode_diagnostics_plots(
    run_dir: Path,
    *,
    warmup_results: list[Any] | None = None,
    train_results: list[Any] | None = None,
    eval_results: list[Any] | None = None,
) -> dict[str, list[Path]]:
    layout = ensure_run_layout(run_dir)
    plots_dir = layout["plots"]
    phase_specs = plan_episode_diagnostic_specs(
        warmup_results=warmup_results,
        train_results=train_results,
        eval_results=eval_results,
    )
    written: dict[str, list[Path]] = {"warmup": [], "train": [], "eval": []}

    for phase, specs in phase_specs.items():
        if not specs:
            continue
        page_size = EPISODES_PER_DIAGNOSTICS_PAGE
        for page_idx in range(0, len(specs), page_size):
            chunk = specs[page_idx : page_idx + page_size]
            page_num = page_idx // page_size + 1
            total_pages = (len(specs) + page_size - 1) // page_size
            if total_pages == 1:
                filename = f"{phase}_episode_diagnostics.png"
            else:
                filename = f"{phase}_episode_diagnostics_p{page_num:02d}.png"
            out_path = plots_dir / filename
            title = f"{phase} episode diagnostics"
            if total_pages > 1:
                title = f"{title} (page {page_num}/{total_pages})"
            plot_episode_diagnostics_page(chunk, out_path, page_title=title)
            written[phase].append(out_path)
    return written


@dataclass(frozen=True)
class RankedEpisode:
    phase: EpisodePhase
    episode_idx: int
    rank: int
    episode_return: float


def _episode_return_value(result: Any) -> float:
    return float(getattr(result, "episode_return", 0.0))


def rank_episodes_by_return(
    results: list[Any],
    *,
    phase: EpisodePhase,
    limit: int,
) -> list[RankedEpisode]:
    if limit <= 0 or not results:
        return []
    ranked = sorted(
        enumerate(results),
        key=lambda item: _episode_return_value(item[1]),
        reverse=True,
    )[:limit]
    return [
        RankedEpisode(
            phase=phase,
            episode_idx=int(idx),
            rank=int(rank),
            episode_return=_episode_return_value(result),
        )
        for rank, (idx, result) in enumerate(ranked, start=1)
    ]


def plan_standard_training_artifacts(
    run_dir: Path,
    *,
    train_results: list[Any],
    eval_results: list[Any],
    train_episode_videos: int = 3,
    eval_episode_videos: int = 2,
    export_episode_reward_plots: bool = True,
) -> tuple[list[tuple[Any, str, Path]], list[tuple[Any, Path]], list[dict[str, Any]]]:
    """Plan reward PNGs + MP4s for top train/eval episodes (by return)."""
    layout = ensure_run_layout(run_dir)
    episodes_dir = layout["episodes"]
    videos_dir = layout["videos"]
    reward_jobs: list[tuple[Any, str, Path]] = []
    video_jobs: list[tuple[Any, Path]] = []
    manifest: list[dict[str, Any]] = []

    def _append_episode(*, ranked: RankedEpisode, result: Any) -> None:
        prefix = ranked.phase
        label = f"{prefix} ep {ranked.episode_idx + 1} (rank {ranked.rank}, return={ranked.episode_return:.1f})"
        reward_path = episodes_dir / f"{prefix}_ep_{ranked.episode_idx}_rank{ranked.rank}_reward.png"
        video_path = videos_dir / f"{prefix}_ep_{ranked.episode_idx}_rank{ranked.rank}.mp4"
        series = getattr(result, "simulation_series", None)
        if series is None:
            return
        if export_episode_reward_plots:
            reward_jobs.append((series, label, reward_path))
        video_jobs.append((series, video_path))
        entry: dict[str, Any] = {
            "phase": ranked.phase,
            "episode_idx": ranked.episode_idx,
            "rank": ranked.rank,
            "episode_return": ranked.episode_return,
            "reward_plot": str(reward_path) if export_episode_reward_plots else None,
            "video": str(video_path),
        }
        manifest.append(entry)
        if ranked.rank == 1 and ranked.phase == "train" and export_episode_reward_plots:
            reward_jobs.append((series, f"train best (ep {ranked.episode_idx + 1})", layout["episodes"] / "train_last_reward.png"))
        if ranked.rank == 1 and ranked.phase == "eval":
            if export_episode_reward_plots:
                reward_jobs.append(
                    (
                        series,
                        f"eval best (ep {ranked.episode_idx + 1})",
                        layout["episodes"] / "eval_best_reward.png",
                    )
                )
            video_jobs.append((series, layout["videos"] / "eval_best.mp4"))

    for ranked in rank_episodes_by_return(
        train_results, phase="train", limit=int(train_episode_videos)
    ):
        _append_episode(ranked=ranked, result=train_results[ranked.episode_idx])

    for ranked in rank_episodes_by_return(
        eval_results, phase="eval", limit=int(eval_episode_videos)
    ):
        _append_episode(ranked=ranked, result=eval_results[ranked.episode_idx])

    return reward_jobs, video_jobs, manifest


def write_artifacts_manifest(run_dir: Path, manifest: list[dict[str, Any]]) -> Path:
    path = run_dir / "artifacts_manifest.json"
    payload = {
        "episodes": manifest,
        "train_video_count": sum(1 for m in manifest if m.get("phase") == "train" and m.get("video")),
        "eval_video_count": sum(1 for m in manifest if m.get("phase") == "eval" and m.get("video")),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _json_safe(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {k: _json_safe(v) for k, v in asdict(value).items()}
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    return str(value)


def write_config_snapshot(run_dir: Path, payload: dict[str, Any]) -> Path:
    path = run_dir / "config.json"
    path.write_text(
        json.dumps(_json_safe(payload), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def episode_row_from_result(
    *,
    global_idx: int,
    phase: str,
    episode_idx: int,
    episode_return: float,
    steps: int,
    learning_row: dict[str, Any] | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "global_idx": int(global_idx),
        "phase": str(phase),
        "episode_idx": int(episode_idx),
        "episode_return": float(episode_return),
        "avg_reward": float(episode_return) / max(1, int(steps)),
        "steps": int(steps),
    }
    defaults = {
        "n_train_updates": 0,
        "q_loss_mean": float("nan"),
        "pi_loss_mean": float("nan"),
        "kl_mean": float("nan"),
        "kl_mu_mean": float("nan"),
        "kl_sigma_mean": float("nan"),
        "eta_mean": float("nan"),
        "buffer_size": 0,
        "in_exploration": False,
    }
    if learning_row is not None:
        defaults.update(learning_row)
    row.update(defaults)
    return row


def read_episodes_csv(run_dir: Path) -> list[dict[str, Any]]:
    path = run_dir / "episodes.csv"
    if not path.is_file():
        raise FileNotFoundError(f"Missing episodes.csv: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def finalize_episodes_csv(run_dir: Path, rows: list[dict[str, Any]]) -> Path:
    path = run_dir / "episodes.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(EPISODE_CSV_FIELDS))
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in EPISODE_CSV_FIELDS})
    return path


def _phase_summary(rows: list[dict[str, Any]], phase: str) -> dict[str, float]:
    phase_rows = [r for r in rows if r.get("phase") == phase]
    if not phase_rows:
        return {
            "episodes": 0.0,
            "return_mean": float("nan"),
            "return_std": float("nan"),
            "return_best": float("nan"),
            "avg_reward_mean": float("nan"),
        }
    returns = np.asarray([float(r["episode_return"]) for r in phase_rows], dtype=np.float64)
    avgs = np.asarray([float(r["avg_reward"]) for r in phase_rows], dtype=np.float64)
    return {
        "episodes": float(len(phase_rows)),
        "return_mean": float(np.mean(returns)),
        "return_std": float(np.std(returns)),
        "return_best": float(np.max(returns)),
        "avg_reward_mean": float(np.mean(avgs)),
    }


def write_summary_metrics_json(
    run_dir: Path,
    rows: list[dict[str, Any]],
    *,
    action_diagnostics: dict[str, Any] | None = None,
) -> Path:
    train_rows = [r for r in rows if r.get("phase") == "train"]
    eval_rows = [r for r in rows if r.get("phase") == "eval"]
    best_eval_idx = -1
    if eval_rows:
        best_eval_idx = int(
            max(range(len(eval_rows)), key=lambda i: float(eval_rows[i]["episode_return"]))
        )
    last_train_learning: dict[str, Any] = {}
    if train_rows:
        last = train_rows[-1]
        for key in (
            "q_loss_mean",
            "pi_loss_mean",
            "kl_mean",
            "kl_mu_mean",
            "kl_sigma_mean",
            "eta_mean",
            "n_train_updates",
        ):
            last_train_learning[key] = last.get(key)

    payload = {
        "warmup": _phase_summary(rows, "warmup"),
        "train": _phase_summary(rows, "train"),
        "eval": _phase_summary(rows, "eval"),
        "best_eval_episode_idx": best_eval_idx,
        "last_train_learning": last_train_learning,
    }
    if action_diagnostics is not None:
        payload["action_diagnostics"] = action_diagnostics
    path = run_dir / "summary_metrics.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _returns_ylim_from_values(ys: list[float]) -> tuple[float, float] | None:
    if not ys:
        return None
    y_min, y_max = min(ys), max(ys)
    if y_min == y_max:
        pad = max(abs(y_min) * 0.05, 1.0)
    else:
        pad = max((y_max - y_min) * 0.08, 1e-6)
    return y_min - pad, y_max + pad


def plot_returns_by_episode(rows: list[dict[str, Any]], out_path: Path) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if not rows:
        raise ValueError("No episode rows to plot.")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    phase_order = ("warmup", "train", "eval")
    phase_colors = {"warmup": "#888888", "train": "#2a6fdb", "eval": "#2db87a"}
    by_phase: dict[str, list[dict[str, Any]]] = {phase: [] for phase in phase_order}
    for row in rows:
        phase = str(row["phase"])
        if phase in by_phase:
            by_phase[phase].append(row)

    active_phases = [phase for phase in phase_order if by_phase[phase]]
    if not active_phases:
        raise ValueError("No episode rows to plot.")

    train_ys = [float(r["episode_return"]) for r in by_phase["train"]]
    train_shared_ylim = _returns_ylim_from_values(train_ys)

    warmup_ys = [float(r["episode_return"]) for r in by_phase["warmup"]]
    warmup_mean = float(np.mean(warmup_ys)) if warmup_ys else None

    n = len(active_phases)
    fig, axes = plt.subplots(1, n, figsize=(3.5 * n + 1.5, 4), squeeze=False)

    for col, phase in enumerate(active_phases):
        ax = axes[0, col]
        phase_rows = by_phase[phase]
        xs = [int(r["episode_idx"]) for r in phase_rows]
        ys = [float(r["episode_return"]) for r in phase_rows]
        ax.plot(
            xs,
            ys,
            "o-",
            color=phase_colors[phase],
            linewidth=1.5,
            markersize=5,
        )
        if phase in ("train", "eval") and warmup_mean is not None:
            ax.axhline(
                warmup_mean,
                color="#888888",
                linewidth=1.2,
                linestyle="--",
                label=f"warmup avg ({warmup_mean:.1f})",
            )
            ax.legend(fontsize=7, loc="lower right")
        ax.set_title(phase)
        ax.set_xlabel("episode index (within phase)")
        ax.set_ylabel("episode return")
        ax.grid(True, alpha=0.25)
        if ys:
            if phase in ("train", "eval") and train_shared_ylim is not None:
                ylim = train_shared_ylim
            else:
                ylim = _returns_ylim_from_values(ys)
            if ylim is not None:
                ax.set_ylim(*ylim)

    fig.suptitle("Returns by episode", y=1.02)
    fig.tight_layout()
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return out_path


def plot_learning_curves(train_rows: list[dict[str, Any]], out_path: Path) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if not train_rows:
        raise ValueError("No train rows for learning curves.")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    eps = [int(r["episode_idx"]) + 1 for r in train_rows]

    def series(key: str) -> list[float]:
        return [float(r.get(key, float("nan"))) for r in train_rows]

    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    panels = [
        (axes[0, 0], series("q_loss_mean"), "q_loss (mean)"),
        (axes[0, 1], series("pi_loss_mean"), "pi_loss (mean)"),
        (axes[1, 0], series("kl_mean"), "kl (mean)"),
        (axes[1, 1], series("eta_mean"), "eta (mean)"),
    ]
    for ax, ys, title in panels:
        ax.plot(eps, ys, "o-", linewidth=1.5, markersize=4)
        ax.set_xlabel("train episode")
        ax.set_ylabel(title)
        ax.set_title(title)
        ax.grid(True, alpha=0.25)

    fig.suptitle("MPO learning curves (per-episode means)", fontsize=11)
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path


def plot_episode_reward_timeline(
    series: Any,
    *,
    label: str,
    out_path: Path,
) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out_path.parent.mkdir(parents=True, exist_ok=True)
    t_s = np.asarray(series.t_s, dtype=float)
    step_reward = np.asarray(series.simulation_reward, dtype=float)
    cumulative = np.cumsum(step_reward)

    fig, axes = plt.subplots(2, 1, figsize=(10, 5), sharex=True)
    axes[0].plot(t_s, step_reward, color="#2a6fdb", linewidth=1.0)
    axes[0].set_ylabel("step reward")
    axes[0].set_title(f"Reward timeline — {label}")
    axes[0].grid(True, alpha=0.25)

    axes[1].plot(t_s, cumulative, color="#c45c26", linewidth=1.4)
    axes[1].set_xlabel("time [s]")
    axes[1].set_ylabel("cumulative return")
    axes[1].grid(True, alpha=0.25)

    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path


def export_run_plots(
    run_dir: Path,
    rows: list[dict[str, Any]],
    *,
    warmup_results: list[Any] | None = None,
    train_results: list[Any] | None = None,
    eval_results: list[Any] | None = None,
) -> dict[str, Any]:
    paths = artifact_paths_map(run_dir)
    plot_returns_by_episode(rows, paths["returns_plot"])
    train_rows = [r for r in rows if r.get("phase") == "train"]
    if train_rows:
        plot_learning_curves(train_rows, paths["learning_curves_plot"])
    diagnostics = export_episode_diagnostics_plots(
        run_dir,
        warmup_results=warmup_results,
        train_results=train_results,
        eval_results=eval_results,
    )
    return {
        "returns_plot": paths["returns_plot"],
        "learning_curves_plot": paths["learning_curves_plot"],
        "episode_diagnostics": diagnostics,
    }


def export_training_episode_video_sync(series: Any, out_path: Path) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    from environment_definition.constants import RenderMode
    from render.render_main import render_from_series

    out_path.parent.mkdir(parents=True, exist_ok=True)
    rendered = render_from_series(
        simulation_series=series,
        render_mode=RenderMode.EXPORT,
        output_path=out_path,
    )
    if rendered is None or not out_path.exists():
        raise RuntimeError(f"Render export failed: {out_path}")
    return out_path
