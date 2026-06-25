"""Pretty-print simulation run context before rollout (notebook- and terminal-friendly)."""
from __future__ import annotations

import sys
from typing import Any

import numpy as np

from environment_definition.constants.SATELLITE import CAMERA_EXPOSURE_TIME
from utils.units.require_compatible_unit import require_compatible_units

from .state_types import SimulationTimestepState
from .stepper import SimulationStepper


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


def _reward_summary(reward_config: Any) -> str:
    if reward_config is None:
        return "defaults"
    flags = []
    for name in (
        "enable_distance_reward",
        "enable_outer_gate",
        "enable_energy",
        "enable_area_intersection",
        "enable_area_novelty",
        "enable_cloud_penalty",
        "enable_secondary_cloud_penalty",
    ):
        if getattr(reward_config, name, False):
            flags.append(name.removeprefix("enable_"))
    return ", ".join(flags) if flags else "all core terms off"


def _camera_mount_lines(
    *,
    label: str,
    mount: Any,
    altitude: Any,
    ureg: Any,
    n_bins: int,
    pixel_ray_samples: int | None,
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
        ("role", reward_role),
        ("tilt off nadir", f"{tilt_deg:.2f} deg"),
        ("FOV (cross x along)", f"{fov_x_deg:.2f} deg x {fov_y_deg:.2f} deg"),
        ("resolution", f"{cam.n_pixels_x} x {cam.n_pixels_y} px"),
        ("pixel pitch", f"{float(cam.pixel_size.to(ureg.um).magnitude):.2f} um"),
        ("focal length", f"{float(cam.focal_length.to(ureg.mm).magnitude):.1f} mm"),
        (f"GSD @ {alt_km:.1f} km", f"{gsd_m:.3f} m"),
        ("observation line bins", str(n_bins)),
    ]
    if pixel_ray_samples is not None:
        rows.append(("strip ray samples", str(pixel_ray_samples)))
    if vertical_fov_rad is not None:
        rows.append(
            ("sim vertical FOV", f"{np.rad2deg(vertical_fov_rad):.3f} deg"),
        )
    if include_exposure:
        rows.append(("exposure time", _format_exposure_for_display(cam.exposure_time, ureg)))
    return [(f"{label} - {k}", v) for k, v in rows]


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
    sim_cfg = simulation_config if simulation_config is not None else stepper._sim_config

    rows: list[tuple[str, str]] = [
        ("episode duration", f"{meta.sim_total_s:.2f} s"),
        ("simulation timestep", f"{meta.sim_dt_s:g} s"),
        ("integration steps", f"{stepper.total_steps} (+1 state samples)"),
        ("orbit altitude", f"{alt_km:.2f} km"),
        ("orbit period", f"{meta.orbit_period_s:.1f} s"),
        ("theta center offset", f"{np.rad2deg(stepper._theta_center_rad):.2f} deg"),
        ("episode theta start (rel. center)", f"{meta.start_angle_deg:.3f} deg"),
        ("episode theta end (rel. center)", f"{meta.end_angle_deg:.3f} deg"),
        ("sat motion span scale", f"{stepper._sat_motion_span_scale:.3f}"),
        ("sat z offset", f"{stepper._sat_z_offset_deg:.2f} deg"),
    ]
    rows.extend(
        [
            ("target areas", str(len(stepper._target_areas))),
            ("target phi stripe", f"{stepper._stripe_phi_min_deg:.2f} deg .. {stepper._stripe_phi_max_deg:.2f} deg"),
            ("cloud patches", str(len(stepper._clouds))),
            ("render mode", str(meta.render_mode)),
            ("torque command source", str(meta.torque_command_source)),
            (
                "torque policy",
                str(meta.torque_policy_label or meta.builtin_torque_policy or meta.controller_mode),
            ),
            (
                "attitude controller",
                "enabled" if meta.attitude_controller_enabled else "disabled",
            ),
            ("control stack (display)", str(meta.controller_mode)),
            ("controller seed", "-" if getattr(sim_cfg, "controller_seed", None) is None else str(sim_cfg.controller_seed)),
            ("controller update (configured)", f"{configured_ctrl_s:g} s"),
            ("controller update (effective)", f"{effective_ctrl_s:g} s ({ctrl_steps} steps)"),
            ("reaction-wheel torque max", f"{tau_max_nm:.4f} N*m" if tau_max_nm is not None else "-"),
            (
                "attitude safety cutoff",
                f"|omega_sat| > {float(stepper._reaction_wheel.max_manouver_rate.to(ureg.deg / ureg.s).magnitude):.2f} deg/s -> block opposing torque",
            ),
            ("camera kernel backend", str(stepper._camera_kernel_backend)),
            ("reward shaping", _reward_summary(stepper._reward_cfg)),
        ]
    )
    if episode_mode is not None:
        rows.append(("episode runner mode", episode_mode))
    agent_line = _agent_descriptor(agent)
    if agent_line is not None:
        rows.append(("agent", agent_line))

    n_bins_primary = int(stepper._camera_observation_line_codes.shape[1])
    if len(stepper._cameras) >= 1:
        rows.extend(
            _camera_mount_lines(
                label="Camera 1 (primary)",
                mount=stepper._cameras[0],
                altitude=stepper._satellite_altitude,
                ureg=ureg,
                n_bins=n_bins_primary,
                pixel_ray_samples=stepper._camera_pixel_ray_samples,
                vertical_fov_rad=stepper._camera_vertical_fov_rad,
                include_exposure=True,
                reward_role="shapes reward (observation line + strip)",
            )
        )
    else:
        rows.extend(
            [
                ("Camera 1 (primary)", "default nadir pinhole (no explicit mount)"),
                ("Camera 1 · observation line bins", str(n_bins_primary)),
                ("Camera 1 · strip ray samples", str(stepper._camera_pixel_ray_samples)),
                (
                    "Camera 1 · sim vertical FOV",
                    f"{np.rad2deg(stepper._camera_vertical_fov_rad):.3f} deg",
                ),
                ("Camera 1 · exposure time", _format_exposure_for_display(CAMERA_EXPOSURE_TIME, ureg)),
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
                pixel_ray_samples=None,
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

    rows: list[tuple[str, str]] = []
    if episode_mode is not None:
        rows.append(("episode runner mode", str(episode_mode)))
    agent_line = _agent_descriptor(agent)
    if agent_line is not None:
        rows.append(("agent", agent_line))
    rows.append(
        (
            "control stack",
            f"{meta.torque_policy_label or meta.controller_mode} "
            f"(attitude controller {'on' if meta.attitude_controller_enabled else 'off'})",
        )
    )
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
            ("reward shaping", _reward_summary(stepper._reward_cfg)),
            (
                "mission",
                f"alt {alt_km:.1f} km · θ {meta.start_angle_deg:.1f}°..{meta.end_angle_deg:.1f}° · "
                f"{len(stepper._target_areas)} target stripe · {len(stepper._clouds)} clouds",
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
        ("step reward", f"{reward:.4f}"),
        ("episode return", f"{episode_return:.2f}"),
        ("body z angle", f"{float(ts.body_z_angle_rad):.4f} rad"),
        ("omega sat", f"{float(ts.omega_sat_rad_s):.4f} rad/s"),
    ]

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


def render_training_panel_html(
    rows: list[tuple[str, str]],
    *,
    title: str = "Live stats",
    border_style: str = "green",
) -> str:
    """Render a Rich table panel to standalone HTML for in-place notebook updates."""
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 1))
    table.add_column("Parameter", style="cyan", no_wrap=True)
    table.add_column("Value")
    for label, value in rows:
        table.add_row(label, value)
    console = Console(record=True, width=110)
    console.print(Panel(table, title=f"[bold]{title}[/bold]", border_style=border_style))
    return console.export_html(inline_styles=False)


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
    out = sys.stdout if file is None else file

    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table

        console = Console(file=out, force_jupyter=_in_notebook())
        table = Table(show_header=True, header_style="bold", box=None, padding=(0, 1))
        table.add_column("Parameter", style="cyan", no_wrap=True)
        table.add_column("Value")
        for label, value in rows:
            table.add_row(label, value)
        console.print(Panel(table, title="[bold]Training context[/bold]", border_style="green"))
    except ImportError:
        print("=== Training context ===", file=out)
        for label, value in rows:
            print(f"  {label}: {value}", file=out)
        print(file=out)


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
    out = sys.stdout if file is None else file

    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table

        console = Console(file=out, force_jupyter=_in_notebook())
        table = Table(show_header=True, header_style="bold", box=None, padding=(0, 1))
        table.add_column("Parameter", style="cyan", no_wrap=True)
        table.add_column("Value")
        for label, value in rows:
            table.add_row(label, value)
        console.print(Panel(table, title="[bold]Simulation info[/bold]", border_style="blue"))
    except ImportError:
        print("=== Simulation info ===", file=out)
        for label, value in rows:
            print(f"  {label}: {value}", file=out)
        print(file=out)
