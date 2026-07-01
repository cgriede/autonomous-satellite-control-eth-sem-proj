"""Archive or delete aborted ML run directories (those containing stderr.txt)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from utils.ml_training.ml_training_utils import (  # noqa: E402
    RUNS_ROOT,
    sweep_aborted_run_directories,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Move aborted runs with partial artifacts to runs/_aborted; "
            "delete config-only aborted runs."
        )
    )
    parser.add_argument(
        "--runs-root",
        type=Path,
        default=RUNS_ROOT,
        help=f"Runs root (default: {RUNS_ROOT})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report actions without moving or deleting directories.",
    )
    args = parser.parse_args()

    result = sweep_aborted_run_directories(runs_root=args.runs_root, dry_run=args.dry_run)
    if not result.actions:
        print(f"No aborted runs under {args.runs_root}")
        return

    prefix = "[dry-run] " if args.dry_run else ""
    for item in result.actions:
        print(f"{prefix}{item.action}: {item.run_dir.name} -> {item.detail}")
    print(
        f"{prefix}summary: archived={len(result.archived)} "
        f"removed={len(result.removed)}"
    )


if __name__ == "__main__":
    main()
