"""Forked MP4 export loop (experiment-only; production stays read-only)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from matplotlib import animation as mpl_animation
from tqdm import tqdm

from environment_definition.constants import RENDER, SIMULATION
from render import render_main as rm
from utils.video_archive import archive_existing_video


def save_one_pass_video_fork(
    export_path: Path | None = None,
    *,
    frame_stride: int = 1,
) -> Path:
    """Production export loop with optional temporal subsampling (``frame_stride`` >= 1)."""
    if frame_stride < 1:
        raise ValueError(f"frame_stride must be >= 1, got {frame_stride}")

    sim_series = rm._require_runtime()
    if rm.FIG is None:
        raise RuntimeError("Figure has not been initialized.")
    export_speed_multiplier = float(SIMULATION.export_speed_multiplier)
    export_fps = int(RENDER.export_fps)
    sim_total_s = float(sim_series.metadata.sim_total_s)
    dt_sim_s = (rm.ANIMATION_INTERVAL_MS / 1000.0) * export_speed_multiplier
    export_num_frames = max(2, int(np.ceil(sim_total_s / dt_sim_s)) + 1)
    frame_indices = list(range(0, export_num_frames, frame_stride))
    if frame_indices[-1] != export_num_frames - 1:
        frame_indices.append(export_num_frames - 1)

    if export_path is None:
        export_path = Path(__file__).resolve().parents[3] / RENDER.export_filename
    export_path = Path(export_path).resolve()
    export_path.parent.mkdir(parents=True, exist_ok=True)
    archived = archive_existing_video(export_path)
    if archived is not None:
        print(f"[video] archived previous export -> {archived}")

    def export_update(frame: int) -> list:
        sim_t = min(float(frame) * dt_sim_s, sim_total_s)
        sim_idx = rm.simulation_index_from_time(sim_t, wrap_orbit=False)
        scene = rm.sample_scene(sim_idx)
        rm.update_panels(scene)
        return []

    mpl_ffmpeg_available = bool(mpl_animation.writers.is_available("ffmpeg"))
    rm.init()

    frame_iter = tqdm(
        frame_indices,
        desc="Writing video",
        unit="frame",
    )

    if mpl_ffmpeg_available:
        writer = mpl_animation.FFMpegWriter(fps=export_fps)
        with writer.saving(rm.FIG, str(export_path), dpi=RENDER.export_dpi):
            for frame in frame_iter:
                export_update(frame)
                writer.grab_frame()
    else:
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        import cv2  # type: ignore[reportMissingImports]

        canvas = FigureCanvasAgg(rm.FIG)
        canvas.draw()
        width, height = canvas.get_width_height()
        writer = cv2.VideoWriter(
            str(export_path),
            cv2.VideoWriter_fourcc(*"mp4v"),
            export_fps,
            (width, height),
        )
        if not writer.isOpened():
            raise RuntimeError("Could not open MP4 writer (OpenCV fallback).")
        for frame in frame_iter:
            export_update(frame)
            canvas.draw()
            rgba = np.asarray(canvas.buffer_rgba())
            bgr = cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGR)
            writer.write(bgr)
        writer.release()
        rm._try_reencode_mp4_h264_for_web(export_path)

    save_one_pass_video_fork._last_n_frames_drawn = len(frame_indices)
    return export_path
