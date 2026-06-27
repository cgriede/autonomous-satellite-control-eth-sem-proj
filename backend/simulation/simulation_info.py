"""Pretty-print simulation run context before rollout (notebook- and terminal-friendly)."""
from __future__ import annotations

import sys
from typing import Any

import numpy as np

from environment_definition.constants.ATTITUDE_SAFETY import (
    OFF_NADIR_HARD_LIMIT_DEG,
    SAFE_MODE_LOCKOUT_S,
)
from environment_definition.constants.SATELLITE import CAMERA_EXPOSURE_TIME
from utils.units.require_compatible_unit import require_compatible_units

from .state_types import SimulationTimestepState
from .stepper import SimulationStepper

_PILOT_KIND_LABELS: dict[str, str] = {
    "sequential_target_baseline": "Sequential baseline",
    "random_torque_agent": "Random torque",
    "max_torque_sweep_agent": "Max-torque sweep",
    "delayed_max_torque": "Delayed max torque",
    "zero_torque": "Zero torque",
    "MPOAgent": "MPOAgent",
}

_ROLLOUT_PHASE_LABELS: dict[str, str] = {
    "warmup": "warmup",
    "train": "training",
    "eval": "evaluation",
}


def _format_exposure_for_display(exposure_time: Any, ureg: Any) -> str:
    """Format pint exposure for simulation info (image-smear model)."""
    require_compatible_units(exposure_time, "second", "exposure_time")
    us = float(exposure_time.to(ureg.us).magnitude)
    if us < 1000.0:
        return f"{us:g} us (image smear)"
    ms = float(exposure_time.to(ureg.ms).magnitude)
    if ms < 1000.0:
        return f"{ms:g} ms (image smear)"
    return f"{float(exposure_time.to(ureg.s).magnitude):g} s (image smear)"


def _in_notebook() -> bool:
    try:
        from IPython import get_ipython  # type: ignore
    except Exception:
        return False
    shell = get_ipython()
    if shell is None:
        return False
    return shell.__class__.__name__ == "ZMQInteractiveShell"


def _agent_descriptor(agent: Any | None) -> str | None:
    if agent is None:
        return None
    parts = [type(agent).__name__]
    for attr in ("checkpoint_path", "model_path", "policy_path", "version"):
        if hasattr(agent, attr):
            value = getattr(agent, attr)
            if value not in (None, ""):
                parts.append(f"{attr}={value}")
    return " | ".join(parts)


def _pilot_kind_label(meta: Any, agent: Any | None) -> str:
    """Human-readable pilot/controller name (torque + shutter policy)."""
    raw = meta.torque_policy_label or meta.builtin_torque_policy
    if raw:
        base = str(raw).split(":")[0]
        if base in _PILOT_KIND_LABELS:
            return _PILOT_KIND_LABELS[base]
        return str(base).replace("_", " ")
    if agent is not None:
        name = type(agent).__name__
        return _PILOT_KIND_LABELS.get(name, name)
    return "unknown"


def _rollout_phase_label(episode_mode: str | None) -> str | None:
    if episode_mode is None:
        return None
    return _ROLLOUT_PHASE_LABELS.get(str(episode_mode).lower(), str(episode_mode))


def _reward_program_rows(reward_config: Any) -> list[tuple[str, str]]:
    """Describe reward terms that are actually active for this episode."""
    if reward_config is None:
        return [("reward program", "defaults")]

    rows: list[tuple[str, str]] = []
    if getattr(reward_config, "enable_image_quality_capture", False):
        rows.append(
            (
                "reward (capture)",
                "applied on shutter: coverage × quality × (1 − clouds); latent every step",
            )
        )
    if getattr(reward_config, "enable_distance_reward", False):
        outer = "on" if getattr(reward_config, "enable_outer_gate", False) else "off"
        rows.append(("reward (distance band)", f"LOS band shaping · outer gate {outer}"))
    if getattr(reward_config, "enable_area_intersection", False):
        rows.append(("reward (area intersection)", "on"))
    if getattr(reward_config, "enable_area_novelty", False):
        rows.append(("reward (area novelty)", "on"))
    if getattr(reward_config, "enable_energy", False):
        rows.append(("reward (energy)", "wheel momentum penalty"))
    if getattr(reward_config, "enable_cloud_penalty", False):
        rows.append(("reward (cloud penalty)", "primary observation line"))
    if getattr(reward_config, "enable_secondary_cloud_penalty", False):
        rows.append(("reward (cloud penalty)", "secondary strip"))

    if rows:
        return rows
    return [("reward program", "no active terms")]


def _attitude_safety_rows(stepper: SimulationStepper, ureg: Any) -> list[tuple[str, str]]:
    hard_limit_deg = float(OFF_NADIR_HARD_LIMIT_DEG.to(ureg.deg).magnitude)
    lockout_s = float(SAFE_MODE_LOCKOUT_S.to(ureg.s).magnitude)
    rw_rate_deg_s = float(
        stepper._reaction_wheel.max_manouver_rate.to(ureg.deg / ureg.s).magnitude
    )
    return [
        (
            "attitude safe-mode limit",
            f"off-nadir > {hard_limit_deg:.0f} deg → brake, nadir recovery, then lockout",
        ),
        (
            "attitude safe-mode lockout",
            f"{lockout_s:.0f} s with no agent torque after nadir recovery",
        ),
        (
            "attitude RW rate limit",
            f"|omega_sat| > {rw_rate_deg_s:.2f} deg/s → block opposing torque",
        ),
    ]


def _camera_mount_lines(
    *,
    label: str,
    mount: Any,
    altitude: Any,
    ureg: Any,
    n_bins: int,
    vertical_fov_rad: float | None,
    include_exposure: bool,
    reward_role: str,
) -> list[tuple[str, str]]:
    cam = mount.camera
    alt_km = float(altitude.to(ureg.km).magnitude)
    fov_y_deg = float(cam.fov(axis="y").to(ureg.deg).magnitude)
    fov_x_deg = float(cam.fov(axis="x").to(ureg.deg).magnitude)
    tilt_deg = float(mount.tilt_off_nadir.to(ureg.deg).magnitude)
    gsd_m = float(cam.gsd_at(altitude).to(ureg.m).magnitude)
    rows: list[tuple[str, str]] = [
        (label, ""),
        ("  role", reward_role),
        ("  tilt off nadir", f"{tilt_deg:.2f} deg"),
        ("  FOV (cross x along)", f"{fov_x_deg:.2f} deg x {fov_y_deg:.2f} deg"),
        ("  resolution", f"{cam.n_pixels_x} x {cam.n_pixels_y} px"),
        ("  pixel pitch", f"{float(cam.pixel_size.to(ureg.um).magnitude):.2f} um"),
        ("  focal length", f"{float(cam.focal_length.to(ureg.mm).magnitude):.1f} mm"),
        (f"  GSD @ {alt_km:.1f} km", f"{gsd_m:.3f} m"),
        ("  observation line bins", str(n_bins)),
    ]
    if vertical_fov_rad is not None:
        rows.append(("  sim vertical FOV", f"{np.rad2deg(vertical_fov_rad):.3f} deg"))
    if include_exposure:
        rows.append(("  exposure time", _format_exposure_for_display(cam.exposure_time, ureg)))
    return rows


def build_simulation_info_rows(
    stepper: SimulationStepper,
    *,
    simulation_config: Any | None = None,
    tau_max_nm: float | None = None,
    agent: Any | None = None,
    episode_mode: str | None = None,
) -> list[tuple[str, str]]:
    """Return (label, value) rows for display."""
    meta = stepper._metadata
    ureg = stepper._ureg
    alt_km = float(stepper._satellite_altitude.to(ureg.km).magnitude)
    configured_ctrl_s = float(stepper._configured_controller_interval_s)
    effective_ctrl_s = float(stepper.effective_controller_update_interval_s)
    ctrl_steps = int(stepper.controller_update_interval_steps)

    rows: list[tuple[str, str]] = [
        ("episode duration", f"{meta.sim_total_s:.2f} s"),
        ("simulation timestep", f"{meta.sim_dt_s:g} s"),
        ("integration steps", f"{stepper.total_steps} (+1 state samples)"),
        ("orbit altitude", f"{alt_km:.2f} km"),
        ("orbit period", f"{meta.orbit_period_s:.1f} s"),
        ("episode theta start (rel. center)", f"{meta.start_angle_deg:.3f} deg"),
        ("episode theta end (rel. center)", f"{meta.end_angle_deg:.3f} deg"),
        ("sat motion span scale", f"{stepper._sat_motion_span_scale:.3f}"),
        ("target areas", str(len(stepper._target_areas))),
        ("cloud patches", str(len(stepper._clouds))),
        ("render mode", str(meta.render_mode)),
        ("pilot", _pilot_kind_label(meta, agent)),
    ]
    rollout = _rollout_phase_label(episode_mode)
    if rollout is not None:
        rows.append(("rollout", rollout))
    rows.extend(
        [
            ("controller update (configured)", f"{configured_ctrl_s:g} s"),
            ("controller update (effective)", f"{effective_ctrl_s:g} s ({ctrl_steps} steps)"),
            ("reaction-wheel torque max", f"{tau_max_nm:.4f} N*m" if tau_max_nm is not None else "-"),
        ]
    )
    rows.extend(_attitude_safety_rows(stepper, ureg))
    rows.extend(_reward_program_rows(stepper._reward_cfg))

    n_bins_primary = int(stepper._camera_observation_line_codes.shape[1])
    if len(stepper._cameras) >= 1:
        rows.extend(
            _camera_mount_lines(
                label="Camera 1 (primary)",
                mount=stepper._cameras[0],
                altitude=stepper._satellite_altitude,
                ureg=ureg,
                n_bins=n_bins_primary,
                vertical_fov_rad=stepper._camera_vertical_fov_rad,
                include_exposure=True,
                reward_role="shapes reward (observation line + cloud fraction)",
            )
        )
    else:
        rows.extend(
            [
                ("Camera 1 (primary)", ""),
                ("  mount", "default nadir pinhole (no explicit mount)"),
                ("  observation line bins", str(n_bins_primary)),
                (
                    "  sim vertical FOV",
                    f"{np.rad2deg(stepper._camera_vertical_fov_rad):.3f} deg",
                ),
                ("  exposure time", _format_exposure_for_display(CAMERA_EXPOSURE_TIME, ureg)),
            ]
        )

    if stepper._has_secondary and len(stepper._cameras) >= 2:
        rows.extend(
            _camera_mount_lines(
                label="Camera 2 (secondary)",
                mount=stepper._cameras[1],
                altitude=stepper._satellite_altitude,
                ureg=ureg,
                n_bins=stepper._n_bins_secondary,
                vertical_fov_rad=stepper._secondary_vertical_fov_rad,
                include_exposure=False,
                reward_role="cloud/context only (no exposure in reward)",
            )
        )
    elif stepper._has_secondary:
        rows.append(("Camera 2 (secondary)", "mount present but bins=0 (inactive)"))
    else:
        rows.append(("Camera 2 (secondary)", "none"))

    return rows


def build_training_context_rows(
    stepper: SimulationStepper,
    *,
    tau_max_nm: float | None = None,
    agent: Any | None = None,
    episode_mode: str | None = None,
) -> list[tuple[str, str]]:
    """Compact rows for MPO training episodes (MDP + control, not full hardware dump)."""
    meta = stepper._metadata
    ureg = stepper._ureg
    alt_km = float(stepper._satellite_altitude.to(ureg.km).magnitude)
    effective_ctrl_s = float(stepper.effective_controller_update_interval_s)
    ctrl_steps = int(stepper.controller_update_interval_steps)
    n_bins_primary = int(stepper._camera_observation_line_codes.shape[1])
    n_bins_secondary = int(stepper._n_bins_secondary) if stepper._has_secondary else 0

    rows: list[tuple[str, str]] = [
        ("pilot", _pilot_kind_label(meta, agent)),
    ]
    rollout = _rollout_phase_label(episode_mode)
    if rollout is not None:
        rows.append(("rollout", rollout))
    rows.extend(
        [
            (
                "episode",
                f"{meta.sim_total_s:.1f} s · {stepper.total_steps} steps · dt={meta.sim_dt_s:g} s",
            ),
            (
                "control interval",
                f"{effective_ctrl_s:g} s ({ctrl_steps} steps)"
                + (
                    f" · τ_max={tau_max_nm:.4f} N*m"
                    if tau_max_nm is not None
                    else ""
                ),
            ),
            (
                "mission",
                f"alt {alt_km:.1f} km · θ {meta.start_angle_deg:.1f}°..{meta.end_angle_deg:.1f}° · "
                f"{len(stepper._target_areas)} targets · {len(stepper._clouds)} clouds",
            ),
            (
                "observation",
                f"primary {n_bins_primary} bins (reward)"
                + (
                    f" · secondary {n_bins_secondary} bins (cloud)"
                    if n_bins_secondary > 0
                    else ""
                ),
            ),
        ]
    )
    rows.extend(_reward_program_rows(stepper._reward_cfg))
    return rows


def _recent_metric_mean(metrics: dict[str, Any], key: str, start: int) -> float | None:
    values = metrics.get(key)
    if not isinstance(values, list) or len(values) <= start:
        return None
    chunk = values[start:]
    if not chunk:
        return None
    return float(np.mean(np.asarray(chunk, dtype=np.float64)))


def exploration_status_for_rollout(
    *,
    mode: str,
) -> tuple[str | None, bool]:
    """Map rollout mode to live-panel label and episode ``in_exploration`` flag.

    Train rollouts use the policy distribution for ``train`` and the policy mean for
    ``eval``. Warmup is not considered an exploration phase here.
    """
    if mode == "warmup":
        return None, False
    if mode == "eval":
        return "deterministic (policy mean)", False
    if mode == "train":
        return "active (policy sample)", True
    return None, False


def build_training_live_stats_rows(
    ts: SimulationTimestepState,
    *,
    step: int,
    total_steps: int,
    reward: float,
    episode_return: float,
    mode: str,
    episode_idx: int,
    episode_total: int | None = None,
    agent: Any | None = None,
    metrics_start: Any | None = None,
    capture_budget_remaining: int | None = None,
    safe_mode_activations: int | None = None,
) -> list[tuple[str, str]]:
    """Rows that change during rollout — for periodic live training panels."""
    pct = 100.0 * float(step) / max(1, int(total_steps))
    ep_label = f"{mode} ep {episode_idx + 1}"
    if episode_total is not None:
        ep_label += f" / {episode_total}"

    rows: list[tuple[str, str]] = [
        ("episode", ep_label),
        ("step", f"{step} / {total_steps} ({pct:.1f}%)"),
        ("sim time", f"{float(ts.sim_time_s):.1f} s"),
        ("reward", f"{episode_return:.2f}"),
    ]
    if capture_budget_remaining is not None:
        rows.append(("shutter budget", f"{int(capture_budget_remaining)} remaining"))
    if safe_mode_activations is not None:
        rows.append(("safe mode activations", f"{int(safe_mode_activations)}"))
    rows.extend(
        [
            ("body z angle", f"{float(ts.body_z_angle_rad):.4f} rad"),
            ("omega sat", f"{float(ts.omega_sat_rad_s):.4f} rad/s"),
        ]
    )

    smear = float(ts.primary_camera_image_smear_px)
    quality = float(ts.primary_camera_image_quality)
    if np.isfinite(smear):
        rows.append(("image smear", f"{smear:.3f} px"))
    if np.isfinite(quality):
        rows.append(("image quality", f"{quality:.4f}"))

    if agent is None:
        return rows

    buffer_size = len(getattr(agent, "buffer", []))
    step_counter = int(getattr(agent, "step_counter", 0))
    rows.append(("buffer", f"{buffer_size}"))
    rows.append(("agent steps", f"{step_counter}"))
    exploration_label, _ = exploration_status_for_rollout(mode=mode)
    if exploration_label is not None:
        rows.append(("exploration", exploration_label))

    if mode != "train":
        return rows

    metrics = getattr(agent, "metrics", None)
    if not isinstance(metrics, dict):
        return rows

    starts = getattr(metrics_start, "lengths", {}) if metrics_start is not None else {}
    metric_labels = (
        ("kl", "kl (ep mean)"),
        ("qloss", "q loss (ep mean)"),
        ("piloss", "pi loss (ep mean)"),
        ("eta", "eta (ep mean)"),
    )
    for key, label in metric_labels:
        mean = _recent_metric_mean(metrics, key, int(starts.get(key, 0)))
        if mean is not None:
            rows.append((label, f"{mean:.6f}"))

    return rows


def _build_info_table(rows: list[tuple[str, str]]):
    from rich.table import Table

    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 1))
    table.add_column("Parameter", style="cyan", no_wrap=True)
    table.add_column("Value")
    for label, value in rows:
        table.add_row(label, value)
    return table


def _render_info_panel_html(
    rows: list[tuple[str, str]],
    *,
    title: str,
    border_style: str,
) -> str:
    from rich.console import Console
    from rich.panel import Panel

    from utils.notebook.display import wrap_notebook_rich_html

    console = Console(record=True, width=110)
    console.print(
        Panel(
            _build_info_table(rows),
            title=f"[bold]{title}[/bold]",
            border_style=border_style,
        )
    )
    return wrap_notebook_rich_html(console.export_html(inline_styles=False))


def _display_info_panel(
    rows: list[tuple[str, str]],
    *,
    title: str,
    border_style: str,
    file: Any | None = None,
) -> None:
    if _in_notebook():
        from IPython.display import HTML, display

        display(HTML(_render_info_panel_html(rows, title=title, border_style=border_style)))
        return

    out = sys.stdout if file is None else file
    try:
        from rich.console import Console
        from rich.panel import Panel

        console = Console(file=out)
        console.print(
            Panel(
                _build_info_table(rows),
                title=f"[bold]{title}[/bold]",
                border_style=border_style,
            )
        )
    except ImportError:
        print(f"=== {title} ===", file=out)
        for label, value in rows:
            print(f"  {label}: {value}", file=out)
        print(file=out)


def render_training_panel_html(
    rows: list[tuple[str, str]],
    *,
    title: str = "Live stats",
    border_style: str = "green",
) -> str:
    """Render a Rich table panel to standalone HTML for in-place notebook updates."""
    return _render_info_panel_html(rows, title=title, border_style=border_style)


def print_training_context(
    stepper: SimulationStepper,
    *,
    simulation_config: Any | None = None,
    tau_max_nm: float | None = None,
    agent: Any | None = None,
    episode_mode: str | None = None,
    file: Any | None = None,
) -> None:
    """Print a compact Rich panel for RL training episodes."""
    _ = simulation_config
    rows = build_training_context_rows(
        stepper,
        tau_max_nm=tau_max_nm,
        agent=agent,
        episode_mode=episode_mode,
    )
    _display_info_panel(
        rows,
        title="Training context",
        border_style="green",
        file=file,
    )


def print_simulation_info(
    stepper: SimulationStepper,
    *,
    simulation_config: Any | None = None,
    tau_max_nm: float | None = None,
    agent: Any | None = None,
    episode_mode: str | None = None,
    file: Any | None = None,
) -> None:
    """Print a Rich panel before tqdm (works in Jupyter and terminals)."""
    rows = build_simulation_info_rows(
        stepper,
        simulation_config=simulation_config,
        tau_max_nm=tau_max_nm,
        agent=agent,
        episode_mode=episode_mode,
    )
    _display_info_panel(
        rows,
        title="Simulation info",
        border_style="blue",
        file=file,
    )
