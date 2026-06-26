"""Gate: simulation series + background-thread eval_best video export."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[3]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from tests.test_training_run_artifacts import _minimal_series
from utils.ml_training.training_artifact_worker import BackgroundArtifactWorker
from utils.ml_training.training_run_artifacts import artifact_paths_map, ensure_run_layout


def main() -> None:
    series = _minimal_series()
    run_dir = Path(__file__).resolve().parent / "results" / "gate_training_episode_video"
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
    print(f"OK n_steps={series.t_s.shape[0]} video={video} bytes={video.stat().st_size}")


if __name__ == "__main__":
    main()
