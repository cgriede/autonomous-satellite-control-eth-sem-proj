"""Global mutex: at most one ML pipeline training run on this host.

Lock file: backend/scripts/experiments/.pipeline_run.lock
Mirror:   docs/experiments/pipeline/.active_run.json (for agents / STATUS)
"""

from __future__ import annotations

import atexit
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_EXPERIMENTS_ROOT = Path(__file__).resolve().parent
_LOCK_PATH = _EXPERIMENTS_ROOT / ".pipeline_run.lock"
_REPO_ROOT = _EXPERIMENTS_ROOT.parents[2]  # experiments → scripts → backend → repo root
_ACTIVE_JSON = _REPO_ROOT / "docs" / "experiments" / "pipeline" / ".active_run.json"


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if sys.platform == "win32":
        try:
            import ctypes

            handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
            if not handle:
                return False
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def read_active_run() -> dict[str, Any] | None:
    """Return active run metadata, or None if no live holder."""
    if not _LOCK_PATH.is_file():
        return None
    try:
        lines = _LOCK_PATH.read_text(encoding="utf-8").strip().splitlines()
        pid = int(lines[0]) if lines else -1
        slug = lines[1] if len(lines) > 1 else "?"
        script = lines[2] if len(lines) > 2 else "?"
        started = lines[3] if len(lines) > 3 else ""
    except (OSError, ValueError, IndexError):
        return None
    if pid != os.getpid() and not _pid_alive(pid):
        _clear_lock_files()
        return None
    return {
        "pid": pid,
        "slug": slug,
        "script": script,
        "started_utc": started,
        "lock_path": str(_LOCK_PATH),
    }


def check_pipeline_run_clear(*, slug: str | None = None) -> None:
    """Fail fast if another pipeline run is active (optional: same slug re-entrant)."""
    active = read_active_run()
    if active is None:
        return
    if active["pid"] == os.getpid():
        return
    if slug is not None and active.get("slug") == slug:
        raise RuntimeError(
            f"Pipeline run already active for slug={slug!r} (pid={active['pid']}). "
            "Wait for completion or clear stale lock if process is dead."
        )
    raise RuntimeError(
        f"Another ML pipeline run is active: slug={active.get('slug')!r} "
        f"pid={active['pid']} script={active.get('script')!r}. "
        "Only one compute-heavy experiment at a time."
    )


def acquire_pipeline_run_lock(*, slug: str, script: str) -> None:
    """Acquire global pipeline lock; raises SystemExit(2) if blocked."""
    if _LOCK_PATH.is_file():
        try:
            lines = _LOCK_PATH.read_text(encoding="utf-8").strip().splitlines()
            old_pid = int(lines[0]) if lines else -1
            old_slug = lines[1] if len(lines) > 1 else "?"
            old_script = lines[2] if len(lines) > 2 else "?"
        except (OSError, ValueError):
            old_pid, old_slug, old_script = -1, "?", "?"
        if old_pid == os.getpid():
            return
        if _pid_alive(old_pid):
            print(
                f"[pipeline] Another ML experiment is running "
                f"(slug={old_slug}, pid={old_pid}, script={old_script}). "
                "Only one pipeline run at a time.",
                file=sys.stderr,
            )
            raise SystemExit(2)
        _clear_lock_files()

    started = datetime.now(timezone.utc).isoformat()
    _LOCK_PATH.write_text(f"{os.getpid()}\n{slug}\n{script}\n{started}\n", encoding="utf-8")
    payload = {
        "pid": os.getpid(),
        "slug": slug,
        "script": script,
        "started_utc": started,
    }
    _ACTIVE_JSON.parent.mkdir(parents=True, exist_ok=True)
    _ACTIVE_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    atexit.register(_release_if_owner)


def _clear_lock_files() -> None:
    _LOCK_PATH.unlink(missing_ok=True)
    _ACTIVE_JSON.unlink(missing_ok=True)


def _release_if_owner() -> None:
    try:
        if not _LOCK_PATH.is_file():
            return
        owner = int(_LOCK_PATH.read_text(encoding="utf-8").splitlines()[0])
        if owner == os.getpid():
            _clear_lock_files()
    except (OSError, ValueError, IndexError):
        pass


__all__ = [
    "acquire_pipeline_run_lock",
    "check_pipeline_run_clear",
    "read_active_run",
]
