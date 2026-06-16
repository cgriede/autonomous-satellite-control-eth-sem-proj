"""Notebook verification for take-picture capture mode and quality-based reward."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np

from autonomous_control.reward import RewardConfig, RewardSignals, compute_reward
from environment_definition.constants.AUTONOMOUS_CONTROL_REWARD import (
    REWARD_IMAGE_QUALITY_CAPTURE_WEIGHT,
)
from environment_definition.constants.SATELLITE import MAX_PRIMARY_CAPTURES_PER_ORBIT
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from simulation.capture_reward import (
    applied_capture_reward_series,
    capture_time_windows_s,
    cloud_fraction_at_index,
    latent_capture_reward_series,
)
from simulation.capture_target import (
    dominant_capture_target_index,
    primary_target_pixel_coverage,
    target_visible_from_codes,
)
from simulation.setup_types import OrbitConfig
from simulation.state_types import SimulationStateSeries
from simulation.take_picture import (
    TakePictureBudget,
    TakePictureConfig,
    resolve_capture_frame_index,
)

from s01_utils import image_quality_verification as iqv

# Verification-only: seed=0 fast polar pass, clouds disabled (see build_take_picture_verification_setup).
TAKE_PICTURE_VERIFICATION_SEED = 0

# Scenario C: wider orbit window → longer overpass, slant range varies more along track.
SCENARIO_C_ORBIT_START_DEG = -12.0
SCENARIO_C_ORBIT_END_DEG = 12.0
SCENARIO_C_N_COMMANDS = 20


def build_take_picture_verification_setup(*, seed: int = TAKE_PICTURE_VERIFICATION_SEED):
    """
    Deterministic easy-mode setup for notebook 06 (no clouds; same orbit window as IQ gate).

    Production / agent training keeps mission clouds; this helper is verification-only.
    """
    return replace(
        iqv.build_fast_image_quality_setup(seed=seed, include_cameras=True),
        clouds=(),
    )


def build_wide_overflight_verification_setup(
    *,
    seed: int = TAKE_PICTURE_VERIFICATION_SEED,
    start_angle_deg: float = SCENARIO_C_ORBIT_START_DEG,
    end_angle_deg: float = SCENARIO_C_ORBIT_END_DEG,
):
    """Scenario C: cloud-free pass with a wider orbit arc (longer overflight, larger slant range swing)."""
    setup = build_take_picture_verification_setup(seed=seed)
    if setup.orbit is None:
        raise ValueError("verification setup requires orbit config")
    orbit = OrbitConfig(
        altitude=setup.orbit.altitude,
        start_angle_deg=float(start_angle_deg),
        end_angle_deg=float(end_angle_deg),
        motion_span_scale=setup.orbit.motion_span_scale,
        sat_z_offset=setup.orbit.sat_z_offset,
    )
    return replace(setup, orbit=orbit)


def _run_take_picture_rollout(setup, *, obc_pointing_mode: str) -> SimulationStateSeries:
    label = f"take_picture_obc_{obc_pointing_mode}"
    return iqv._run_rollout(
        setup,
        simulation_config=iqv.image_quality_simulation_config(
            obc_pointing_mode=obc_pointing_mode,  # type: ignore[arg-type]
            torque_policy_label=label,
        ),
    )


def resolve_verification_capture_step(
    target_series: SimulationStateSeries,
    nadir_series: SimulationStateSeries,
) -> int:
    """
    Orbit step for take-picture verification: over the target stripe on both rollouts.

    Picks the frame where the primary strip sees the target on **both** series and
    target-track image quality is highest (OBC locked, low smear).
    """
    n = min(int(target_series.t_s.shape[0]), int(nadir_series.t_s.shape[0]))
    best_k = -1
    best_q = -1.0
    for k in range(n):
        if not _target_visible_at_frame(target_series, k):
            continue
        if not _target_visible_at_frame(nadir_series, k):
            continue
        q = float(target_series.camera_image_quality[k])
        if np.isfinite(q) and q > best_q:
            best_q = q
            best_k = k
    if best_k < 0:
        raise ValueError(
            "take-picture verification: no frame with target in primary strip on both rollouts"
        )
    return best_k


@dataclass(frozen=True)
class CaptureResult:
    cmd_step: int
    capture_step: int | None
    picture_taken: bool
    target_visible: bool
    target_coverage: float
    quality: float
    cloud_frac: float
    dominant_target_index: int | None
    capture_target_novel: bool
    latent_reward: float
    capture_reward: float
    budget_remaining: int


@dataclass(frozen=True)
class TakePictureVerificationContext:
    """Rollouts + capture schedule used by the notebook 06 numeric and video gates."""

    nadir_series: SimulationStateSeries
    target_series: SimulationStateSeries
    cmd_steps: tuple[int, ...]
    capture_step: int
    nadir_captures: list[CaptureResult]
    target_captures: list[CaptureResult]


@dataclass(frozen=True)
class ScenarioCBudgetExhaustionContext:
    """Scenario C: OBC target track on wide overflight with budget+1 shutter commands."""

    series: SimulationStateSeries
    cmd_steps: tuple[int, ...]
    captures: list[CaptureResult]
    orbit_start_deg: float
    orbit_end_deg: float


def _target_visible_at_frame(series: SimulationStateSeries, k: int) -> bool:
    return target_visible_from_codes(series.camera_observation_line_codes[k])


def _dominant_target_at_frame(series: SimulationStateSeries, k: int) -> int | None:
    return dominant_capture_target_index(series.camera_observation_line_codes[k])


def evaluate_capture_at_step(
    series: SimulationStateSeries,
    *,
    cmd_step: int,
    budget: TakePictureBudget,
    reward_config: RewardConfig | None = None,
    capture_latency_steps: int = 0,
) -> CaptureResult:
    """Apply one take-picture command; reward uses quality at the resolved capture frame."""
    cfg = reward_config or RewardConfig(
        enable_distance_reward=False,
        enable_image_quality_capture=True,
    )
    capture_k = resolve_capture_frame_index(
        cmd_step=cmd_step,
        n_steps=int(series.t_s.shape[0]),
        capture_latency_steps=capture_latency_steps,
    )
    dominant: int | None = None
    if capture_k is not None:
        dominant = _dominant_target_at_frame(series, capture_k)
        taken, capture_target_novel = budget.attempt_capture(dominant)
    else:
        taken = False
        capture_target_novel = False
    quality = (
        float(series.camera_image_quality[capture_k])
        if capture_k is not None
        else float("nan")
    )
    cloud = cloud_fraction_at_index(series, capture_k) if capture_k is not None else 0.0
    visible = dominant is not None
    coverage = (
        primary_target_pixel_coverage(
            series.camera_observation_line_codes[capture_k],
            target_index=dominant,
        )
        if capture_k is not None
        else 0.0
    )
    q = quality if np.isfinite(quality) else 0.0
    signals = RewardSignals(
        distance_to_target=0.0 * ureg.km,
        picture_taken=taken,
        capture_target_novel=capture_target_novel,
        target_visible=visible,
        camera_image_quality=q,
        primary_target_pixel_coverage=coverage,
        camera_cloud_blocked_fraction=cloud,
    )
    _total, components = compute_reward(signals=signals, cfg=cfg)
    latent = float(components["latent_capture_reward"])
    return CaptureResult(
        cmd_step=int(cmd_step),
        capture_step=capture_k,
        picture_taken=taken,
        target_visible=visible,
        target_coverage=coverage,
        quality=quality,
        cloud_frac=cloud,
        dominant_target_index=dominant,
        capture_target_novel=capture_target_novel,
        latent_reward=latent,
        capture_reward=float(components["image_quality_capture_reward"]),
        budget_remaining=int(budget.remaining),
    )


def resolve_evenly_spaced_cmd_steps(
    series: SimulationStateSeries,
    n_commands: int,
    *,
    require_target_visible: bool = True,
) -> tuple[int, ...]:
    """Pick ``n_commands`` sim steps evenly across the episode (optionally target-visible only)."""
    n = int(series.t_s.shape[0])
    if require_target_visible:
        pool = [k for k in range(n) if _target_visible_at_frame(series, k)]
    else:
        pool = list(range(n))
    if len(pool) < n_commands:
        raise ValueError(
            f"need {n_commands} take-picture commands but only {len(pool)} qualifying frames"
        )
    if n_commands == 1:
        return (pool[len(pool) // 2],)
    picks = np.linspace(0, len(pool) - 1, n_commands)
    return tuple(int(pool[int(round(i))]) for i in picks)


def evaluate_capture_schedule(
    series: SimulationStateSeries,
    *,
    cmd_steps: tuple[int, ...],
    max_pictures: int = MAX_PRIMARY_CAPTURES_PER_ORBIT,
    capture_latency_steps: int = 0,
) -> list[CaptureResult]:
    budget = TakePictureBudget.from_config(TakePictureConfig(max_pictures_per_episode=max_pictures))
    return [
        evaluate_capture_at_step(
            series,
            cmd_step=step,
            budget=budget,
            capture_latency_steps=capture_latency_steps,
        )
        for step in cmd_steps
    ]


def print_capture_results(label: str, results: list[CaptureResult]) -> None:
    print(f"Take-picture capture gate [{label}]")
    print(
        f"  budget={MAX_PRIMARY_CAPTURES_PER_ORBIT}  "
        f"k_capture={REWARD_IMAGE_QUALITY_CAPTURE_WEIGHT:.0f}  "
        f"latent = k * coverage * quality * (1 - cloud_frac)  "
        f"(applied only on novel target shutter)\n"
    )
    print(
        "  cmd  cap  taken  novel  tgt  cov    quality  cloud   latent  applied  budget_left"
    )
    for r in results:
        cap = "—" if r.capture_step is None else f"{r.capture_step:3d}"
        tgt = "—" if r.dominant_target_index is None else f"T{r.dominant_target_index}"
        print(
            f"  {r.cmd_step:3d}  {cap}  "
            f"{'yes' if r.picture_taken else ' no'}     "
            f"{'yes' if r.capture_target_novel else ' no'}     "
            f"{tgt:>3}  {r.target_coverage:5.3f}  {r.quality:7.4f}  {r.cloud_frac:5.3f}  "
            f"{r.latent_reward:7.2f}  {r.capture_reward:7.2f}  {r.budget_remaining:3d}"
        )
    taken = [r for r in results if r.picture_taken]
    if taken:
        print(
            f"\n  captures={len(taken)}  "
            f"total_capture_reward={sum(r.capture_reward for r in taken):.2f}  "
            f"mean_quality={float(np.mean([r.quality for r in taken if np.isfinite(r.quality)])):.4f}"
        )


def build_take_picture_verification_context(
    *,
    seed: int = TAKE_PICTURE_VERIFICATION_SEED,
) -> TakePictureVerificationContext:
    """
    Run nadir/target rollouts without clouds; one capture at the target overpass step.
    """
    setup = build_take_picture_verification_setup(seed=seed)
    nadir = _run_take_picture_rollout(setup, obc_pointing_mode="nadir")
    target = _run_take_picture_rollout(setup, obc_pointing_mode="target")
    capture_step = resolve_verification_capture_step(target, nadir)
    cmd_steps = (capture_step,)
    nadir_captures = evaluate_capture_schedule(nadir, cmd_steps=cmd_steps)
    target_captures = evaluate_capture_schedule(target, cmd_steps=cmd_steps)
    return TakePictureVerificationContext(
        nadir_series=nadir,
        target_series=target,
        cmd_steps=cmd_steps,
        capture_step=capture_step,
        nadir_captures=nadir_captures,
        target_captures=target_captures,
    )


def print_take_picture_verification_context(ctx: TakePictureVerificationContext) -> None:
    """Print capture tables and scenario comparison from a pre-built context."""
    print_capture_results("A: OBC nadir hold", ctx.nadir_captures)
    print()
    print_capture_results("B: OBC target track", ctx.target_captures)

    nadir_sum = sum(r.capture_reward for r in ctx.nadir_captures if r.picture_taken)
    target_sum = sum(r.capture_reward for r in ctx.target_captures if r.picture_taken)
    print(
        f"\nScenario comparison: nadir capture reward total={nadir_sum:.2f}  "
        f"target capture reward total={target_sum:.2f}  (expect target > nadir at overpass)"
    )
    target_cap = next(r for r in ctx.target_captures if r.cmd_step == ctx.capture_step)
    nadir_cap = next(r for r in ctx.nadir_captures if r.cmd_step == ctx.capture_step)
    print(
        f"Capture at step {ctx.capture_step}  "
        f"t={float(ctx.target_series.t_s[ctx.capture_step]):.1f} s  "
        f"(clouds off; stripe visible on both rollouts)"
    )
    print(
        f"Latent at shutter: target track={target_cap.latent_reward:.2f}  "
        f"nadir hold={nadir_cap.latent_reward:.2f}  "
        f"(expect target > nadir; latent > 0 when bore on target)"
    )


def print_take_picture_reward_gate(
    *,
    seed: int = TAKE_PICTURE_VERIFICATION_SEED,
) -> TakePictureVerificationContext:
    """
    Compare capture rewards on nadir-hold vs target-track at the target overpass step.

    Uses cloud-free verification setup; target track should earn higher capture credit.
    """
    ctx = build_take_picture_verification_context(seed=seed)
    print_take_picture_verification_context(ctx)
    return ctx


def export_take_picture_verification_videos(
    ctx: TakePictureVerificationContext,
    out_dir: Path | str,
    *,
    width: int = 680,
) -> dict[str, Path]:
    """
    Export proof MP4s for notebook 06; telemetry shows per-frame image quality.

    Reuses the same rollouts as the numeric gate (no second simulation).
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    exports: dict[str, Path] = {}
    for filename, series, label in (
        ("06-take-picture-nadir-hold.mp4", ctx.nadir_series, "A nadir hold"),
        ("06-take-picture-target-track.mp4", ctx.target_series, "B target track"),
    ):
        path = out / filename
        print(f"Exporting {filename} [{label}]  capture step={ctx.capture_step}  t={float(series.t_s[ctx.capture_step]):.1f}s")
        series_for_render = replace(
            series,
            metadata=replace(series.metadata, take_picture_cmd_steps=ctx.cmd_steps),
        )
        exports[filename] = iqv.export_image_quality_video(series_for_render, path, width=width)
    return exports


def plot_capture_reward_timeline(
    series: SimulationStateSeries,
    *,
    cmd_steps: tuple[int, ...],
    label: str = "rollout",
    capture_latency_steps: int = 0,
    ax=None,
):
    """Latent vs applied reward; pink vertical marks = take-picture command times."""
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    cmd_color = "deeppink"
    t_s = np.asarray(series.t_s, dtype=float)
    latent = latent_capture_reward_series(series)
    applied = applied_capture_reward_series(
        series,
        cmd_steps=cmd_steps,
        capture_latency_steps=capture_latency_steps,
    )
    if ax is None:
        _, ax = plt.subplots(figsize=(9, 3.2))

    windows = capture_time_windows_s(
        series,
        cmd_steps,
        capture_latency_steps=capture_latency_steps,
    )
    for t0, t1 in windows:
        ax.axvspan(t0, t1, color=cmd_color, alpha=0.22, linewidth=0, zorder=0)
        ax.axvline(t0, color=cmd_color, alpha=0.85, linewidth=1.2, zorder=1)

    (latent_line,) = ax.plot(t_s, latent, color="cyan", linewidth=1.2, label="latent")
    (applied_line,) = ax.plot(
        t_s, applied, color="gold", linewidth=1.0, drawstyle="steps-post", label="applied"
    )
    ax.set_title(f"Reward [{label}]")
    ax.set_xlabel("time [s]")
    ax.set_ylabel("reward")
    ax.grid(True, alpha=0.25)
    handles = [latent_line, applied_line]
    if windows:
        handles.append(
            Patch(facecolor=cmd_color, alpha=0.35, edgecolor=cmd_color, label="take picture")
        )
    ax.legend(handles=handles, loc="upper right", fontsize=8)
    ymax = float(np.nanmax(latent)) if latent.size else 1.0
    ax.set_ylim(0.0, max(ymax * 1.1, 1.0))
    return ax


def build_scenario_c_budget_exhaustion_context(
    *,
    seed: int = TAKE_PICTURE_VERIFICATION_SEED,
    start_angle_deg: float = SCENARIO_C_ORBIT_START_DEG,
    end_angle_deg: float = SCENARIO_C_ORBIT_END_DEG,
    n_commands: int = SCENARIO_C_N_COMMANDS,
) -> ScenarioCBudgetExhaustionContext:
    """
    Scenario C: OBC target track, wide overflight, many take-picture commands (default 20).

    Expect at most ``MAX_PRIMARY_CAPTURES_PER_ORBIT`` accepted captures; extras are rejected.
    Repeat target index → shutter consumed but applied reward 0.
    """
    setup = build_wide_overflight_verification_setup(
        seed=seed,
        start_angle_deg=start_angle_deg,
        end_angle_deg=end_angle_deg,
    )
    series = _run_take_picture_rollout(setup, obc_pointing_mode="target")
    cmd_steps = resolve_evenly_spaced_cmd_steps(series, n_commands)
    captures = evaluate_capture_schedule(series, cmd_steps=cmd_steps)
    return ScenarioCBudgetExhaustionContext(
        series=series,
        cmd_steps=cmd_steps,
        captures=captures,
        orbit_start_deg=float(start_angle_deg),
        orbit_end_deg=float(end_angle_deg),
    )


def print_scenario_c_budget_exhaustion_context(ctx: ScenarioCBudgetExhaustionContext) -> None:
    """Print scenario C capture table and budget-exhaustion summary."""
    print(
        f"Scenario C: OBC target track  orbit=[{ctx.orbit_start_deg:.0f}, {ctx.orbit_end_deg:.0f}] deg  "
        f"commands={len(ctx.cmd_steps)}  budget={MAX_PRIMARY_CAPTURES_PER_ORBIT}"
    )
    print_capture_results("C: wide overflight / budget+1 commands", ctx.captures)
    taken = [r for r in ctx.captures if r.picture_taken]
    rejected = [r for r in ctx.captures if not r.picture_taken]
    novel = [r for r in ctx.captures if r.capture_target_novel]
    repeat = [r for r in taken if not r.capture_target_novel]
    print(
        f"\n  shutters accepted={len(taken)}  rejected={len(rejected)}  "
        f"novel={len(novel)}  repeat_wasted={len(repeat)}  "
        f"(budget={MAX_PRIMARY_CAPTURES_PER_ORBIT}; applied only on first capture per target index)"
    )
    if rejected:
        r = rejected[0]
        print(
            f"  first rejected cmd step={r.cmd_step}  latent={r.latent_reward:.2f}  "
            f"applied={r.capture_reward:.2f}  budget_left={r.budget_remaining}"
        )
    quality = np.asarray(ctx.series.camera_image_quality, dtype=float)
    finite_q = quality[np.isfinite(quality)]
    if finite_q.size:
        print(
            f"  episode quality range [{float(np.min(finite_q)):.3f}, {float(np.max(finite_q)):.3f}]  "
            f"(wider pass → larger slant-range swing)"
        )


def print_scenario_c_budget_gate(
    *,
    seed: int = TAKE_PICTURE_VERIFICATION_SEED,
) -> ScenarioCBudgetExhaustionContext:
    ctx = build_scenario_c_budget_exhaustion_context(seed=seed)
    print_scenario_c_budget_exhaustion_context(ctx)
    return ctx


def export_scenario_c_video(
    ctx: ScenarioCBudgetExhaustionContext,
    out_dir: Path | str,
    *,
    width: int = 680,
    filename: str = "06-take-picture-scenario-c-budget.mp4",
) -> Path:
    """Export scenario C MP4 with all shutter bands on the live reward panel."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / filename
    print(
        f"Exporting {filename} [C wide target track]  "
        f"commands={len(ctx.cmd_steps)}  n_frames={int(ctx.series.t_s.shape[0])}"
    )
    series_for_render = replace(
        ctx.series,
        metadata=replace(ctx.series.metadata, take_picture_cmd_steps=ctx.cmd_steps),
    )
    return iqv.export_image_quality_video(series_for_render, path, width=width)


def print_budget_exhaustion_demo(*, seed: int = TAKE_PICTURE_VERIFICATION_SEED) -> None:
    """Issue more commands than budget allows; extra commands yield zero capture reward."""
    setup = build_take_picture_verification_setup(seed=seed)
    nadir = _run_take_picture_rollout(setup, obc_pointing_mode="nadir")
    target = _run_take_picture_rollout(setup, obc_pointing_mode="target")
    capture_step = resolve_verification_capture_step(target, nadir)
    n = int(target.t_s.shape[0])
    cmd_steps = (capture_step,) + tuple(range(0, n, max(1, n // 15)))
    cmd_steps = tuple(dict.fromkeys(cmd_steps))
    results = evaluate_capture_schedule(target, cmd_steps=cmd_steps, max_pictures=3)
    print_capture_results("budget exhaustion (max 3 captures)", results)
    rejected = [r for r in results if not r.picture_taken]
    print(f"\n  commands after budget exhausted: {len(rejected)} (reward=0 for each)")
