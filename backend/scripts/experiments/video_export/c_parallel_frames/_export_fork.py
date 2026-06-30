"""Hypothesis C fork — delegates to production parallel export."""

from __future__ import annotations

import os
from pathlib import Path

from render.video_export_parallel import (
    resolve_export_worker_count,
    save_one_pass_video_parallel,
)


def patched_save(export_path: Path | None = None) -> Path:
    n_workers = resolve_export_worker_count()
    os.environ["VIDEO_EXPORT_WORKERS"] = str(n_workers)
    out = save_one_pass_video_parallel(export_path, n_workers=n_workers)
    patched_save._last_n_frames_drawn = getattr(
        save_one_pass_video_parallel, "_last_n_frames_drawn", None
    )
    return out
