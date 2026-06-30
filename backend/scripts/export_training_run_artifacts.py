"""Export plots/videos for a completed run from agent.pt (no retraining)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BACKEND_DIR = Path(__file__).resolve().parents[1]
S01_DIR = BACKEND_DIR / "notebooks" / "s01"
for path in (BACKEND_DIR, S01_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from s01_utils import training_workflow as tw  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Export training run artifacts from checkpoint")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--train-videos", type=int, default=2)
    parser.add_argument("--eval-videos", type=int, default=1)
    parser.add_argument("--no-reward-plots", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    result = tw.export_artifacts_from_checkpoint(
        args.run_dir,
        train_episode_videos=int(args.train_videos),
        eval_episode_videos=int(args.eval_videos),
        export_episode_reward_plots=not args.no_reward_plots,
        show_progress=not args.quiet,
    )
    print(f"run_dir={result['run_dir']}")
    print(f"train_replayed={result['train_episodes_replayed']}")
    print(f"eval_replayed={result['eval_episodes_replayed']}")
    if result["errors"]:
        print("errors:")
        for err in result["errors"]:
            print(f"  - {err}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
