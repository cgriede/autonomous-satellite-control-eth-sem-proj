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
from environment_definition.constants.SIMULATION import OBSERVATION_TARGET
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from simulation.state_types import SimulationStateSeries
from simulation.take_picture import TakePictureBudget, TakePictureConfig, resolve_capture_frame_index

from s01_utils import image_quality_verification as iqv

# Verification-only: seed=0 fast polar pass, clouds disabled (see build_take_picture_verification_setup).
TAKE_PICTURE_VERIFICATION_SEED = 0


def build_take_picture_verification_setup(*, seed: int = TAKE_PICTURE_VERIFICATION_SEED):
    """
    Deterministic easy-mode setup for notebook 06 (no clouds; same orbit window as IQ gate).

    Production / agent training keeps mission clouds; this helper is verification-only.
    """
    return replace(
        iqv.build_fast_image_quality_setup(seed=seed, include_cameras=True),
        clouds=(),
    )


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
    quality: float
    cloud_frac: float
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


def _target_visible_at_frame(series: SimulationStateSeries, k: int) -> bool:
    codes = np.asarray(series.camera_observation_line_codes[k], dtype=np.int8)
    return bool(np.any(codes == np.int8(OBSERVATION_TARGET)))


def _cloud_fraction_at_frame(series: SimulationStateSeries, k: int) -> float:
    cloud = float(series.camera_cloud_blocked_fraction[k])
    return 0.0 if not np.isfinite(cloud) else float(np.clip(cloud, 0.0, 1.0))


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
    taken = budget.try_capture() if capture_k is not None else False
    quality = (
        float(series.camera_image_quality[capture_k])
        if capture_k is not None
        else float("nan")
    )
    cloud = _cloud_fraction_at_frame(series, capture_k) if capture_k is not None else 0.0
    visible = _target_visible_at_frame(series, capture_k) if capture_k is not None else False
    signals = RewardSignals(
        distance_to_target=0.0 * ureg.km,
        picture_taken=taken,
        target_visible=visible,
        camera_image_quality=quality if np.isfinite(quality) else 0.0,
        camera_cloud_blocked_fraction=cloud,
    )
    _total, components = compute_reward(signals=signals, cfg=cfg)
    return CaptureResult(
        cmd_step=int(cmd_step),
        capture_step=capture_k,
        picture_taken=taken,
        target_visible=visible,
        quality=quality,
        cloud_frac=cloud,
        capture_reward=float(components["image_quality_capture_reward"]),
        budget_remaining=int(budget.remaining),
    )


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
        f"reward = k * quality * (1 - cloud_frac)\n"
    )
    print("  cmd  cap  taken  visible  quality  cloud   reward  budget_left")
    for r in results:
        cap = "—" if r.capture_step is None else f"{r.capture_step:3d}"
        print(
            f"  {r.cmd_step:3d}  {cap}  "
            f"{'yes' if r.picture_taken else ' no'}     "
            f"{'yes' if r.target_visible else ' no'}      "
            f"{r.quality:7.4f}  {r.cloud_frac:5.3f}  {r.capture_reward:7.2f}  {r.budget_remaining:3d}"
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
    print(
        f"Capture at step {ctx.capture_step}  "
        f"t={float(ctx.target_series.t_s[ctx.capture_step]):.1f} s  "
        f"(clouds off; stripe visible on both rollouts)"
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
        exports[filename] = iqv.export_image_quality_video(series, path, width=width)
    return exports


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
