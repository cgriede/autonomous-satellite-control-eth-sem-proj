"""Notebook helpers to show exported MP4s (H.264 after render pipeline) in Jupyter / VS Code."""

from __future__ import annotations

from pathlib import Path
from typing import Any

# Set in ``init_mpo_video_cell()`` when ``ipywidgets`` is available.
VIDEO_WIDGET_OUT: Any = None


def init_mpo_video_cell() -> None:
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


def display_mpo_video(path: Path | str, *, width: int = 680) -> None:
    """Show a video file in the notebook (embedded, works with H.264 exports)."""
    from IPython.display import Video, clear_output, display

    p = Path(path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"Video not found: {p}")

    if VIDEO_WIDGET_OUT is not None:
        with VIDEO_WIDGET_OUT:
            clear_output(wait=True)
            display(Video(str(p), embed=True, width=width))
    else:
        display(Video(str(p), embed=True, width=width))


def log_exported_video(path: Path | str, *, tag: str = "export") -> None:
    """Notebook-friendly line after the render pipeline wrote an MP4 (path + size)."""
    p = Path(path).resolve()
    try:
        nbytes = int(p.stat().st_size) if p.exists() else 0
    except OSError:
        nbytes = -1
    print(f"[mpo_video:{tag}] {p.name} ({nbytes} bytes)")
