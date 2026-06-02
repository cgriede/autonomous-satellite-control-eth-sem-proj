# Render Module API Interface

This document describes the current render API in `backend/render/render_main.py`.

## Overview

- **Module role:** consume a precomputed `SimulationStateSeries` and render/export visualization panels.
- **Boundary:** render code is view-only; it does not implement physics propagation itself.
- **Execution context:** run with `backend/` as import root.
- **Ownership contract:** simulation computes dynamics, camera/cloud outputs, and reward signals; renderer only visualizes simulation outputs.

## Fidelity Contract

- Render outputs must reflect the real simulation controller selected for the run.
- No hidden controller substitution is allowed in render paths.
- Current render simulation supports `baseline` and `random` controller modes only.
- Renderer must never generate substitute simulation state for train/eval semantics.

## Runtime Dependencies

- `numpy`, `matplotlib` (`FuncAnimation`), optional `cv2` fallback when ffmpeg is unavailable.
- Simulation source: `simulation.run_simulation.run_simulation()`.
- Episode-level expected artifact contract: `SimulationStateSeries`.

## Key Runtime Functions

### `run_simulation(...)` (called from render module)

- Produces `SimulationStateSeries` consumed by all render panels.
- Receives `SimulationConfig` with `render_mode` and `controller_mode`.

### `_reconfigure_runtime(simulation_config)`

- Rebuilds `SIMULATION_SERIES` and derived globals (`N_CLOUDS`, `N_BINS`, `STATIC_SCENE`).

### `init()`

- Resets panel artists and playback time.
- Returns an empty list for `FuncAnimation` compatibility.

### `update(_frame)`

- Advances playback time (unless paused) and refreshes all panels from current series index.

### `save_one_pass_video_30x(export_path=None)`

- Exports one pass through the precomputed series.
- Uses ffmpeg writer when available, otherwise OpenCV fallback.

## CLI Interface

`render_main.py` entrypoint arguments:

- `--render-mode {headless,interactive,export}` (default `interactive`)
- `--controller-mode {baseline,random}` (default from `SimulationConfig`)
- `--save-one-pass-30x` (forces export mode)
- `--output-path <path>` (optional export path)

Examples:

```bash
python backend/render/render_main.py --render-mode interactive --controller-mode random
python backend/render/render_main.py --render-mode export --controller-mode baseline --save-one-pass-30x
```

## Panels

### Closeup (“Target Zoom”)

- **Module:** `backend/render/_closeup_view.py`
- **Data:** same world-km frame as the main orbit panel; consumes `ground_center`, `ground_left`, `ground_right`, primary/secondary cone edges, and cloud arcs from the per-frame scene dict built in `render_main.py`.
- **Ground footprint:** polyline through left — center — right ground patch corners (`camera_ground_*_xy_km` from `SimulationStateSeries`). The center vertex is the primary boresight ground intersection; it is not drawn as a separate marker.
- **Dynamic follow:** when `ground_center` is finite, axis limits are recomputed each frame with `_closeup_world_window_km(..., focus_xy_km=ground_center)` so the zoom window tracks the moving footprint. When ground intersection is unavailable, limits fall back to framing the static mission target arc.
- **Telemetry:** ground-patch coordinates remain in the info panel (`ground_patch_hit_text`); only the redundant yellow center dot was removed from the plot.

## Notes

- Module import creates figure/panel globals; this is a singleton-style render script.
- Designed for 2D orbit visualization from precomputed series data.
- For architecture goals and invariants, see `docs/project-charter.md`.
