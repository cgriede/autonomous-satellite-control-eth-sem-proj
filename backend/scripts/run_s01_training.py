"""CLI entry for S01 notebook-08 MPO training (cluster or local)."""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
S01_DIR = BACKEND_DIR / "notebooks" / "s01"
for path in (BACKEND_DIR, S01_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import s01_utils.training_workflow as tw


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="S01 MPO training workflow (notebook 08).")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--warmup-episodes", type=int, default=10)
    parser.add_argument("--train-episodes", type=int, default=20)
    parser.add_argument("--eval-episodes", type=int, default=2)
    parser.add_argument("--run-id", type=str, default=None)
    parser.add_argument(
        "--preflight",
        action="store_true",
        help="Run fast inline preflight gate before training.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.preflight:
        tw.run_s01_training_preflight_gate()
    cfg = replace(
        tw.TrainingWorkflowConfig(),
        seed=args.seed,
        warmup_episodes=args.warmup_episodes,
        train_episodes=args.train_episodes,
        eval_episodes=args.eval_episodes,
        run_id=args.run_id,
    )
    setup = tw.build_training_workflow_setup(cfg)
    result = tw.run_training_workflow(setup, show_progress=True)
    tw.print_training_kpis(result)
    errors = result.wait_for_artifacts()
    if errors:
        print("Artifact warnings:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
