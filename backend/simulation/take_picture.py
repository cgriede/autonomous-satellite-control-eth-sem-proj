"""Take-picture command budget and discrete capture frame resolution."""

from __future__ import annotations

from dataclasses import dataclass

from environment_definition.constants.SATELLITE import MAX_PRIMARY_CAPTURES_PER_ORBIT


@dataclass(frozen=True)
class TakePictureConfig:
    """Episode-level shutter / downlink budget."""

    max_pictures_per_episode: int = MAX_PRIMARY_CAPTURES_PER_ORBIT


@dataclass
class TakePictureBudget:
    """Remaining capture slots for one episode."""

    remaining: int

    @classmethod
    def from_config(cls, config: TakePictureConfig | None = None) -> TakePictureBudget:
        cfg = config or TakePictureConfig()
        return cls(remaining=int(cfg.max_pictures_per_episode))

    def try_capture(self) -> bool:
        """Consume one slot; return False when budget is exhausted."""
        if self.remaining <= 0:
            return False
        self.remaining -= 1
        return True


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
    "resolve_capture_frame_index",
]
