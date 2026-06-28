"""Extend S01 warmup bundle fingerprint with dt + reward_mode (experiment-only)."""

from __future__ import annotations

from typing import Any

_PATCHED = False
_ORIGINAL: Any = None
_EXTRA: dict[str, Any] = {"reward_mode": "sparse"}


def set_warmup_fingerprint_extra(**kwargs: Any) -> None:
    _EXTRA.update(kwargs)


def activate_warmup_fingerprint_patch() -> None:
    global _PATCHED, _ORIGINAL
    if _PATCHED:
        return
    import s01_utils.training_workflow as tw

    _ORIGINAL = tw.s01_training_warmup_fingerprint

    def _wrapped(setup: Any, *, episode_count: int) -> dict[str, Any]:
        fp = _ORIGINAL(setup, episode_count=episode_count)
        fp.update({k: v for k, v in _EXTRA.items() if v is not None})
        return fp

    tw.s01_training_warmup_fingerprint = _wrapped  # type: ignore[method-assign]
    _PATCHED = True


def deactivate_warmup_fingerprint_patch() -> None:
    global _PATCHED, _ORIGINAL
    if not _PATCHED or _ORIGINAL is None:
        return
    import s01_utils.training_workflow as tw

    tw.s01_training_warmup_fingerprint = _ORIGINAL
    _PATCHED = False
    _ORIGINAL = None
