"""Hypothesis D — explicit 720p export (1280x720)."""

from __future__ import annotations

from pathlib import Path

from render.render_main import save_one_pass_video_30x


def patched_save(export_path: Path | None = None) -> Path:
    """Production path now uses RENDER.export_pixel_width/height; thin alias for bench."""
    return save_one_pass_video_30x(export_path=export_path)
