"""Gate: frozen fixture + eval_best video export (smoke or visual preview)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[3]
EXPERIMENT_ROOT = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(EXPERIMENT_ROOT) not in sys.path:
    sys.path.insert(0, str(EXPERIMENT_ROOT))

from _runner_common import load_frozen_series, probe_video
from utils.ml_training.training_artifact_worker import BackgroundArtifactWorker
from utils.ml_training.training_run_artifacts import artifact_paths_map, ensure_run_layout

_FIXTURE_HELP = (
    "gate: 5-step smoke test (~0.2 s, not for visual QA). "
    "training_sparse: full S01 episode (~43 s, matches training-run exports)."
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export eval_best.mp4 from a frozen series fixture.")
    parser.add_argument(
        "--fixture",
        default="gate",
        choices=("gate", "training_sparse"),
        help=_FIXTURE_HELP,
    )
    args = parser.parse_args()

    series = load_frozen_series(args.fixture)
    run_dir = EXPERIMENT_ROOT / "results" / f"{args.fixture}_training_episode_video"
    ensure_run_layout(run_dir)
    paths = artifact_paths_map(run_dir)
    worker = BackgroundArtifactWorker(run_dir)
    worker.submit_video_export(series, paths["eval_best_video"])
    errors = worker.shutdown(wait=True)
    if errors:
        raise RuntimeError("\n".join(errors))
    video = paths["eval_best_video"]
    if not video.exists():
        raise RuntimeError(f"video missing: {video}")
    info = probe_video(video)
    print(
        f"OK fixture={args.fixture} n_steps={series.t_s.shape[0]} "
        f"video={video} bytes={video.stat().st_size} "
        f"duration_s={info.get('duration_s')} "
        f"resolution={info.get('width')}x{info.get('height')}"
    )
    if args.fixture == "gate":
        print(
            "NOTE: gate is a fast smoke test only (~4 frames). "
            "For visual QA matching training runs: "
            "python backend/scripts/experiments/video_export/run_training_episode_video_gate.py --fixture training_sparse"
        )


if __name__ == "__main__":
    main()
