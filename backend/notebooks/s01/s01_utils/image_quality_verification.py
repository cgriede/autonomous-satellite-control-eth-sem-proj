"""Notebook verification helpers for primary-camera image quality during simulation."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import numpy as np

from environment_definition.constants.SATELLITE import IMAGE_QUALITY_SMEAR_REFERENCE_M
from environment_definition.constants.SIMULATION import ObcPointingMode, RenderMode, SimulationConfig
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from environment_definition.mission_profiles.s01_multiple_targets_fwd_fish import build_setup
from simulation.image_quality import (
    PrimaryImageQualityDiagnostics,
    bore_ground_speed_m_s,
    decompose_primary_image_quality,
)
from simulation.setup_types import OrbitConfig, SimulationOverrides
from simulation.state_types import SimulationStateSeries
from simulation.stepper_factory import build_stepper


def build_fast_image_quality_setup(*, seed: int = 0, include_cameras: bool = True):
    """Shorter polar pass for iteration (narrow orbit window, fewer ray samples)."""
    base = build_setup(seed=seed, include_cameras=include_cameras)
    base_orbit = base.orbit
    if base_orbit is None or base_orbit.altitude is None:
        raise ValueError("build_setup must provide orbit.altitude for image-quality verification.")
    overrides = SimulationOverrides(camera_observation_line_n_bins=24) if include_cameras else None
    if base.simulation_overrides is not None and include_cameras:
        overrides = replace(
            base.simulation_overrides,
            camera_observation_line_n_bins=24,
        )
    orbit = OrbitConfig(
        altitude=base_orbit.altitude,
        start_angle_deg=-3.0,
        end_angle_deg=3.0,
        motion_span_scale=1.05,
        sat_z_offset=base_orbit.sat_z_offset if base_orbit.sat_z_offset is not None else 0 * ureg.deg,
    )
    return replace(base, orbit=orbit, simulation_overrides=overrides)


def image_quality_simulation_config(
    *,
    obc_pointing_mode: ObcPointingMode = "none",
    torque_policy_label: str = "zero_torque",
) -> SimulationConfig:
    """HEADLESS config: zero agent torque; optional OBC nadir/target pointing."""
    return SimulationConfig(
        render_mode=RenderMode.HEADLESS,
        torque_command_source="external",
        torque_policy_label=torque_policy_label,
        obc_pointing_mode=obc_pointing_mode,
    )


def _run_rollout(
    setup,
    *,
    simulation_config: SimulationConfig,
    wheel_torque_nm: float = 0.0,
    show_progress: bool = False,
) -> SimulationStateSeries:
    from tqdm import tqdm

    resolved = setup.resolve(require_camera=True)
    stepper = build_stepper(resolved, simulation_config=simulation_config)
    total_steps = max(0, int(stepper._t_s.shape[0]) - 1)
    with tqdm(total=total_steps, desc="image-quality rollout", disable=not show_progress) as pbar:
        while not stepper.done:
            stepper.step(wheel_torque_cmd_nm=float(wheel_torque_nm))
            if pbar.n < total_steps:
                pbar.update(1)
    return stepper.finalize_series()


def run_nadir_pointing_image_quality_gate(*, seed: int = 0, fast: bool = True) -> SimulationStateSeries:
    """Scenario A: OBC nadir hold, ω_sat=0 at start, zero agent torque."""
    setup = build_fast_image_quality_setup(seed=seed, include_cameras=True) if fast else build_setup(
        seed=seed, include_cameras=True
    )
    return _run_rollout(
        setup,
        simulation_config=image_quality_simulation_config(
            obc_pointing_mode="nadir",
            torque_policy_label="zero_torque_obc_nadir",
        ),
    )


def run_target_pointing_image_quality_gate(*, seed: int = 0, fast: bool = True) -> SimulationStateSeries:
    """Scenario B: OBC points bore at mission view anchor (dashed target line in render)."""
    setup = build_fast_image_quality_setup(seed=seed, include_cameras=True) if fast else build_setup(
        seed=seed, include_cameras=True
    )
    return _run_rollout(
        setup,
        simulation_config=image_quality_simulation_config(
            obc_pointing_mode="target",
            torque_policy_label="zero_torque_obc_target",
        ),
    )


def _finite_quality_stats(series: SimulationStateSeries) -> dict[str, float]:
    smear = np.asarray(series.camera_image_smear_px, dtype=float)
    quality = np.asarray(series.camera_image_quality, dtype=float)
    mask = np.isfinite(smear) & np.isfinite(quality)
    if not np.any(mask):
        return {
            "smear_min": float("nan"),
            "smear_max": float("nan"),
            "quality_min": float("nan"),
            "quality_max": float("nan"),
        }
    sm = smear[mask]
    q = quality[mask]
    return {
        "smear_min": float(np.min(sm)),
        "smear_max": float(np.max(sm)),
        "quality_min": float(np.min(q)),
        "quality_max": float(np.max(q)),
    }


def _torque_stats(series: SimulationStateSeries) -> dict[str, float]:
    tau = np.asarray(series.wheel_torque_cmd_nm, dtype=float)
    if tau.size == 0:
        return {"tau_min": float("nan"), "tau_max": float("nan"), "tau_mean": float("nan")}
    return {
        "tau_min": float(np.min(tau)),
        "tau_max": float(np.max(tau)),
        "tau_mean": float(np.mean(tau)),
    }


def _body_rate_stats(series: SimulationStateSeries) -> dict[str, float]:
    if not hasattr(series, "body_z_angle_rad") or series.body_z_angle_rad is None:
        return {"omega_deg_s_min": float("nan"), "omega_deg_s_max": float("nan")}
    dt = np.diff(np.asarray(series.t_s, dtype=float))
    dz = np.diff(np.unwrap(np.asarray(series.body_z_angle_rad, dtype=float)))
    omega = dz / np.maximum(dt, 1e-12)
    if omega.size == 0:
        return {"omega_deg_s_min": float("nan"), "omega_deg_s_max": float("nan")}
    omega_deg_s = np.rad2deg(omega)
    return {
        "omega_deg_s_min": float(np.min(omega_deg_s)),
        "omega_deg_s_max": float(np.max(omega_deg_s)),
    }


def _sat_xy_at(series: SimulationStateSeries, k: int) -> np.ndarray:
    return np.array(
        [
            series.radius_km[k] * np.cos(series.theta_orbit_rad[k]),
            series.radius_km[k] * np.sin(series.theta_orbit_rad[k]),
        ],
        dtype=float,
    )


def _omega_body_from_series(series: SimulationStateSeries, k: int) -> float:
    if k <= 0:
        return 0.0
    dt = float(series.t_s[k] - series.t_s[k - 1])
    if dt <= 0.0:
        return 0.0
    dz = float(series.body_z_angle_rad[k] - series.body_z_angle_rad[k - 1])
    return dz / dt


def decompose_series_frame(
    series: SimulationStateSeries,
    k: int,
) -> PrimaryImageQualityDiagnostics:
    """Recompute smear decomposition for frame ``k`` from stored series fields."""
    z = float(series.body_z_angle_rad[k])
    boresight = np.array([np.cos(z), np.sin(z)], dtype=float)
    omega_body = _omega_body_from_series(series, k)
    return decompose_primary_image_quality(
        sat_pos_xy_km=_sat_xy_at(series, k),
        bore_ground_xy_km=series.camera_ground_center_xy_km[k],
        boresight_dir_unit_xy=boresight,
        gsd_m=float(series.camera_gsd_m[k]),
        theta_orbit_rad=float(series.theta_orbit_rad[k]),
        omega_orbit_rad_s=float(series.metadata.omega_rad_s),
        orbit_radius_km=float(series.radius_km[k]),
        omega_body_rad_s=omega_body,
    )


def print_image_quality_quantity_audit(
    series: SimulationStateSeries,
    *,
    label: str,
    frame_indices: tuple[int, ...] = (0, 50, 100, 200),
    view_anchor_xy_km: tuple[float, float] | None = None,
) -> None:
    """Print model intermediates vs empirical bore ground speed for selected frames."""
    from simulation.attitude_controller import target_boresight_angle_rad

    anchor = (
        np.asarray(view_anchor_xy_km, dtype=float)
        if view_anchor_xy_km is not None
        else None
    )
    print(f"Image quality quantity audit [{label}]")
    print(
        "  k   slant_km  elev_deg  omega_b  v_bore_analytic  v_bore_emp  "
        "anchor_dist_km  track_err_deg  smear  quality"
    )
    bore = series.camera_ground_center_xy_km
    for k in frame_indices:
        if k < 0 or k >= series.t_s.shape[0]:
            continue
        diag = decompose_series_frame(series, k)
        v_emp = (
            bore_ground_speed_m_s(
                bore[k],
                dt_s=float(series.t_s[k] - series.t_s[k - 1]),
                prev_bore_ground_xy_km=bore[k - 1],
            )
            if k > 0
            else float("nan")
        )
        anchor_dist = (
            float(np.linalg.norm(bore[k] - anchor))
            if anchor is not None
            else float("nan")
        )
        track_err = (
            float(
                np.rad2deg(
                    series.body_z_angle_rad[k]
                    - target_boresight_angle_rad(_sat_xy_at(series, k), anchor)
                )
            )
            if anchor is not None
            else float("nan")
        )
        print(
            f"  {k:3d} {diag.slant_range_km:9.3f} {diag.elevation_deg:9.3f} "
            f"{diag.omega_body_rad_s:9.5f} {diag.v_bore_ground_m_s:9.3f} {v_emp:9.3f} "
            f"{anchor_dist:14.3f} {track_err:13.3f} {diag.smear_px:7.4f} {diag.quality:7.4f}"
        )


def print_nadir_vs_target_quantity_audit(*, seed: int = 0) -> None:
    """Compare model terms for scenarios A/B."""
    nadir = run_nadir_pointing_image_quality_gate(seed=seed, fast=True)
    target = run_target_pointing_image_quality_gate(seed=seed, fast=True)
    va = nadir.metadata.view_anchor_xy_km
    last = int(nadir.t_s.shape[0] - 1)
    frames = tuple(i for i in (0, 50, 100, 200, last) if i <= last)
    print_image_quality_quantity_audit(
        nadir, label="A: OBC nadir hold", frame_indices=frames, view_anchor_xy_km=va
    )
    print()
    print_image_quality_quantity_audit(
        target, label="B: OBC target track", frame_indices=frames, view_anchor_xy_km=va
    )
    print()
    _print_locked_frame_speed_summary(nadir, "A nadir", va)
    _print_locked_frame_speed_summary(target, "B target", va)


def _print_locked_frame_speed_summary(
    series: SimulationStateSeries,
    label: str,
    view_anchor_xy_km: tuple[float, float] | None,
) -> None:
    from simulation.attitude_controller import target_boresight_angle_rad

    if view_anchor_xy_km is None:
        return
    anchor = np.asarray(view_anchor_xy_km, dtype=float)
    emps: list[float] = []
    models: list[float] = []
    bore = series.camera_ground_center_xy_km
    for k in range(1, series.t_s.shape[0]):
        err = abs(
            float(
                np.rad2deg(
                    series.body_z_angle_rad[k]
                    - target_boresight_angle_rad(_sat_xy_at(series, k), anchor)
                )
            )
        )
        if err >= 0.5:
            continue
        emps.append(
            bore_ground_speed_m_s(
                bore[k],
                dt_s=float(series.t_s[k] - series.t_s[k - 1]),
                prev_bore_ground_xy_km=bore[k - 1],
            )
        )
        models.append(decompose_series_frame(series, k).v_bore_ground_m_s)
    if not emps:
        print(f"{label}: no frames with |track_err| < 0.5 deg")
        return
    print(
        f"{label}: locked frames n={len(emps)}  "
        f"v_bore_emp mean={float(np.mean(emps)):.2f} m/s  "
        f"v_bore_analytic mean={float(np.mean(models)):.2f} m/s"
    )


def print_image_quality_gate(
    series: SimulationStateSeries,
    *,
    label: str = "rollout",
    max_steps: int = 10,
    stride: int = 1,
) -> None:
    """Print per-step smear, normalized quality, GSD, and applied RW torque."""
    n = min(int(series.t_s.shape[0]), int(max_steps))
    stats = _finite_quality_stats(series)
    tau_stats = _torque_stats(series)
    omega_stats = _body_rate_stats(series)
    print(f"Image quality gate [{label}]: {n} frames shown, stride={stride}")
    print(
        f"  series stats: smear [{stats['smear_min']:.4f}, {stats['smear_max']:.4f}] px  "
        f"quality [{stats['quality_min']:.4f}, {stats['quality_max']:.4f}]"
    )
    print(
        f"  RW torque applied [N·m]: [{tau_stats['tau_min']:+.4f}, {tau_stats['tau_max']:+.4f}]  "
        f"mean {tau_stats['tau_mean']:+.4f}"
    )
    print(
        f"  body z rate [deg/s]: [{omega_stats['omega_deg_s_min']:+.3f}, "
        f"{omega_stats['omega_deg_s_max']:+.3f}]"
    )
    print(
        f"  reference blur for quality=0.5: IMAGE_QUALITY_SMEAR_REFERENCE_M "
        f"({float(IMAGE_QUALITY_SMEAR_REFERENCE_M.to(ureg.m).magnitude):.2f} m)\n"
    )

    for k in range(0, n, stride):
        smear = float(series.camera_image_smear_px[k])
        quality = float(series.camera_image_quality[k])
        gsd = float(series.camera_gsd_m[k])
        tau = float(series.wheel_torque_cmd_nm[k])
        print(
            f"step {k:3d}  smear_px={smear:12.6f}  quality={quality:12.6f}  "
            f"gsd={gsd:8.3f} m  tau={tau:+.4f} N·m"
        )


def print_nadir_vs_target_pointing_gate(
    *,
    seed: int = 0,
    max_steps: int = 20,
) -> tuple[SimulationStateSeries, SimulationStateSeries]:
    """
    Scenarios A/B for image-quality verification.

    A — OBC nadir hold: orbital smear baseline at ω_sat≈0 (~quality 0.28–0.30).
    B — OBC target track: bore locked to view anchor; median quality ~0.9+.
    """
    nadir = run_nadir_pointing_image_quality_gate(seed=seed, fast=True)
    target = run_target_pointing_image_quality_gate(seed=seed, fast=True)

    if nadir.metadata.view_anchor_xy_km is not None:
        print(f"View anchor (target track): {nadir.metadata.view_anchor_xy_km} km\n")

    print_image_quality_gate(nadir, label="A: OBC nadir hold", max_steps=max_steps, stride=max(1, max_steps // 10))
    print()
    print_image_quality_gate(
        target, label="B: OBC target track", max_steps=max_steps, stride=max(1, max_steps // 10)
    )

    nadir_stats = _finite_quality_stats(nadir)
    target_stats = _finite_quality_stats(target)
    print(
        f"\nScenario comparison:"
        f"\n  A nadir  quality [{nadir_stats['quality_min']:.4f}, {nadir_stats['quality_max']:.4f}]  "
        f"smear [{nadir_stats['smear_min']:.4f}, {nadir_stats['smear_max']:.4f}] px"
        f"\n  B target quality [{target_stats['quality_min']:.4f}, {target_stats['quality_max']:.4f}]  "
        f"smear [{target_stats['smear_min']:.4f}, {target_stats['smear_max']:.4f}] px"
        f"\n  (expect B quality > A; target track residual smear from tracking error)"
    )
    return nadir, target


def export_image_quality_video(
    series: SimulationStateSeries,
    out_path: Path | str,
    *,
    width: int = 680,
) -> Path:
    """Export episode MP4; telemetry panel shows per-frame image quality."""
    from utils.notebook.video import export_and_play_saved_video

    path = export_and_play_saved_video(simulation_series=series, out_path=Path(out_path), width=width)
    print(f"artifact={path}")
    return path
