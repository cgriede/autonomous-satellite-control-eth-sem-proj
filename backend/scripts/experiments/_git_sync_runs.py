"""Commit and push new artifacts under backend/autonomous_control/runs/."""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
RUNS_DIR = REPO_ROOT / "backend" / "autonomous_control" / "runs"


def _run(cmd: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, check=False, capture_output=True, text=True)


def sync_runs_git(
    *,
    message: str,
    push: bool = True,
    dry_run: bool = False,
) -> dict[str, str | bool]:
    """Stage runs/, commit if dirty, optionally push."""
    if not RUNS_DIR.is_dir():
        return {"status": "skipped", "reason": f"runs dir missing: {RUNS_DIR}"}

    status = _run(["git", "status", "--porcelain", "--", str(RUNS_DIR.relative_to(REPO_ROOT))], cwd=REPO_ROOT)
    if status.returncode != 0:
        return {"status": "error", "reason": status.stderr.strip() or "git status failed"}

    if not status.stdout.strip():
        return {"status": "clean", "reason": "no changes under runs/"}

    if dry_run:
        return {"status": "dry_run", "reason": status.stdout.strip()[:500]}

    add = _run(["git", "add", "--", str(RUNS_DIR.relative_to(REPO_ROOT))], cwd=REPO_ROOT)
    if add.returncode != 0:
        return {"status": "error", "reason": add.stderr.strip() or "git add failed"}

    commit = _run(["git", "commit", "-m", message], cwd=REPO_ROOT)
    if commit.returncode != 0:
        return {"status": "error", "reason": commit.stderr.strip() or "git commit failed"}

    result: dict[str, str | bool] = {"status": "committed", "message": message}
    if push:
        push_res = _run(["git", "push"], cwd=REPO_ROOT)
        if push_res.returncode != 0:
            result["status"] = "committed_push_failed"
            result["push_error"] = push_res.stderr.strip() or push_res.stdout.strip()
        else:
            result["status"] = "pushed"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Git commit/push backend/autonomous_control/runs/")
    parser.add_argument("--message", "-m", required=True)
    parser.add_argument("--no-push", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    out = sync_runs_git(message=args.message, push=not args.no_push, dry_run=args.dry_run)
    print(out)
    if out.get("status") == "error":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
