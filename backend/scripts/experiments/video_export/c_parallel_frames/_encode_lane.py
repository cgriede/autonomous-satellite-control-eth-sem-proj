"""Encode ordered RGBA frame files to H.264 via ffmpeg (NVENC when available)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

BACKEND_DIR = Path(__file__).resolve().parents[4]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def encode_rgba_dir_to_mp4(
    *,
    frame_dir: Path,
    frame_indices: list[int],
    out_path: Path,
    width: int,
    height: int,
    fps: int,
) -> None:
    from render.render_main import (
        _FfmpegRawVideoPipeWriter,
        _resolve_ffmpeg_executable,
        _resolve_h264_export_codec,
    )

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
    except RuntimeError as exc:
        if codec != "h264_nvenc":
            raise
        _run("libx264", ["-pix_fmt", "yuv420p", "-preset", "veryfast"])
