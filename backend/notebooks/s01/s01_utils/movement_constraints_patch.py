"""S01 notebook helpers: attitude safety patch, delayed-violation rollout, MP4 export."""

from __future__ import annotations

import math
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
from gymnasium import spaces

from autonomous_control.controller_baselines import DelayedMaxTorquePolicy
from environment_definition.constants.ATTITUDE_SAFETY import NADIR_RECOVERY_TOLERANCE_DEG
from environment_definition.constants.SATELLITE import REACTION_WHEEL_MAX_TORQUE
from environment_definition.constants.SIMULATION import RenderMode, SimulationConfig
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from environment_definition.mission_profiles.s01_multiple_targets_fwd_fish import (
    build_setup,
    sample_satellite_altitude,
)
from simulation.attitude_controller import AttitudeSafetyConfig, AttitudeSafetyController
from simulation.camera_2d import off_nadir_angle_rad
from simulation.setup_types import OrbitConfig, SimulationOverrides
from simulation.state_types import SimulationStateSeries
from simulation.stepper import SimulationStepper
from simulation.stepper_factory import build_stepper
from utils.geometry.polar_meridian_track import build_target_grid_polar_meridian

def _movement_orbit_config() -> OrbitConfig:
    base = build_setup(seed=0, include_cameras=False).orbit
    alt = base.altitude if base is not None and base.altitude is not None else sample_satellite_altitude(seed=0)
    return OrbitConfig(
        altitude=alt,
        start_angle_deg=-4.0,
        end_angle_deg=4.0,
        motion_span_scale=1.05,
        sat_z_offset=0 * ureg.deg,
    )
_MIN_SIM_TOTAL_S = 30.0


def _single_target_grid():
    segments = build_target_grid_polar_meridian(
        n_targets=1,
        target_size=20 * ureg.km,
        spacing=40 * ureg.km,
        anchor_lat=85 * ureg.deg,
    )
    return tuple(s.to_observation_target_area() for s in segments)


def build_fast_movement_setup(*, seed: int = 0, include_cameras: bool = False):
    """HEADLESS iteration setup (cells 3–6)."""
    overrides = SimulationOverrides(camera_pixel_ray_samples=16) if include_cameras else None
    return replace(
        build_setup(seed=seed, include_cameras=include_cameras),
        clouds=(),
        target_areas=_single_target_grid(),
        orbit=_movement_orbit_config(),
        simulation_overrides=overrides,
    )


def build_movement_video_setup(*, seed: int = 0):
    """Camera-enabled setup for required MP4 gate."""
    return build_fast_movement_setup(seed=seed, include_cameras=True)


def _make_policy_env(*, tau_max_nm: float, dt_s: float) -> Any:
    class _Env:
        pass

    env = _Env()
    env.action_space = spaces.Box(
        low=np.array([-tau_max_nm], dtype=np.float32),
        high=np.array([tau_max_nm], dtype=np.float32),
        shape=(1,),
        dtype=np.float32,
    )
    env.dt = dt_s * ureg.s
    return env


def patch_stepper(
    stepper: SimulationStepper,
    *,
    config: AttitudeSafetyConfig | None = None,
    tau_max_nm: float | None = None,
) -> AttitudeSafetyController:
    """Enable canonical stepper attitude safety (no monkeypatch)."""
    del tau_max_nm  # uses satellite torque from stepper
    controller = stepper.enable_attitude_safety(config=config)
    stepper.attitude_safety_events = []
    return controller


def unpatch_stepper(stepper: SimulationStepper) -> None:
    stepper._attitude_safety = None
    stepper.attitude_safety_events = []


def run_policy_rollout(
    stepper: SimulationStepper,
    policy: Any,
    *,
    print_events: bool = True,
    show_progress: bool = False,
) -> tuple[SimulationStateSeries, list[dict[str, Any]]]:
    """Per-step policy loop (ignores controller update interval)."""
    from tqdm import tqdm

    if hasattr(policy, "reset_episode"):
        policy.reset_episode()
    stepper.attitude_safety_events = []

    total_steps = max(0, int(stepper._t_s.shape[0]) - 1)  # type: ignore[attr-defined]
    pbar = tqdm(total=total_steps, desc="movement rollout", disable=not show_progress)
    while not stepper.done:
        ts = stepper.current_timestep_state()
        if hasattr(policy, "set_sim_time_s"):
            policy.set_sim_time_s(ts.sim_time_s)
        action = policy.get_action(np.zeros(1, dtype=np.float64), train=False)
        torque_cmd_nm = float(np.asarray(action, dtype=np.float64).reshape(-1)[0])
        stepper.step(wheel_torque_cmd_nm=torque_cmd_nm)
        if print_events and stepper.attitude_safety_events:
            events = stepper.attitude_safety_events
            if events and events[-1]["step"] == ts.step_idx:
                rec = events[-1]
                print(
                    f"{rec['event']} step={rec['step']} t={rec['t_s']:.1f}s "
                    f"off_nadir={rec['off_nadir_deg']:.1f}deg "
                    f"cmd={rec['cmd_nm']:.3f} out={rec['out_nm']:.3f}"
                )
        if pbar.n < total_steps:
            pbar.update(1)
    pbar.close()
    return stepper.finalize_series(), list(stepper.attitude_safety_events)


def max_off_nadir_deg_series(series: SimulationStateSeries) -> np.ndarray:
    n = series.t_s.shape[0]
    out = np.zeros(n, dtype=float)
    for k in range(n):
        sat_xy = np.array(
            [
                series.radius_km[k] * np.cos(series.theta_orbit_rad[k]),
                series.radius_km[k] * np.sin(series.theta_orbit_rad[k]),
            ],
            dtype=float,
        )
        body_z = float(series.body_z_angle_rad[k])
        bore = np.array([np.cos(body_z), np.sin(body_z)], dtype=float)
        out[k] = math.degrees(off_nadir_angle_rad(sat_xy, bore))
    return out


def print_movement_verification_summary(
    series: SimulationStateSeries,
    events: list[dict[str, Any]],
    *,
    delay_s: float = 5.0,
) -> dict[str, Any]:
    off_deg = max_off_nadir_deg_series(series)
    max_off = float(np.max(off_deg))
    warnings = [e for e in events if e["event"] == "SAFETY_WARNING"]
    takeovers = [e for e in events if e["event"] == "SAFE_MODE_TAKEOVER"]
    lockouts = [e for e in events if e["event"] == "LOCKOUT_ACTIVE"]
    exits = [e for e in events if e["event"] == "SAFE_MODE_EXIT"]
    sim_total = float(series.metadata.sim_total_s)
    final_off = float(off_deg[-1]) if off_deg.size else 0.0
    tol_deg = float(NADIR_RECOVERY_TOLERANCE_DEG.to(ureg.deg).magnitude)
    lockout_off = float(lockouts[0]["off_nadir_deg"]) if lockouts else final_off

    print("Movement verification summary")
    print(f"  sim_total_s:     {sim_total:.1f}")
    print(f"  t_coast_end:     {delay_s:.1f}s")
    print(f"  max_off_nadir:   {max_off:.2f} deg")
    print(f"  final_off_nadir: {final_off:.2f} deg")
    print(f"  lockout_off_nadir: {lockout_off:.2f} deg")
    print(f"  n_warnings:      {len(warnings)}")
    print(f"  n_takeover:      {len(takeovers)}")
    print(f"  n_lockout_steps: {len(lockouts)}")
    print(f"  n_safe_exit:     {len(exits)}")
    if warnings:
        w0 = warnings[0]
        print(f"  first_warning:   step={w0['step']} t={w0['t_s']:.1f}s")
    if takeovers:
        t0 = takeovers[0]
        print(f"  takeover:        step={t0['step']} t={t0['t_s']:.1f}s")
    if lockouts:
        l0 = lockouts[0]
        print(f"  lockout_start:   step={l0['step']} t={l0['t_s']:.1f}s")

    envelope_ok = max_off <= 45.0 + 0.5
    takeover_ok = len(takeovers) >= 1
    lockout_ok = len(lockouts) >= 1
    recovery_ok = lockout_off <= tol_deg + 0.5
    if envelope_ok and takeover_ok and lockout_ok and recovery_ok:
        print("PASS: envelope + takeover + lockout + recovery")
    else:
        print(
            f"FAIL: envelope_ok={envelope_ok} takeover_ok={takeover_ok} "
            f"lockout_ok={lockout_ok} recovery_ok={recovery_ok}"
        )

    return {
        "max_off_nadir_deg": max_off,
        "final_off_nadir_deg": final_off,
        "lockout_off_nadir_deg": lockout_off,
        "n_warnings": len(warnings),
        "n_takeover": len(takeovers),
        "n_lockout": len(lockouts),
        "takeover_step": takeovers[0]["step"] if takeovers else None,
        "lockout_step": lockouts[0]["step"] if lockouts else None,
        "envelope_ok": envelope_ok,
        "takeover_ok": takeover_ok,
        "lockout_ok": lockout_ok,
        "recovery_ok": recovery_ok,
    }


def movement_simulation_config(
    *,
    torque_policy_label: str = "delayed_max_torque",
    attitude_controller_enabled: bool = True,
    render_mode: RenderMode = RenderMode.HEADLESS,
) -> SimulationConfig:
    """HEADLESS config for notebook 03: external policy + optional attitude controller."""
    return SimulationConfig(
        render_mode=render_mode,
        torque_command_source="external",
        torque_policy_label=torque_policy_label,
        attitude_controller_enabled=attitude_controller_enabled,
    )


def build_movement_stepper(
    setup,
    *,
    simulation_config: SimulationConfig | None = None,
    patch: bool = True,
) -> tuple[SimulationStepper, AttitudeSafetyController | None]:
    sim_cfg = simulation_config or movement_simulation_config(
        attitude_controller_enabled=patch,
    )
    resolved = setup.resolve(require_camera=bool(setup.cameras))
    stepper = build_stepper(resolved, simulation_config=sim_cfg)
    sim_total = float(stepper._metadata.sim_total_s)  # type: ignore[attr-defined]
    if sim_total < _MIN_SIM_TOTAL_S:
        raise ValueError(
            f"Movement setup sim_total_s={sim_total:.1f} < {_MIN_SIM_TOTAL_S}; widen OrbitConfig."
        )
    controller = stepper._attitude_safety if patch else None
    if patch and controller is None:
        controller = patch_stepper(stepper)
    return stepper, controller


def make_delayed_max_policy(stepper: SimulationStepper, *, delay_s: float = 5.0, tau_scale: float = 1.0):
    tau_max_nm = float(REACTION_WHEEL_MAX_TORQUE.to(ureg.N * ureg.m).magnitude)
    env = _make_policy_env(tau_max_nm=tau_max_nm, dt_s=float(stepper._sim_dt_s))  # type: ignore[attr-defined]
    return DelayedMaxTorquePolicy(env, delay_s=delay_s, tau_scale=tau_scale)


def export_movement_verification_video(
    series: SimulationStateSeries,
    out_path: Path | str | None = None,
    *,
    play: bool = False,
) -> Path:
    from utils.notebook.video import _export_render_video, play_saved_video

    if out_path is None:
        out_path = (
            Path(__file__).resolve().parents[1]
            / "artifacts"
            / "movement_constraints_delayed_max.mp4"
        )
    path = _export_render_video(simulation_series=series, out_path=Path(out_path))
    if play:
        play_saved_video(path)
    return path
