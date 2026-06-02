"""Notebook helpers to show exported MP4s (H.264 after render pipeline) in Jupyter / VS Code.

Episode verification policy: run canonical ``SimulationStateSeries`` export (``RenderMode.EXPORT``)
then display the MP4 with :func:`play_saved_video` / :func:`export_and_play_saved_video`.
Do not open ``RenderMode.INTERACTIVE`` (matplotlib Sat Sim player) from notebooks — export
subsamples frames for speed and the HTML ``<video>`` player is the review surface.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

# Set in ``init_mpo_video_cell()`` when ``ipywidgets`` is available.
VIDEO_WIDGET_OUT: Any = None


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


def _video_codec_name(path: Path) -> str | None:
    """Return ffmpeg-reported codec short name (e.g. ``h264``, ``mpeg4``) or ``None``."""
    try:
        from render.render_main import _resolve_ffmpeg_executable
    except ImportError:
        return None
    import subprocess

    ffmpeg_exe, _ = _resolve_ffmpeg_executable()
    if ffmpeg_exe is None:
        return None
    proc = subprocess.run(
        [ffmpeg_exe, "-hide_banner", "-i", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    for line in proc.stderr.splitlines():
        if "Video:" in line:
            # e.g. "Video: h264 (High) ..." or "Video: mpeg4 (Simple Profile) ..."
            token = line.split("Video:", 1)[1].strip().split(",", 1)[0].strip()
            return token.split("(", 1)[0].strip().split()[0]
    return None


def ensure_notebook_playable_mp4(path: Path | str) -> tuple[bool, str]:
    """Ensure MP4 is H.264 yuv420p for HTML5 notebook players; re-encode when needed."""
    from render.render_main import _try_reencode_mp4_h264_for_web

    p = Path(path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"Video not found: {p}")

    codec = _video_codec_name(p)
    if codec == "h264":
        return True, "already_h264"
    ok, detail = _try_reencode_mp4_h264_for_web(p)
    if ok:
        return True, detail
    if codec is None:
        return False, f"codec_unknown_reencode_failed:{detail}"
    return False, f"codec_{codec}_reencode_failed:{detail}"


def play_saved_video(path: Path | str, *, width: int = 680) -> None:
    """Play an MP4 on disk using a ``file://`` URI (reliable on Windows notebooks)."""
    from IPython.display import HTML, clear_output, display

    p = Path(path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"Video not found: {p}")

    playable_ok, playable_detail = ensure_notebook_playable_mp4(p)
    log_exported_video(p, tag="play")
    if not playable_ok:
        print(
            f"[mpo_video:play] warning: not browser-H.264 ({playable_detail}); "
            "player may be blank. Install imageio-ffmpeg in ASC and re-export."
        )

    video_html = (
        f'<video controls width="{width}" style="max-width:100%;" '
        f'src="{p.as_uri()}">'
        "Your browser does not support the video element."
        "</video>"
    )
    if VIDEO_WIDGET_OUT is not None:
        with VIDEO_WIDGET_OUT:
            clear_output(wait=True)
            display(HTML(video_html))
    else:
        display(HTML(video_html))


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
    codec = _video_codec_name(p) if p.exists() else None
    codec_note = f", codec={codec}" if codec else ""
    print(f"[mpo_video:{tag}] {p.name} ({nbytes} bytes{codec_note})")


def _export_render_video(*, simulation_series, out_path: Path) -> Path:
    """Export a render video from a simulation series to a path. For use in notebooks."""
    from environment_definition.constants import RenderMode
    from render.render_main import render_from_series

    out_path = Path(out_path).resolve()
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
    playable_ok, playable_detail = ensure_notebook_playable_mp4(out_path)
    if not playable_ok:
        print(f"[mpo_video:export] warning: H.264 re-encode failed ({playable_detail})")
    log_exported_video(out_path, tag="after_export")
    return out_path


def export_and_play_saved_video(
    *,
    simulation_series,
    out_path: Path | str,
    width: int = 680,
) -> Path:
    """Export an episode MP4 and display it in the notebook HTML video player."""
    path = _export_render_video(simulation_series=simulation_series, out_path=Path(out_path))
    play_saved_video(path, width=width)
    return path
