"""Hypothesis A — export every 2nd sim-time frame (half matplotlib draws)."""

from __future__ import annotations

from pathlib import Path

from _export_fork import save_one_pass_video_fork

FRAME_STRIDE = 2


def patched_save(export_path: Path | None = None) -> Path:
    out = save_one_pass_video_fork(export_path, frame_stride=FRAME_STRIDE)
    patched_save._last_n_frames_drawn = save_one_pass_video_fork._last_n_frames_drawn
    return out


patched_save._last_n_frames_drawn = None
