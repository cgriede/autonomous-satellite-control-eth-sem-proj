"""Archive an existing MP4 before overwrite (sibling ``video_archive/`` folder)."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

_ARCHIVE_DIR_NAME = "video_archive"
_VERSION_PATTERN = re.compile(r"^(\d{3})-(.+)$")


def video_archive_dir_for(out_path: Path) -> Path:
    """``video_archive`` next to the export file's parent directory."""
    return Path(out_path).resolve().parent / _ARCHIVE_DIR_NAME


def next_archived_video_path(out_path: Path) -> Path:
    """Return ``video_archive/NNN-<basename>`` with the next free version index."""
    out_path = Path(out_path).resolve()
    archive_dir = video_archive_dir_for(out_path)
    archive_dir.mkdir(parents=True, exist_ok=True)
    base_name = out_path.name
    max_n = 0
    for entry in archive_dir.iterdir():
        if not entry.is_file():
            continue
        match = _VERSION_PATTERN.match(entry.name)
        if match is None or match.group(2) != base_name:
            continue
        max_n = max(max_n, int(match.group(1)))
    return archive_dir / f"{max_n + 1:03d}-{base_name}"


def archive_existing_video(out_path: Path) -> Path | None:
    """
    If ``out_path`` exists, move it into ``video_archive/NNN-<basename>``.

    Returns the archive path, or ``None`` when there was nothing to archive.
    """
    out_path = Path(out_path).resolve()
    if not out_path.is_file():
        return None
    archived = next_archived_video_path(out_path)
    shutil.move(str(out_path), str(archived))
    return archived
