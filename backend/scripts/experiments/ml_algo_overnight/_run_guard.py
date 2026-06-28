"""Single active ml_algo_overnight job on this host."""

from __future__ import annotations

import atexit
import os
import sys
from pathlib import Path

_LOCK_PATH = Path(__file__).resolve().parent / ".experiment_run.lock"


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


def acquire_experiment_run_lock(*, script: str) -> None:
    if _LOCK_PATH.is_file():
        try:
            text = _LOCK_PATH.read_text(encoding="utf-8").strip().splitlines()
            old_pid = int(text[0]) if text else -1
            old_script = text[1] if len(text) > 1 else "?"
        except (OSError, ValueError):
            old_pid, old_script = -1, "?"
        if old_pid == os.getpid():
            return
        if _pid_alive(old_pid):
            print(
                f"[ml_algo_overnight] Another experiment is running "
                f"(pid={old_pid}, script={old_script}).",
                file=sys.stderr,
            )
            raise SystemExit(2)
        _LOCK_PATH.unlink(missing_ok=True)

    _LOCK_PATH.write_text(f"{os.getpid()}\n{script}\n", encoding="utf-8")

    def _release() -> None:
        try:
            if _LOCK_PATH.is_file():
                owner = int(_LOCK_PATH.read_text(encoding="utf-8").splitlines()[0])
                if owner == os.getpid():
                    _LOCK_PATH.unlink(missing_ok=True)
        except (OSError, ValueError, IndexError):
            pass

    atexit.register(_release)
