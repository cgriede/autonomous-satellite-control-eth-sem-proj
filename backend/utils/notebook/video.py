"""Notebook helpers to show exported MP4s (H.264 after render pipeline) in Jupyter / VS Code."""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any

# Set in ``init_mpo_video_cell()`` when ``ipywidgets`` is available.
VIDEO_WIDGET_OUT: Any = None

# #region agent log
def _agent_debug_log(*, location: str, message: str, data: dict[str, Any], hypothesis_id: str) -> None:
    entry = {
        "sessionId": "c8a7bc",
        "timestamp": int(time.time() * 1000),
        "location": location,
        "message": message,
        "data": data,
        "hypothesisId": hypothesis_id,
    }
    log_path = Path(__file__).resolve().parents[3] / "debug-c8a7bc.log"
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry) + "\n")


def _probe_mp4_for_debug(path: Path) -> dict[str, Any]:
    out: dict[str, Any] = {"path": str(path), "size_bytes": int(path.stat().st_size)}
    try:
        head = path.read_bytes()[:64]
        out["head_hex"] = head[:32].hex()
        if b"ftyp" in head:
            i = head.index(b"ftyp")
            out["ftyp_brand"] = head[i + 4 : i + 8].decode("ascii", errors="replace")
    except OSError as exc:
        out["head_error"] = str(exc)
    try:
        import imageio_ffmpeg

        ff = imageio_ffmpeg.get_ffmpeg_exe()
        if ff and Path(ff).exists():
            proc = subprocess.run(
                [str(ff), "-hide_banner", "-i", str(path)],
                capture_output=True,
                text=True,
                check=False,
            )
            tail = (proc.stderr or "")[-800:]
            out["ffmpeg_probe_tail"] = tail
            out["likely_h264"] = "h264" in tail.lower() or "avc1" in tail.lower()
            out["likely_mpeg4"] = "mpeg4" in tail.lower() or "mp4v" in tail.lower()
    except Exception as exc:
        out["ffmpeg_probe_error"] = str(exc)
    return out


# #endregion


def init_video_cell() -> None:
    """Create a fixed output area for videos (optional; falls back to inline display)."""
    global VIDEO_WIDGET_OUT
    from IPython.display import HTML, display

    VIDEO_WIDGET_OUT = None
    try:
        import ipywidgets as widgets  # type: ignore

        VIDEO_WIDGET_OUT = widgets.Output(layout={"border": "1px solid #444", "max_width": "720px"})
        display(HTML("<b>Rendered videos</b>"))
        display(VIDEO_WIDGET_OUT)
    except Exception:
        display(HTML("<p><b>Rendered videos</b> (below)</p>"))


def play_saved_video(path: Path | str, *, width: int = 680) -> None:
    """Play an MP4 already on disk without embedding it into the notebook JSON."""
    from IPython.display import Video, clear_output, display

    p = Path(path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"Video not found: {p}")

    log_exported_video(p, tag="play")
    video = Video(str(p), embed=False, width=width)
    if VIDEO_WIDGET_OUT is not None:
        with VIDEO_WIDGET_OUT:
            clear_output(wait=True)
            display(video)
    else:
        display(video)


def display_video(path: Path | str, *, width: int = 680) -> None:
    """Play a video file already saved on disk (alias for :func:`play_saved_video`)."""
    play_saved_video(path, width=width)


def log_exported_video(path: Path | str, *, tag: str = "export") -> None:
    """Notebook-friendly line after the render pipeline wrote an MP4 (path + size)."""
    p = Path(path).resolve()
    try:
        nbytes = int(p.stat().st_size) if p.exists() else 0
    except OSError:
        nbytes = -1
    print(f"[mpo_video:{tag}] {p.name} ({nbytes} bytes)")

def _export_render_video(*, simulation_series, out_path: Path) -> Path:
    """Export a render video from a simulation series to a path. For use in notebooks."""
    from environment_definition.constants import RenderMode
    from render.render_main import render_from_series

    out_path.parent.mkdir(parents=True, exist_ok=True)
    result = render_from_series(
        simulation_series=simulation_series,
        render_mode=RenderMode.EXPORT,
        output_path=out_path,
    )
    if result is None:
        raise RuntimeError("Render export did not return output path.")
    if not out_path.exists() or out_path.stat().st_size <= 0:
        raise RuntimeError(f"Render export missing/empty video: {out_path}")
    # #region agent log
    _agent_debug_log(
        location="video.py:_export_render_video",
        message="after_render_from_series",
        data=_probe_mp4_for_debug(out_path),
        hypothesis_id="H1,H2,H5",
    )
    # #endregion
    log_exported_video(out_path, tag="after_export")
    return out_path