"""Deprecated — vector/torque routing is production ``EpisodeRunner`` + ``TrainingWorkflowConfig``."""

from _obc_attitude_request_fork import ObcAttitudeRequestContext  # noqa: F401 — re-export


def activate_episode_runner_fork(obc_ctx: ObcAttitudeRequestContext | None = None) -> None:
    _ = obc_ctx


def deactivate_episode_runner_fork() -> None:
    pass


def active_obc_context() -> None:
    return None


__all__ = [
    "ObcAttitudeRequestContext",
    "activate_episode_runner_fork",
    "active_obc_context",
    "deactivate_episode_runner_fork",
]
