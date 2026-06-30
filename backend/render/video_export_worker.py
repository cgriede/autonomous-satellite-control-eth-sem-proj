"""Process-pool worker: draw a shard of export frames to temp RGBA files."""

from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np


def render_shard_to_dir(
    *,
    series_pickle: bytes,
    shard_indices: list[int],
    tmpdir: str,
    dt_sim_s: float,
    sim_total_s: float,
    export_dpi: int,
    fig_width_in: float,
    fig_height_in: float,
) -> tuple[int, int, int]:
    """Return (frames_written, width, height)."""
    from matplotlib.backends.backend_agg import FigureCanvasAgg

    from environment_definition.constants import RenderMode
    from render import render_main as rm

    series = pickle.loads(series_pickle)
    rm.render_from_series(
        simulation_series=series,
        render_mode=RenderMode.HEADLESS,
        output_path=None,
    )
    rm._build_panels()
    rm.init()

    if rm.FIG is None:
        raise RuntimeError("Figure not initialized in worker")

    rm.FIG.set_size_inches(float(fig_width_in), float(fig_height_in))
    rm.FIG.set_dpi(int(export_dpi))
    canvas = FigureCanvasAgg(rm.FIG)
    canvas.draw()
    width, height = canvas.get_width_height()

    out_dir = Path(tmpdir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for export_frame in shard_indices:
        sim_t = min(float(export_frame) * float(dt_sim_s), float(sim_total_s))
        sim_idx = rm.simulation_index_from_time(sim_t, wrap_orbit=False)
        scene = rm.sample_scene(sim_idx)
        rm.update_panels(scene)
        canvas.draw()
        rgba = np.asarray(canvas.buffer_rgba(), dtype=np.uint8)
        path = out_dir / f"frame_{int(export_frame):06d}.rgba"
        rgba.tofile(path)

    if rm.FIG is not None:
        import matplotlib.pyplot as plt

        plt.close(rm.FIG)
        rm.FIG = None

    return len(shard_indices), int(width), int(height)
