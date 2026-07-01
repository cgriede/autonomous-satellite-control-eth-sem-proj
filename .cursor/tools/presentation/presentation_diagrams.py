"""Render presentation diagrams + synthesis plots to PNG (matplotlib only).

Cohesive dark "mission-control" theme shared by every figure so the generated
diagrams sit seamlessly on the dark deck built by ``presentation_pptx.py``.

Diagrams (structure):
  * architecture_overview  — the converged system architecture
  * scientific_method      — hypothesis cycle + experiment ladder w/ verdicts
  * reward_anatomy         — reward-term breakdown (signs + gating)
  * ml_agents_flow         — SAC / MPO training loop
  * simulation_kernel_flow — build + step loop

Synthesis plots (real, verified KPI numbers from experiment verdict JSONs):
  * results_scoreboard     — eval mean return across the campaign

Agent tool — .cursor/tools/presentation/
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_OUT = _REPO_ROOT / "docs" / "presentation" / "final" / "with-cursor" / "diagrams"

# --- shared dark theme -------------------------------------------------------

BG = "#0B1221"        # deep space navy (deck background)
PANEL = "#16223B"     # raised card
PANEL_2 = "#1E2D4D"   # lighter card
INK = "#EAF0FB"       # primary text
MUTED = "#93A4C3"     # secondary text
EDGE = "#2C3E63"      # subtle border

CYAN = "#38BDF8"      # primary accent
BLUE = "#6366F1"
GREEN = "#34D399"     # canonical / learning / positive
AMBER = "#FBBF24"     # safety / caution
RED = "#F87171"       # failure / penalty
PURPLE = "#A78BFA"    # MPO
PINK = "#F472B6"

_FONT = "DejaVu Sans"


def _new_canvas(title: str, subtitle: str | None = None):
    fig, ax = plt.subplots(figsize=(13.333, 7.5))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 13.333)
    ax.set_ylim(0, 7.5)
    ax.axis("off")
    ax.text(0.45, 7.12, title, fontsize=21, fontweight="bold", color=INK,
            family=_FONT, ha="left", va="center")
    if subtitle:
        ax.text(0.47, 6.74, subtitle, fontsize=11.5, color=CYAN, family=_FONT,
                ha="left", va="center")
    # accent rule under the header
    ax.plot([0.45, 12.9], [6.52, 6.52], color=EDGE, lw=1.2, zorder=0)
    ax.plot([0.45, 3.1], [6.52, 6.52], color=CYAN, lw=2.6, zorder=1)
    return fig, ax


def _box(ax, xy, text, *, width=2.4, height=0.62, facecolor=PANEL,
         edgecolor=CYAN, fontcolor=INK, fontsize=9.5, bold=False, lw=1.6, zorder=3):
    x, y = xy
    patch = FancyBboxPatch(
        (x - width / 2, y - height / 2), width, height,
        boxstyle="round,pad=0.02,rounding_size=0.10",
        linewidth=lw, edgecolor=edgecolor, facecolor=facecolor, zorder=zorder,
    )
    ax.add_patch(patch)
    ax.text(x, y, text, ha="center", va="center", fontsize=fontsize,
            color=fontcolor, family=_FONT, zorder=zorder + 1,
            fontweight="bold" if bold else "normal")
    return patch


def _band(ax, y, height, label, color):
    """A faint horizontal lane with a label tag placed just above the lane."""
    top = y + height / 2
    ax.add_patch(FancyBboxPatch(
        (0.35, y - height / 2), 12.65, height,
        boxstyle="round,pad=0.0,rounding_size=0.06",
        linewidth=1.0, edgecolor=EDGE, facecolor="#0F1A30", zorder=1,
    ))
    ax.add_patch(FancyBboxPatch(
        (0.35, y - height / 2), 0.16, height,
        boxstyle="square,pad=0.0", linewidth=0, facecolor=color, zorder=2,
    ))
    ax.text(0.5, top + 0.17, label, fontsize=9, color=color,
            family=_FONT, fontweight="bold", ha="left", va="center")


def _arrow(ax, start, end, color=MUTED, lw=1.6, style="-|>", zorder=4):
    ax.add_patch(FancyArrowPatch(
        start, end, arrowstyle=style, mutation_scale=14, linewidth=lw,
        color=color, shrinkA=5, shrinkB=5, zorder=zorder,
    ))


def _chip(ax, xy, text, color, *, width=2.0, fontsize=8.5):
    _box(ax, xy, text, width=width, height=0.42, facecolor=color,
         edgecolor=color, fontcolor="#0B1221", fontsize=fontsize, bold=True)


def _save(fig, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, facecolor=BG, bbox_inches="tight", pad_inches=0.18)
    plt.close(fig)
    return output_path


# --- 1. converged architecture ----------------------------------------------

def render_architecture_overview(output_path: Path | str) -> Path:
    output_path = Path(output_path)
    fig, ax = _new_canvas(
        "Converged system architecture",
        "Built from scratch · one episode = one canonical SimulationStateSeries (train = eval = render)",
    )

    # Lane backgrounds
    _band(ax, 5.65, 0.95, "CONFIGURATION", BLUE)
    _band(ax, 4.05, 1.30, "SIMULATION CORE", GREEN)
    _band(ax, 1.55, 2.25, "LEARNING LOOP", CYAN)

    # Configuration lane
    _box(ax, (2.3, 5.65), "EnvironmentSetup\n.resolve()", width=2.5, height=0.66,
         edgecolor=BLUE, fontsize=9.5, bold=True)
    _box(ax, (7.7, 5.65),
         "constants: SIMULATION · MISSION · SATELLITE\nAUTONOMOUS_CONTROL_REWARD · ATTITUDE_SAFETY",
         width=6.6, height=0.66, edgecolor=BLUE, fontcolor=MUTED, fontsize=9)
    _box(ax, (11.9, 5.65), "mission_profiles\n(s01 overflight)", width=2.3, height=0.66,
         edgecolor=BLUE, fontcolor=MUTED, fontsize=8.5)
    _arrow(ax, (3.55, 5.65), (4.38, 5.65), color=BLUE)

    # Simulation core lane — stepper + kernels
    _box(ax, (1.95, 4.05), "stepper_factory\n.build_stepper()", width=2.3, height=0.78,
         edgecolor=GREEN, fontsize=9, bold=True)
    kernels = [
        (4.95, "Dynamics +\nReactionWheel"),
        (7.15, "AttitudeSafety /\nOBC pointing"),
        (9.35, "SensorKernel\ncamera_2d · quality"),
        (11.55, "RewardKernel\ncapture credit"),
    ]
    for x, t in kernels:
        _box(ax, (x, 4.05), t, width=2.0, height=0.78, edgecolor=GREEN,
             fontcolor=INK, fontsize=8.5)
    _arrow(ax, (3.1, 4.05), (3.95, 4.05), color=GREEN)
    ax.text(7.1, 4.78, "SimulationStepper.step(τ)", fontsize=8.5, color=GREEN,
            family=_FONT, ha="center", va="center", style="italic")

    # config -> core
    _arrow(ax, (2.3, 5.32), (1.95, 4.44), color=BLUE)

    # Canonical artifact (hero pill)
    _box(ax, (6.85, 2.95),
         "SimulationStateSeries   —   canonical episode artifact",
         width=8.6, height=0.6, facecolor=PANEL_2, edgecolor=GREEN,
         fontcolor=GREEN, fontsize=11.5, bold=True, lw=2.2)
    _arrow(ax, (6.85, 3.62), (6.85, 3.28), color=GREEN, lw=2.0)

    # Learning loop (left) and render (right)
    learn = [
        (2.15, 1.95, "EpisodeRunner\nwarmup·train·eval"),
        (4.45, 1.95, "Controller\nObservation"),
        (6.75, 1.95, "Encoder\nMLP + 1D-CNN"),
        (9.05, 1.95, "Actor / Critic\nSAC | MPO"),
    ]
    for x, y, t in learn:
        _box(ax, (x, y), t, width=2.05, height=0.74, edgecolor=CYAN, fontsize=8.5)
    for i in range(len(learn) - 1):
        _arrow(ax, (learn[i][0] + 1.02, 1.95), (learn[i + 1][0] - 1.02, 1.95), color=CYAN)

    _box(ax, (8.6, 0.78), "action_adapter\nτ  |  vector u", width=2.05, height=0.62,
         edgecolor=AMBER, fontcolor=AMBER, fontsize=8.5, bold=True)
    _arrow(ax, (9.05, 1.58), (8.6, 1.09), color=AMBER)
    # action feeds back into the stepper (closed loop)
    _arrow(ax, (9.63, 0.78), (12.85, 0.78), color=AMBER, lw=1.4)
    _arrow(ax, (12.85, 0.78), (12.85, 4.05), color=AMBER, lw=1.4)
    _arrow(ax, (12.85, 4.05), (12.6, 4.05), color=AMBER, lw=1.4)
    ax.text(12.62, 1.9, "closed loop", fontsize=7.5, color=AMBER, rotation=90,
            family=_FONT, ha="center", va="center")

    # artifact -> learning
    _arrow(ax, (5.0, 2.65), (2.6, 2.34), color=GREEN)

    # render branch
    _box(ax, (11.45, 1.95), "render/* (view-only)\nMP4 + episode plots", width=2.5,
         height=0.74, edgecolor=PURPLE, fontcolor=PURPLE, fontsize=8.5, bold=True)
    _arrow(ax, (8.9, 2.65), (11.2, 2.34), color=PURPLE)

    ax.text(0.45, 0.12,
            "backend/  environment_definition · simulation · autonomous_control · render        "
            "D-003: production code frozen during hypothesis forks",
            fontsize=7.5, color=MUTED, family=_FONT, ha="left", va="center")
    return _save(fig, output_path)


# --- 2. scientific method ----------------------------------------------------

def render_scientific_method(output_path: Path | str) -> Path:
    output_path = Path(output_path)
    fig, ax = _new_canvas(
        "Scientific method",
        "Hypothesis-driven pipeline · one logical delta per arm · frozen protocol (dt 1.5 s, seeds, episode counts)",
    )

    # Top: hypothesis cycle
    cycle = [
        (1.85, 5.5, "Research\nquestion", CYAN),
        (4.05, 5.5, "Literature\n+ decisions", BLUE),
        (6.25, 5.5, "Design\n1 delta / arm", PURPLE),
        (8.45, 5.5, "Run\ntrain · eval", AMBER),
        (10.65, 5.5, "Evidence\nKPI·plot·video", GREEN),
        (12.5, 5.5, "Verdict\ncard", PINK),
    ]
    for x, y, t, c in cycle:
        _box(ax, (x, y), t, width=1.85, height=0.78, edgecolor=c, fontsize=8.7, bold=True)
    for i in range(len(cycle) - 1):
        _arrow(ax, (cycle[i][0] + 0.95, 5.5), (cycle[i + 1][0] - 0.95, 5.5), color=MUTED)
    # feedback loop arrow back to design
    _arrow(ax, (12.5, 5.11), (12.5, 4.35), color=PINK, lw=1.4)
    _arrow(ax, (12.5, 4.35), (6.25, 4.35), color=PINK, lw=1.4)
    _arrow(ax, (6.25, 4.35), (6.25, 5.11), color=PINK, lw=1.4)
    ax.text(9.3, 4.18, "negative result narrows the search space", fontsize=8,
            color=PINK, family=_FONT, ha="center", va="center", style="italic")

    # Section label for ladder
    ax.text(0.45, 3.45, "EXPERIMENT LADDER", fontsize=9.5, color=CYAN,
            family=_FONT, fontweight="bold", ha="left", va="center")
    ax.plot([0.45, 12.9], [3.18, 3.18], color=EDGE, lw=1.0)

    ladder = [
        (2.0, "Exp 1\nShutter threshold", "MPO sparse · 0.5 vs 0.9", "not supported", RED,
         "514.9 vs 516 cmds/ep"),
        (5.0, "Exp 2\nModular encoder", "SAC sparse · flat vs compress", "not supported", RED,
         "no win at 7 ep"),
        (8.0, "Exp 3\nSAC vs MPO", "sparse SAC · dense MPO", "SAC supported", GREEN,
         "SAC learns · MPO flat"),
        (11.0, "Exp 4\nVector OBC", "torque vs vector ref", "both learn", GREEN,
         "promoted (D-016)"),
    ]
    for x, title, method, verdict, color, note in ladder:
        _box(ax, (x, 2.35), title, width=2.55, height=0.74, edgecolor=color,
             fontsize=9.3, bold=True)
        ax.text(x, 1.72, method, fontsize=8, color=MUTED, family=_FONT,
                ha="center", va="center")
        _chip(ax, (x, 1.18), verdict, color, width=2.3)
        ax.text(x, 0.72, note, fontsize=7.6, color=INK, family=_FONT,
                ha="center", va="center", style="italic")
    for i in range(len(ladder) - 1):
        _arrow(ax, (ladder[i][0] + 1.3, 2.35), (ladder[i + 1][0] - 1.3, 2.35), color=MUTED)

    ax.text(0.45, 0.12,
            "Invalid runs documented and excluded · 16 decisions logged (D-001 … D-016) · report stays qualitative (D-008)",
            fontsize=7.5, color=MUTED, family=_FONT, ha="left", va="center")
    return _save(fig, output_path)


# --- 3. reward anatomy -------------------------------------------------------

def render_reward_anatomy(output_path: Path | str) -> Path:
    output_path = Path(output_path)
    fig, ax = _new_canvas(
        "Reward anatomy (notebook-08 capture-only path)",
        "Credit paid only on budgeted shutter events · dense penalties regularize control",
    )

    _box(ax, (6.85, 5.55), "step reward  r(s, a)", width=4.6, height=0.72,
         facecolor=PANEL_2, edgecolor=CYAN, fontcolor=CYAN, fontsize=13, bold=True, lw=2.2)

    pos = [
        (2.4, "+ capture credit",
         "quality x coverage x (1 - cloud_frac)\n@ budgeted, novel shutter  (<=10/orbit)"),
        (6.85, "+ area terms",
         "intersection & novelty\nratio (geodetic path)"),
    ]
    for x, head, body in pos:
        _box(ax, (x, 3.95), head, width=3.9, height=0.55, edgecolor=GREEN,
             fontcolor=GREEN, fontsize=10.5, bold=True)
        ax.text(x, 3.28, body, fontsize=8.6, color=INK, family=_FONT,
                ha="center", va="center")
        _arrow(ax, (6.85, 5.18), (x, 4.25), color=GREEN)

    _box(ax, (10.9, 3.95), "- penalties", width=3.9, height=0.55, edgecolor=RED,
         fontcolor=RED, fontsize=10.5, bold=True)
    ax.text(10.9, 3.28,
            "shutter waste  (-k)\ntorque effort  -k(tau/tau_max)^2  (off in vector mode)",
            fontsize=8.6, color=INK, family=_FONT, ha="center", va="center")
    _arrow(ax, (6.85, 5.18), (10.9, 4.25), color=RED)

    # the one term worth a slide of its own
    _box(ax, (6.85, 1.75),
         "quality (the q in capture credit) = image-quality from motion smear  ->  see next slide",
         width=10.6, height=0.7, facecolor=PANEL_2, edgecolor=AMBER, fontcolor=AMBER,
         fontsize=11, bold=True)
    _arrow(ax, (2.4, 2.95), (4.0, 2.12), color=MUTED)

    ax.text(0.45, 0.12,
            "Source: autonomous_control/reward.py · simulation/reward_kernel.py · constants/AUTONOMOUS_CONTROL_REWARD.py",
            fontsize=7.5, color=MUTED, family=_FONT, ha="left", va="center")
    return _save(fig, output_path)


# --- 4. ML agents flow (dark) ------------------------------------------------

def render_ml_agents_flowchart(output_path: Path | str) -> Path:
    output_path = Path(output_path)
    fig, ax = _new_canvas(
        "ML training loop — SAC & MPO (shared stack)",
        "Shared Encoder / Actor / Critic · per-tick store to ReplayBuffer · throttled gradient updates",
    )

    boxes = [
        (2.1, 5.6, "EnvironmentSetup\nbuild_stepper"),
        (5.0, 5.6, "EpisodeRunner\ncontroller ticks"),
        (8.0, 5.6, "TimestepState ->\nObservation"),
        (11.0, 5.6, "Encoder\nMLP + 1D-CNN"),
    ]
    for x, y, t in boxes:
        _box(ax, (x, y), t, width=2.4, height=0.7, edgecolor=CYAN, fontsize=9)
    for i in range(len(boxes) - 1):
        _arrow(ax, (boxes[i][0] + 1.25, 5.6), (boxes[i + 1][0] - 1.25, 5.6), color=MUTED)

    _box(ax, (6.85, 4.35), "Actor pi(a|s) -> action_adapter\n[ tau | vector u ]  +  [ shutter ]",
         width=4.6, height=0.72, edgecolor=AMBER, fontcolor=INK, fontsize=9.5)
    _arrow(ax, (11.0, 5.25), (8.6, 4.65), color=MUTED)
    _arrow(ax, (6.85, 3.99), (6.85, 3.5), color=MUTED)

    _box(ax, (6.85, 3.15),
         "SimulationStepper.step(tau)\nSafety / OBC -> Dynamics -> Sensor -> Reward",
         width=5.4, height=0.72, facecolor=PANEL_2, edgecolor=GREEN, fontcolor=GREEN,
         fontsize=9.5, bold=True)
    _arrow(ax, (6.85, 2.79), (6.85, 2.32), color=MUTED)

    _box(ax, (6.85, 1.98), "ReplayBuffer.store(s, a, r, s', done)", width=4.8, height=0.6,
         edgecolor=BLUE, fontcolor=INK, fontsize=9.5)
    _arrow(ax, (6.85, 1.68), (3.6, 1.18), color=MUTED)
    _arrow(ax, (6.85, 1.68), (10.1, 1.18), color=MUTED)

    _box(ax, (3.6, 0.78),
         "SAC  (off-policy actor-critic)\ntwin Q + entropy bonus (fixed alpha) · stable, simple to tune",
         width=5.6, height=0.66, facecolor=PANEL, edgecolor=GREEN, fontcolor=INK, fontsize=8.3)
    _box(ax, (10.1, 0.78),
         "MPO  (EM-style policy opt.)\nKL trust region (eta dual) · stricter, more sensitive",
         width=5.6, height=0.66, facecolor=PANEL, edgecolor=PURPLE, fontcolor=INK, fontsize=8.3)

    ax.text(0.45, 0.12,
            "Reward shaping (sparse / dense) and algorithm are tuned independently — we test which pairing works.",
            fontsize=7.5, color=MUTED, family=_FONT, ha="left", va="center")
    return _save(fig, output_path)


# --- 5. simulation kernel flow (dark) ----------------------------------------

def render_simulation_kernel_flowchart(output_path: Path | str) -> Path:
    output_path = Path(output_path)
    fig, ax = _new_canvas(
        "Simulation kernel — build & step loop",
        "Sole stepper constructor · one SimulationStateSeries per episode",
    )

    build = [
        (2.2, 5.6, "EnvironmentSetup\nmission · clouds · cameras"),
        (5.6, 5.6, "resolve()\nResolvedSetup"),
        (8.9, 5.6, "build_stepper()\nSimulationStepper"),
        (11.6, 5.6, "Orbit grid\nprecompute t, theta, r"),
    ]
    for x, y, t in build:
        _box(ax, (x, y), t, width=2.5, height=0.7, edgecolor=CYAN, fontsize=8.7)
    for i in range(len(build) - 1):
        _arrow(ax, (build[i][0] + 1.3, 5.6), (build[i + 1][0] - 1.3, 5.6), color=MUTED)

    _arrow(ax, (8.9, 5.25), (6.85, 4.75), color=MUTED)
    _box(ax, (6.85, 4.4), "step(wheel_torque_cmd_nm)", width=3.4, height=0.6,
         facecolor=PANEL_2, edgecolor=AMBER, fontcolor=AMBER, fontsize=9.5, bold=True)

    _box(ax, (2.6, 3.35), "Torque path:\nAttitudeSafetyController", width=3.0, height=0.7,
         edgecolor=AMBER, fontsize=8.3)
    _box(ax, (6.85, 3.35), "OBC PD:\nnadir / target track", width=3.0, height=0.7,
         edgecolor=CYAN, fontsize=8.3)
    _box(ax, (11.0, 3.35), "Vector path:\nu -> theta_req -> PD", width=3.0, height=0.7,
         edgecolor=GREEN, fontsize=8.3)
    _arrow(ax, (6.5, 4.1), (3.0, 3.7), color=MUTED)
    _arrow(ax, (6.85, 4.1), (6.85, 3.7), color=MUTED)
    _arrow(ax, (7.2, 4.1), (10.6, 3.7), color=MUTED)

    _box(ax, (6.85, 2.4), "DynamicsKernel.propagate\n2D attitude + reaction wheel",
         width=4.6, height=0.66, edgecolor=BLUE, fontsize=9)
    _arrow(ax, (2.6, 3.0), (5.2, 2.6), color=MUTED)
    _arrow(ax, (6.85, 3.0), (6.85, 2.73), color=MUTED)
    _arrow(ax, (11.0, 3.0), (8.5, 2.6), color=MUTED)
    _arrow(ax, (6.85, 2.07), (6.85, 1.62), color=MUTED)

    _box(ax, (6.85, 1.3),
         "SensorKernel.evaluate -> obs lines · GSD · cloud_frac · quality",
         width=7.0, height=0.6, edgecolor=PURPLE, fontsize=8.6)
    _arrow(ax, (6.85, 1.0), (6.85, 0.62), color=MUTED)

    _box(ax, (6.85, 0.34),
         "RewardKernel.evaluate -> SimulationStateSeries  (train = eval = render)",
         width=8.2, height=0.5, facecolor=PANEL_2, edgecolor=GREEN, fontcolor=GREEN,
         fontsize=9, bold=True)
    return _save(fig, output_path)


# --- 6. results scoreboard (synthesis plot, verified numbers) ----------------

# (label, eval mean return, learning_mode, source verdict file)
_SCOREBOARD = [
    ("MPO sparse · overnight H1a", -243.5, False),
    ("MPO sparse · Exp1 shutter t09", -101.6, False),
    ("SAC flat encoder · Exp2 v1", -78.9, False),
    ("MPO dense · Exp3", -51.6, False),
    ("SAC vector · Exp4 ref1", -24.1, True),
    ("SAC sparse · Exp3", -22.2, True),
    ("SAC torque · Exp4 ref0", -11.1, True),
    ("SAC M sparse · hparam", 50.6, True),
    ("SAC S sparse · hparam", 69.8, True),
    ("SAC compress · encoder r2", 80.9, True),
    # Exp 8: MPO fixed dual torque — first learning signal
    ("MPO fixed dual · Exp8 torque", -81.1, True),
    # Exp 11: MPO fixed dual vector — second positive path
    ("MPO fixed dual · Exp11 vector", 45.5, True),
    # Exp 9: SAC shutter split — waste penalty OFF beats baseline
    ("SAC shutter-split · Exp9 vector", 106.4, True),
]


def render_results_scoreboard(output_path: Path | str) -> Path:
    output_path = Path(output_path)
    fig, ax = plt.subplots(figsize=(13.333, 7.5))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    labels = [r[0] for r in _SCOREBOARD]
    values = [r[1] for r in _SCOREBOARD]
    learn = [r[2] for r in _SCOREBOARD]
    ypos = list(range(len(labels)))
    colors = [GREEN if lm else RED for lm in learn]

    ax.barh(ypos, values, color=colors, edgecolor="#0B1221", height=0.66, zorder=3)
    ax.axvline(0, color=MUTED, lw=1.2, zorder=2)

    # deterministic baseline reference (frozen warmup mean return = +89)
    baseline = 89.0
    ax.axvline(baseline, color=AMBER, lw=2.0, ls="--", zorder=5)
    ax.text(baseline + 3, len(labels) - 0.35, "deterministic\nbaseline +89",
            color=AMBER, fontsize=10, fontweight="bold", va="top", ha="left",
            family=_FONT, zorder=6)

    for y, v in zip(ypos, values):
        off = 4 if v >= 0 else -4
        ha = "left" if v >= 0 else "right"
        ax.text(v + off, y, f"{v:+.1f}", va="center", ha=ha, color=INK,
                fontsize=10, fontweight="bold", family=_FONT, zorder=4)

    ax.set_yticks(ypos)
    ax.set_yticklabels(labels, color=INK, fontsize=10.5, family=_FONT)
    ax.set_xlim(-285, 160)
    ax.tick_params(axis="x", colors=MUTED)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xlabel("eval mean episode return", color=MUTED, fontsize=11, family=_FONT)
    ax.set_title("The learnability journey  —  eval return across the campaign",
                 color=INK, fontsize=18, fontweight="bold", family=_FONT, pad=16, loc="left")
    ax.grid(axis="x", color=EDGE, lw=0.7, zorder=0)

    # legend (placed in the empty lower-right quadrant)
    ax.text(0.985, 0.17, "learning signal inferred", transform=ax.transAxes, color=GREEN,
            fontsize=11, fontweight="bold", ha="right", va="center", family=_FONT)
    ax.text(0.985, 0.115, "no learning signal", transform=ax.transAxes, color=RED,
            fontsize=11, fontweight="bold", ha="right", va="center", family=_FONT)

    fig.text(0.012, 0.012,
             "Learning signal = our read of returns trending up with finite KL (heuristic, not a setting).  "
             "Baseline = deterministic warmup mean (+89).  Sources: verdict JSONs + run summary_metrics.json",
             color=MUTED, fontsize=8, family=_FONT)
    fig.subplots_adjust(left=0.27, right=0.97, top=0.86, bottom=0.12)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, facecolor=BG)
    plt.close(fig)
    return output_path


# --- 7. safety flow (mode-specific) ------------------------------------------

def render_safety_flow(output_path: Path | str) -> Path:
    output_path = Path(output_path)
    fig, ax = _new_canvas(
        "Attitude safety — mode-specific control",
        "Hard limit 45 deg off-nadir · two action interfaces, one reaction wheel",
    )

    _chip(ax, (3.45, 6.05), "TORQUE MODE — Ref0 (production)", AMBER, width=5.0, fontsize=9)
    _chip(ax, (9.9, 6.05), "VECTOR MODE — Ref1 (alt. action space)", GREEN, width=5.0, fontsize=9)

    # left lane (torque)
    _box(ax, (3.45, 5.35), "agent: wheel torque tau_cmd", width=4.6, height=0.56,
         edgecolor=AMBER, fontsize=9)
    _box(ax, (3.45, 4.55), "AttitudeSafetyController.arbitrate()", width=4.6, height=0.56,
         facecolor=PANEL_2, edgecolor=AMBER, fontcolor=INK, fontsize=9, bold=True)
    _arrow(ax, (3.45, 5.07), (3.45, 4.83), color=AMBER)
    outs = [
        (1.75, "normal:\npass-through", GREEN),
        (3.45, "near limit:\ntaper torque", AMBER),
        (5.25, "predicted\nviolation:\nsafe-mode", RED),
    ]
    for x, t, c in outs:
        _box(ax, (x, 3.65), t, width=1.55, height=0.72, edgecolor=c, fontcolor=c, fontsize=8)
        _arrow(ax, (3.45, 4.27), (x, 4.02), color=MUTED)
    # safe-mode FSM
    fsm = [(1.55, "BRAKE"), (2.85, "CRUISE"), (4.15, "SETTLE"), (5.55, "LOCKOUT\n60 s")]
    for x, t in fsm:
        _box(ax, (x, 2.55), t, width=1.2, height=0.5, edgecolor=RED, fontcolor=INK, fontsize=8)
    for i in range(len(fsm) - 1):
        _arrow(ax, (fsm[i][0] + 0.6, 2.55), (fsm[i + 1][0] - 0.6, 2.55), color=RED)
    _arrow(ax, (5.25, 3.29), (5.55, 2.8), color=RED)
    ax.text(3.4, 2.0, "agent torque rejected -> OBC nadir hold", fontsize=8,
            color=MUTED, family=_FONT, ha="center", va="center", style="italic")

    # right lane (vector)
    _box(ax, (9.9, 5.35), "agent: u in [-1, 1]", width=4.6, height=0.56,
         edgecolor=GREEN, fontsize=9)
    _box(ax, (9.9, 4.55), "f_n = 45 deg * u   ->   theta_req = theta_nadir + f_n",
         width=4.9, height=0.56, edgecolor=GREEN, fontsize=8.6)
    _box(ax, (9.9, 3.65), "safety: if off-nadir >= 45 deg -> hold last valid theta_req",
         width=4.9, height=0.56, facecolor=PANEL_2, edgecolor=GREEN, fontcolor=INK,
         fontsize=8.4, bold=True)
    _box(ax, (9.9, 2.75), "PD controller -> tau   (torque-path safety bypassed)",
         width=4.9, height=0.56, edgecolor=GREEN, fontsize=8.4)
    _arrow(ax, (9.9, 5.07), (9.9, 4.83), color=GREEN)
    _arrow(ax, (9.9, 4.27), (9.9, 3.93), color=GREEN)
    _arrow(ax, (9.9, 3.37), (9.9, 3.03), color=GREEN)

    # shared bottom
    _box(ax, (6.85, 1.25),
         "ReactionWheel torque gate (block if |omega_sat| > 3 deg/s)  ->  DynamicsKernel (2D attitude)",
         width=10.5, height=0.6, facecolor=PANEL_2, edgecolor=CYAN, fontcolor=CYAN,
         fontsize=9, bold=True)
    _arrow(ax, (3.45, 1.78), (5.2, 1.55), color=MUTED)
    _arrow(ax, (9.9, 2.47), (8.6, 1.55), color=MUTED)

    ax.text(0.45, 0.12,
            "Source: simulation/attitude_controller.py · simulation/obc_pointing_request.py · constants/ATTITUDE_SAFETY.py",
            fontsize=7.5, color=MUTED, family=_FONT, ha="left", va="center")
    return _save(fig, output_path)


# --- 8. image quality --------------------------------------------------------

def render_image_quality(output_path: Path | str) -> Path:
    output_path = Path(output_path)
    fig, ax = _new_canvas(
        "Image quality — motion-smear model",
        "Ground motion during exposure blurs the frame; quality feeds capture credit",
    )

    _box(ax, (2.5, 5.45), "bore ground speed |v_bore|\nanalytic WGS84 ray hit rate",
         width=3.6, height=0.8, edgecolor=CYAN, fontsize=8.8)
    _box(ax, (2.5, 4.25), "exposure  t_exp = 100 us", width=3.6, height=0.56,
         edgecolor=CYAN, fontsize=9)

    _box(ax, (6.95, 4.9), "ground blur = |v_bore| x t_exp   [m]",
         width=4.0, height=0.7, facecolor=PANEL_2, edgecolor=AMBER, fontcolor=AMBER,
         fontsize=10, bold=True)
    _arrow(ax, (4.32, 5.45), (5.05, 5.05), color=MUTED)
    _arrow(ax, (4.32, 4.25), (5.05, 4.75), color=MUTED)

    _box(ax, (11.1, 4.9), "quality = ref / (blur + ref)\nref = 0.30 m  ->  q = 0.5 @ 0.30 m blur",
         width=4.0, height=0.7, facecolor=PANEL_2, edgecolor=GREEN, fontcolor=GREEN,
         fontsize=8.8, bold=True)
    _arrow(ax, (8.97, 4.9), (9.1, 4.9), color=MUTED)

    ax.text(2.5, 3.55, "smear_px = blur / GSD\n(telemetry only)", fontsize=8,
            color=MUTED, family=_FONT, ha="center", va="center", style="italic")

    _box(ax, (6.95, 3.0),
         "nadir coast: blur ~0.7 m  ->  quality ~0.30          "
         "target track: blur ~0.04 m  ->  quality ~0.90",
         width=11.0, height=0.62, edgecolor=AMBER, fontcolor=INK, fontsize=9)
    _arrow(ax, (11.1, 4.55), (9.5, 3.31), color=MUTED)

    _box(ax, (6.95, 1.7),
         "capture credit = quality x coverage x (1 - cloud_frac)   @ budgeted, novel shutter",
         width=11.0, height=0.66, facecolor=PANEL_2, edgecolor=GREEN, fontcolor=GREEN,
         fontsize=10.5, bold=True)
    _arrow(ax, (6.95, 2.69), (6.95, 2.03), color=GREEN)

    ax.text(0.45, 0.12,
            "Source: simulation/image_quality.py (analytic bore ground velocity, WGS84 ray) · constants/SATELLITE.py",
            fontsize=7.5, color=MUTED, family=_FONT, ha="left", va="center")
    return _save(fig, output_path)


# --- 9. Exp 3 compare (data-driven) ------------------------------------------

_EXP3_SAC = [
    -72.11, -75.94, -76.64, -78.07, -80.44, -82.13, -84.55, -84.01, -79.85, -75.89,
    -75.72, -71.32, -74.67, -75.47, -66.91, -32.00, 5.33, -71.10, -63.75, -27.00,
    -38.19, -26.13, -36.19, -37.62, -47.13, -18.75, -22.98, -41.21, -24.27, -27.87,
    -56.15, -14.38, -55.24, -28.76, -22.74, -10.47, -44.82,
]
_EXP3_MPO = [-100.54] + [-51.60] * 21


def render_exp3_compare(output_path: Path | str) -> Path:
    output_path = Path(output_path)
    fig, ax = plt.subplots(figsize=(13.333, 7.5))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    ax.plot(range(1, len(_EXP3_SAC) + 1), _EXP3_SAC, "-o", color=GREEN, lw=2.2,
            ms=4, label="SAC (sparse) — learning signal", zorder=4)
    ax.plot(range(1, len(_EXP3_MPO) + 1), _EXP3_MPO, "-o", color=PURPLE, lw=2.2,
            ms=4, label="MPO (dense) — collapsed at -51.6", zorder=4)
    ax.axhline(0, color=MUTED, lw=1.0, zorder=1)
    ax.axhline(89, color=AMBER, lw=1.8, ls="--", zorder=2)
    ax.text(len(_EXP3_SAC), 92, "deterministic baseline +89", color=AMBER,
            fontsize=10, fontweight="bold", ha="right", family=_FONT)

    ax.annotate("SAC best +5.3 (ep 16)", xy=(16, 5.33), xytext=(19, 38),
                color=GREEN, fontsize=10, fontweight="bold", family=_FONT,
                arrowprops=dict(arrowstyle="->", color=GREEN))
    ax.text(23, -47, "MPO flat-lines despite dense credit", color=PURPLE,
            fontsize=10.5, fontweight="bold", family=_FONT)

    ax.set_xlabel("train episode", color=MUTED, fontsize=11, family=_FONT)
    ax.set_ylabel("episode return", color=MUTED, fontsize=11, family=_FONT)
    ax.set_title("Exp 3 — SAC learns, MPO collapses  (dt 1.5 s, patience-stopped)",
                 color=INK, fontsize=18, fontweight="bold", family=_FONT, pad=14, loc="left")
    ax.tick_params(colors=MUTED)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.grid(color=EDGE, lw=0.6, zorder=0)
    leg = ax.legend(loc="lower right", fontsize=11, facecolor=PANEL, edgecolor=EDGE)
    for txt in leg.get_texts():
        txt.set_color(INK)
    fig.text(0.012, 0.012, "eval mean: SAC -22.2 (verdict supported) · MPO -51.6 (inconclusive). "
             "Source: ml_sac_mpo_compare/results/compare_sac_mpo.json",
             color=MUTED, fontsize=8, family=_FONT)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.88, bottom=0.11)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, facecolor=BG)
    plt.close(fig)
    return output_path


# --- 10. Exp 4 compare (bars) ------------------------------------------------

def render_exp4_compare(output_path: Path | str) -> Path:
    output_path = Path(output_path)
    fig, ax = plt.subplots(figsize=(13.333, 7.5))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    groups = ["eval mean return", "best train return"]
    torque = [-11.1, 8.4]
    vector = [-24.1, 95.8]
    x = np.arange(len(groups))
    w = 0.34
    b1 = ax.bar(x - w / 2, torque, w, color=CYAN, edgecolor=BG, label="Ref0 — torque", zorder=3)
    b2 = ax.bar(x + w / 2, vector, w, color=GREEN, edgecolor=BG, label="Ref1 — vector", zorder=3)
    ax.axhline(0, color=MUTED, lw=1.0)
    for bars in (b1, b2):
        for r in bars:
            h = r.get_height()
            ax.text(r.get_x() + r.get_width() / 2, h + (3 if h >= 0 else -3),
                    f"{h:+.1f}", ha="center", va="bottom" if h >= 0 else "top",
                    color=INK, fontsize=12, fontweight="bold", family=_FONT)

    ax.set_xticks(list(x))
    ax.set_xticklabels(groups, color=INK, fontsize=13, family=_FONT)
    ax.set_ylabel("episode return", color=MUTED, fontsize=11, family=_FONT)
    ax.set_ylim(-40, 120)
    ax.set_title("Exp 4 — torque vs vector action space  (SAC, 50 episodes)",
                 color=INK, fontsize=18, fontweight="bold", family=_FONT, pad=14, loc="left")
    ax.tick_params(colors=MUTED)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.grid(axis="y", color=EDGE, lw=0.6, zorder=0)
    leg = ax.legend(loc="upper left", fontsize=12, facecolor=PANEL, edgecolor=EDGE)
    for txt in leg.get_texts():
        txt.set_color(INK)
    ax.text(0.5, 108, "Both arms show a learning signal · hold-last events = 0 · "
            "torque wins eval, vector peaks higher in train",
            color=MUTED, fontsize=10.5, family=_FONT, ha="center")
    fig.text(0.012, 0.012, "Source: ml_agent_reference_pointing/results/agent_reference.json "
             "(eval) + run returns_by_episode (train best)", color=MUTED, fontsize=8, family=_FONT)
    fig.subplots_adjust(left=0.08, right=0.97, top=0.88, bottom=0.10)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, facecolor=BG)
    plt.close(fig)
    return output_path


# --- registry ----------------------------------------------------------------

_DIAGRAMS = {
    "architecture_overview": render_architecture_overview,
    "scientific_method": render_scientific_method,
    "reward_anatomy": render_reward_anatomy,
    "image_quality": render_image_quality,
    "safety_flow": render_safety_flow,
    "ml_agents_flow": render_ml_agents_flowchart,
    "simulation_kernel_flow": render_simulation_kernel_flowchart,
    "results_scoreboard": render_results_scoreboard,
    "exp3_compare": render_exp3_compare,
    "exp4_compare": render_exp4_compare,
}


def render_all(output_dir: Path | str | None = None) -> list[Path]:
    out = Path(output_dir) if output_dir is not None else _DEFAULT_OUT
    out.mkdir(parents=True, exist_ok=True)
    return [fn(out / f"{name}.png") for name, fn in _DIAGRAMS.items()]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render presentation diagram PNGs.")
    parser.add_argument("--output-dir", type=Path, default=_DEFAULT_OUT)
    parser.add_argument("--which", choices=("all", *_DIAGRAMS.keys()), default="all")
    args = parser.parse_args(argv)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if args.which == "all":
        for p in render_all(args.output_dir):
            print(f"Wrote {p}")
    else:
        p = _DIAGRAMS[args.which](args.output_dir / f"{args.which}.png")
        print(f"Wrote {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
