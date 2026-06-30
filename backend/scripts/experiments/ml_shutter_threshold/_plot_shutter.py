"""Matplotlib plots for shutter threshold experiment."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

PLOTS_DIR = Path(__file__).resolve().parent / "results" / "plots"


def _require_matplotlib():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def plot_shutter_unit_hist(arms: dict[str, dict[str, Any]], *, out_path: Path) -> None:
    plt = _require_matplotlib()
    fig, ax = plt.subplots(figsize=(8, 4))
    for arm_id, kpis in arms.items():
        units = [
            float(s["shutter_unit"])
            for s in (kpis.get("shutter_samples") or [])
            if s.get("shutter_unit") is not None
        ]
        if not units:
            continue
        ax.hist(units, bins=40, alpha=0.5, label=f"{arm_id} (n={len(units)})", density=True)
    for t in (0.5, 0.9):
        ax.axvline(t, color="k", linestyle="--", linewidth=1, alpha=0.6)
    ax.set_xlabel("shutter_unit")
    ax.set_ylabel("density")
    ax.set_title("Shutter unit distribution at controller steps")
    ax.legend()
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def plot_fire_rate_vs_threshold(samples: list[dict[str, Any]], *, out_path: Path) -> None:
    plt = _require_matplotlib()
    units = np.array([float(s["shutter_unit"]) for s in samples], dtype=float)
    if units.size == 0:
        return
    thresholds = np.linspace(0.35, 0.95, 25)
    rates = [float(np.mean(units > t)) for t in thresholds]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(thresholds, rates, marker="o", markersize=3)
    for t, label in ((0.5, "0.5"), (0.9, "0.9")):
        ax.axvline(t, color="gray", linestyle="--", alpha=0.7)
        ax.text(t, 0.02, label, rotation=90, va="bottom", ha="right")
    ax.set_xlabel("threshold")
    ax.set_ylabel("fire rate (counterfactual)")
    ax.set_title("Fire rate vs threshold (pooled samples)")
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def plot_shutter_cmds_per_episode(arms: dict[str, dict[str, Any]], *, out_path: Path) -> None:
    plt = _require_matplotlib()
    fig, ax = plt.subplots(figsize=(8, 4))
    width = 0.35
    x_base = np.arange(7)
    for i, (arm_id, kpis) in enumerate(arms.items()):
        cmds = list(kpis.get("shutter_cmds_per_episode") or [])
        if not cmds:
            continue
        x = x_base[: len(cmds)] + (i - 0.5 * (len(arms) - 1)) * width
        ax.bar(x, cmds, width=width, label=arm_id)
    ax.set_xlabel("train episode")
    ax.set_ylabel("shutter cmds")
    ax.set_title("Shutter commands per train episode")
    ax.legend()
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def plot_train_returns(arms: dict[str, dict[str, Any]], *, out_path: Path) -> None:
    plt = _require_matplotlib()
    fig, ax = plt.subplots(figsize=(8, 4))
    for arm_id, kpis in arms.items():
        rets = list(kpis.get("train_returns") or [])
        if not rets:
            continue
        ax.plot(range(len(rets)), rets, marker="o", label=arm_id)
    ax.set_xlabel("train episode")
    ax.set_ylabel("episode return")
    ax.set_title("Train returns")
    ax.legend()
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def write_all_plots(arms: dict[str, dict[str, Any]]) -> list[str]:
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)
    paths: list[str] = []
    p1 = PLOTS_DIR / "shutter_unit_hist.png"
    plot_shutter_unit_hist(arms, out_path=p1)
    paths.append(str(p1))
    pooled = []
    for kpis in arms.values():
        pooled.extend(kpis.get("shutter_samples") or [])
    p2 = PLOTS_DIR / "fire_rate_vs_threshold.png"
    plot_fire_rate_vs_threshold(pooled, out_path=p2)
    paths.append(str(p2))
    p3 = PLOTS_DIR / "shutter_cmds_per_episode.png"
    plot_shutter_cmds_per_episode(arms, out_path=p3)
    paths.append(str(p3))
    p4 = PLOTS_DIR / "train_returns.png"
    plot_train_returns(arms, out_path=p4)
    paths.append(str(p4))
    return paths
