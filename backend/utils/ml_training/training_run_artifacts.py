"""Run-directory layout, CSV/JSON snapshots, and matplotlib training plots."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

import numpy as np

from utils.ml_training.ml_training_utils import telemetry_dir

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
        "returns_plot": layout["plots"] / "returns_by_episode.png",
        "learning_curves_plot": layout["plots"] / "learning_curves.png",
        "train_last_reward_plot": layout["episodes"] / "train_last_reward.png",
        "eval_best_reward_plot": layout["episodes"] / "eval_best_reward.png",
        "eval_best_video": layout["videos"] / "eval_best.mp4",
    }


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


def plot_returns_by_episode(rows: list[dict[str, Any]], out_path: Path) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if not rows:
        raise ValueError("No episode rows to plot.")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    xs = [int(r["global_idx"]) for r in rows]
    ys = [float(r["episode_return"]) for r in rows]
    phases = [str(r["phase"]) for r in rows]
    phase_colors = {"warmup": "#888888", "train": "#2a6fdb", "eval": "#2db87a"}

    fig, ax = plt.subplots(figsize=(10, 4))
    for phase, color in phase_colors.items():
        mask = [p == phase for p in phases]
        if not any(mask):
            continue
        ax.plot(
            [x for x, m in zip(xs, mask) if m],
            [y for y, m in zip(ys, mask) if m],
            "o-",
            color=color,
            label=phase,
            linewidth=1.5,
            markersize=5,
        )

    boundaries: list[int] = []
    for i in range(1, len(phases)):
        if phases[i] != phases[i - 1]:
            boundaries.append(xs[i] - 0.5)
    for x in boundaries:
        ax.axvline(x, color="#cccccc", linestyle="--", linewidth=0.8)

    ax.set_xlabel("episode (global index)")
    ax.set_ylabel("episode return")
    ax.set_title("Returns by episode")
    ax.grid(True, alpha=0.25)
    ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
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


def export_run_plots(run_dir: Path, rows: list[dict[str, Any]]) -> dict[str, Path]:
    paths = artifact_paths_map(run_dir)
    plot_returns_by_episode(rows, paths["returns_plot"])
    train_rows = [r for r in rows if r.get("phase") == "train"]
    if train_rows:
        plot_learning_curves(train_rows, paths["learning_curves_plot"])
    return {
        "returns_plot": paths["returns_plot"],
        "learning_curves_plot": paths["learning_curves_plot"],
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
