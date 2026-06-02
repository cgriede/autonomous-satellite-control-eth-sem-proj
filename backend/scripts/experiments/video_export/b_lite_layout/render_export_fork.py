"""Hypothesis B — export without telemetry / reward / torque / secondary cam strip panels."""

from __future__ import annotations

from pathlib import Path

from render.render_main import save_one_pass_video_30x


def patched_save(export_path: Path | None = None) -> Path:
    return save_one_pass_video_30x(export_path)
