"""Take-picture command budget and discrete capture frame resolution."""

from __future__ import annotations

from dataclasses import dataclass, field

from environment_definition.constants.SATELLITE import CAMERA_EXPOSURE_TIME, MAX_PRIMARY_CAPTURES_PER_ORBIT
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg


@dataclass(frozen=True)
class TakePictureConfig:
    """Episode-level shutter / downlink budget."""

    max_pictures_per_episode: int = MAX_PRIMARY_CAPTURES_PER_ORBIT


@dataclass
class TakePictureBudget:
    """Remaining shutter slots and per-target novelty for one episode."""

    remaining: int
    captured_target_indices: set[int] = field(default_factory=set)

    @classmethod
    def from_config(cls, config: TakePictureConfig | None = None) -> TakePictureBudget:
        cfg = config or TakePictureConfig()
        return cls(remaining=int(cfg.max_pictures_per_episode))

    def attempt_capture(self, target_index: int | None) -> tuple[bool, bool]:
        """
        Try to fire the shutter on ``target_index`` (``None`` = no target in FOV).

        Returns ``(shutter_accepted, reward_eligible)``. Repeat captures of the same
        target index consume budget but are not reward-eligible.
        """
        if self.remaining <= 0:
            return False, False
        self.remaining -= 1
        if target_index is None:
            return True, False
        idx = int(target_index)
        if idx in self.captured_target_indices:
            return True, False
        self.captured_target_indices.add(idx)
        return True, True

    def try_capture(self) -> bool:
        """Consume one slot without target novelty tracking (legacy budget tests)."""
        if self.remaining <= 0:
            return False
        self.remaining -= 1
        return True


def capture_exposure_duration_s() -> float:
    """Primary-camera shutter open time [s] (pint-backed constant)."""
    return float(CAMERA_EXPOSURE_TIME.to(ureg.s).magnitude)


def resolve_capture_time_window_s(
    *,
    t_cmd_s: float,
    sim_dt_s: float,
    capture_latency_steps: int = 0,
) -> tuple[float, float]:
    """
    Time interval [t0, t1] for one take-picture exposure (for plots / telemetry).

    Uses the physical exposure; widens to at least one sim step so sub-step
    exposures remain visible on discrete timelines.
    """
    latency_s = float(capture_latency_steps) * float(sim_dt_s)
    t0 = float(t_cmd_s) + latency_s
    span = max(capture_exposure_duration_s(), float(sim_dt_s))
    return t0, t0 + span


def resolve_capture_frame_index(
    *,
    cmd_step: int,
    n_steps: int,
    capture_latency_steps: int = 0,
) -> int | None:
    """
    Frame index used for capture reward after a take-picture command.

    Discrete sim: quality is read from the closest frame at or after the command
    step (optional latency in whole sim steps).
    """
    k = int(cmd_step) + int(capture_latency_steps)
    if k < 0 or k >= int(n_steps):
        return None
    return k


__all__ = [
    "TakePictureBudget",
    "TakePictureConfig",
    "capture_exposure_duration_s",
    "resolve_capture_frame_index",
    "resolve_capture_time_window_s",
]
