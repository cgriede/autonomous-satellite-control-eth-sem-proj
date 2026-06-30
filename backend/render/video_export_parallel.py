"""Parallel CPU frame draw shards + ordered ffmpeg H.264 encode."""

from __future__ import annotations

import os
import pickle
import shutil
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np

from environment_definition.constants import RENDER, SIMULATION
from render.render_main import (
    ANIMATION_INTERVAL_MS,
    _FfmpegRawVideoPipeWriter,
    _resolve_ffmpeg_executable,
    _resolve_h264_export_codec,
)
from render.video_export_worker import render_shard_to_dir
from utils.video_archive import archive_existing_video


def _split_shards(indices: list[int], n_workers: int) -> list[list[int]]:
    n_workers = max(1, min(int(n_workers), len(indices)))
    shards: list[list[int]] = [[] for _ in range(n_workers)]
    for i, idx in enumerate(indices):
        shards[i % n_workers].append(int(idx))
    return [s for s in shards if s]


def _encode_rgba_dir_to_mp4(
    *,
    frame_dir: Path,
    frame_indices: list[int],
    out_path: Path,
    width: int,
    height: int,
    fps: int,
) -> None:
    ffmpeg_exe, _ = _resolve_ffmpeg_executable()
    if ffmpeg_exe is None:
        raise SystemError("ffmpeg not available for parallel encode lane")

    out_path = Path(out_path).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    codec, extra_args, _ = _resolve_h264_export_codec(ffmpeg_exe)

    def _run(active_codec: str, active_extra: list[str]) -> None:
        with _FfmpegRawVideoPipeWriter(
            out_path,
            width=width,
            height=height,
            fps=int(fps),
            ffmpeg_exe=ffmpeg_exe,
            codec=active_codec,
            extra_args=active_extra,
        ) as pipe:
            for idx in frame_indices:
                rgba_path = frame_dir / f"frame_{int(idx):06d}.rgba"
                if not rgba_path.is_file():
                    raise FileNotFoundError(f"Missing frame file: {rgba_path}")
                rgba = np.fromfile(rgba_path, dtype=np.uint8)
                expected = int(width) * int(height) * 4
                if rgba.size != expected:
                    raise ValueError(
                        f"Frame {idx} size mismatch: got {rgba.size}, expected {expected}"
                    )
                pipe.write_rgba_frame(rgba.reshape((height, width, 4)))

    try:
        _run(codec, extra_args)
    except RuntimeError:
        if codec != "h264_nvenc":
            raise
        _run("libx264", ["-pix_fmt", "yuv420p", "-preset", "veryfast"])


def compute_export_frame_indices(sim_total_s: float) -> list[int]:
    export_speed_multiplier = float(SIMULATION.export_speed_multiplier)
    export_frame_stride = max(1, int(RENDER.export_frame_stride))
    dt_sim_s = (ANIMATION_INTERVAL_MS / 1000.0) * export_speed_multiplier
    export_num_frames = max(2, int(np.ceil(sim_total_s / dt_sim_s)) + 1)
    frame_indices = list(range(0, export_num_frames, export_frame_stride))
    if frame_indices[-1] != export_num_frames - 1:
        frame_indices.append(export_num_frames - 1)
    return frame_indices


def resolve_export_worker_count() -> int:
    """Worker count for parallel export (env override, else ``RENDER.export_workers``)."""
    default = int(getattr(RENDER, "export_workers", 8))
    n_workers = int(os.environ.get("VIDEO_EXPORT_WORKERS", default))
    return max(1, n_workers)


def save_one_pass_video_parallel(
    export_path: Path | None = None,
    *,
    n_workers: int | None = None,
) -> Path:
    from render import render_main as rm

    if n_workers is None:
        n_workers = resolve_export_worker_count()

    ffmpeg_exe, ffmpeg_via = _resolve_ffmpeg_executable()
    if ffmpeg_exe is None:
        raise SystemError(
            "ffmpeg is not available; cannot export video. "
            "Install ffmpeg or the Python package 'imageio-ffmpeg'."
        )

    sim_series = rm._require_runtime()
    if rm.FIG is None:
        raise RuntimeError("Figure has not been initialized.")

    export_fps = int(RENDER.export_fps)
    export_dpi = int(RENDER.export_dpi)
    fig_w_in, fig_h_in, export_pixel_width, export_pixel_height = rm.export_canvas_geometry()
    sim_total_s = float(sim_series.metadata.sim_total_s)
    dt_sim_s = (ANIMATION_INTERVAL_MS / 1000.0) * float(SIMULATION.export_speed_multiplier)
    frame_indices = compute_export_frame_indices(sim_total_s)

    if export_path is None:
        export_path = Path(__file__).resolve().parents[1] / RENDER.export_filename
    export_path = Path(export_path).resolve()
    export_path.parent.mkdir(parents=True, exist_ok=True)
    archived = archive_existing_video(export_path)
    if archived is not None:
        print(f"[video] archived previous export -> {archived}")

    _, _, codec_label = _resolve_h264_export_codec(ffmpeg_exe)
    shards = _split_shards(frame_indices, n_workers)
    print(
        f"[video] parallel export workers={len(shards)} "
        f"frames={len(frame_indices)} encoder={codec_label} via={ffmpeg_via} fps={export_fps}"
    )

    series_pickle = pickle.dumps(sim_series, protocol=pickle.HIGHEST_PROTOCOL)
    tmp_root = Path(tempfile.mkdtemp(prefix="video_export_parallel_"))
    width = height = 0
    try:
        with ProcessPoolExecutor(max_workers=len(shards)) as pool:
            futures = []
            for shard_i, shard in enumerate(shards):
                shard_dir = tmp_root / f"shard_{shard_i:03d}"
                futures.append(
                    pool.submit(
                        render_shard_to_dir,
                        series_pickle=series_pickle,
                        shard_indices=shard,
                        tmpdir=str(shard_dir),
                        dt_sim_s=float(dt_sim_s),
                        sim_total_s=float(sim_total_s),
                        export_dpi=export_dpi,
                        fig_width_in=fig_w_in,
                        fig_height_in=fig_h_in,
                    )
                )
            for fut in as_completed(futures):
                _, w, h = fut.result()
                if w > 0:
                    width, height = w, h

        merged_dir = tmp_root / "merged"
        merged_dir.mkdir(parents=True, exist_ok=True)
        for shard_i in range(len(shards)):
            shard_dir = tmp_root / f"shard_{shard_i:03d}"
            for rgba_file in shard_dir.glob("frame_*.rgba"):
                shutil.copy2(rgba_file, merged_dir / rgba_file.name)

        _encode_rgba_dir_to_mp4(
            frame_dir=merged_dir,
            frame_indices=frame_indices,
            out_path=export_path,
            width=width,
            height=height,
            fps=export_fps,
        )
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)

    return export_path
