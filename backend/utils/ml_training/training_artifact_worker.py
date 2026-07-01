"""Background thread for matplotlib plots and video export off the training hot path."""

from __future__ import annotations

import queue
import threading
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from utils.ml_training.training_run_artifacts import (
    export_run_plots,
    export_training_episode_video_sync,
    plot_episode_reward_timeline,
)


@dataclass(frozen=True)
class _RewardPlotJob:
    series: Any
    label: str
    out_path: Path


@dataclass(frozen=True)
class _VideoExportJob:
    series: Any
    out_path: Path


@dataclass(frozen=True)
class _RunPlotsJob:
    run_dir: Path
    episode_rows: list[dict[str, Any]]
    warmup_results: list[Any] | None = None
    train_results: list[Any] | None = None
    eval_results: list[Any] | None = None


class BackgroundArtifactWorker:
    def __init__(self, run_dir: Path) -> None:
        self._run_dir = Path(run_dir)
        self._queue: queue.Queue[Any] = queue.Queue()
        self._errors: list[str] = []
        self._lock = threading.Lock()
        self._stop_sentinel = object()
        self._thread = threading.Thread(
            target=self._worker_loop,
            name="training-artifact-worker",
            daemon=True,
        )
        self._thread.start()

    def submit_reward_plot(self, series: Any, *, label: str, out_path: Path) -> None:
        self._queue.put(_RewardPlotJob(series=series, label=label, out_path=Path(out_path)))

    def submit_video_export(self, series: Any, out_path: Path) -> None:
        self._queue.put(_VideoExportJob(series=series, out_path=Path(out_path)))

    def submit_run_plots(
        self,
        episode_rows: list[dict[str, Any]],
        *,
        warmup_results: list[Any] | None = None,
        train_results: list[Any] | None = None,
        eval_results: list[Any] | None = None,
    ) -> None:
        self._queue.put(
            _RunPlotsJob(
                run_dir=self._run_dir,
                episode_rows=list(episode_rows),
                warmup_results=list(warmup_results) if warmup_results is not None else None,
                train_results=list(train_results) if train_results is not None else None,
                eval_results=list(eval_results) if eval_results is not None else None,
            )
        )

    def drain(self, timeout: float | None = None) -> list[str]:
        """Block until queue is empty; return error messages."""
        _ = timeout
        self._queue.join()
        with self._lock:
            return list(self._errors)

    def shutdown(self, *, wait: bool = True) -> list[str]:
        if wait:
            self._queue.join()
        self._queue.put(self._stop_sentinel)
        if wait:
            self._thread.join()
        with self._lock:
            return list(self._errors)

    def _record_error(self, message: str) -> None:
        with self._lock:
            self._errors.append(message)

    def _run_job(self, job: Any) -> None:
        if isinstance(job, _RewardPlotJob):
            plot_episode_reward_timeline(job.series, label=job.label, out_path=job.out_path)
            return
        if isinstance(job, _VideoExportJob):
            export_training_episode_video_sync(job.series, job.out_path)
            return
        if isinstance(job, _RunPlotsJob):
            export_run_plots(
                job.run_dir,
                job.episode_rows,
                warmup_results=job.warmup_results,
                train_results=job.train_results,
                eval_results=job.eval_results,
            )
            return
        raise TypeError(f"Unknown artifact job: {type(job)!r}")

    def _worker_loop(self) -> None:
        import matplotlib

        try:
            matplotlib.use("Agg")
        except Exception:
            pass
        while True:
            job = self._queue.get()
            try:
                if job is self._stop_sentinel:
                    return
                self._run_job(job)
            except Exception as exc:
                self._record_error(f"{type(job).__name__}: {exc}\n{traceback.format_exc()}")
            finally:
                self._queue.task_done()


def run_artifacts_sync(
    *,
    reward_jobs: list[tuple[Any, str, Path]] | None = None,
    video_jobs: list[tuple[Any, Path]] | None = None,
    run_dir: Path | None = None,
    episode_rows: list[dict[str, Any]] | None = None,
    warmup_results: list[Any] | None = None,
    train_results: list[Any] | None = None,
    eval_results: list[Any] | None = None,
    skip_run_plots: bool = False,
    on_error: Callable[[str], None] | None = None,
) -> list[str]:
    """Synchronous fallback when background_artifacts=False."""
    errors: list[str] = []
    for series, label, out_path in reward_jobs or []:
        try:
            plot_episode_reward_timeline(series, label=label, out_path=out_path)
        except Exception as exc:
            msg = f"reward_plot({label}): {exc}"
            errors.append(msg)
            if on_error:
                on_error(msg)
    for series, out_path in video_jobs or []:
        try:
            export_training_episode_video_sync(series, out_path)
        except Exception as exc:
            msg = f"video_export({out_path.name}): {exc}"
            errors.append(msg)
            if on_error:
                on_error(msg)
    if run_dir is not None and episode_rows is not None and not skip_run_plots:
        try:
            export_run_plots(
                run_dir,
                episode_rows,
                warmup_results=warmup_results,
                train_results=train_results,
                eval_results=eval_results,
            )
        except Exception as exc:
            msg = f"run_plots: {exc}"
            errors.append(msg)
            if on_error:
                on_error(msg)
    return errors
