# Render Module API Interface

This document describes the public interface exposed by the current render module implementation in `backend/render/first_plot.py`.

## Overview

- **Module role:** render a 2D Earth-orbit scene with a satellite, animated state updates, and optional one-pass MP4 export.
- **Current boundary:** single Python script module (`first_plot.py`) with module-level initialization and function APIs.
- **Execution context:** intended to run with `backend/` as import root (see `.vscode/launch.json`).

## Runtime Context and Dependencies

- **Core libraries:** `numpy`, `matplotlib` (`pyplot`, `FuncAnimation`, widgets, patches).
- **Optional export fallback:** `cv2` (OpenCV) used only if `ffmpeg` writer is unavailable.
- **Project dependencies:**
  - `environment_definition.constants` (`EARTH_RADIUS`, `EARTH_GRAVITATIONAL_PARAMETER`, `SIMULATION`, `RENDER`, `UREG`)
  - `environment_definition.mission_profiles.mission_1_random_fl` (`SATELLITE_ALTITUDE`)
  - `utils.flight_geometry.line_of_sight` (`minimum_contact_angle`)
- **State model:** module-level globals hold simulation clock, speed multiplier, spin rate, and pre-created matplotlib artists.

## Public API

### `set_sim_speed(multiplier)`

- **Purpose:** set live animation simulation speed multiplier.
- **Parameters:**
  - `multiplier` (`float`-convertible): scales simulated seconds advanced per render tick.
- **Returns:** `None`.
- **Side effects:** updates module global `sim_speed_multiplier`.
- **Failure modes:** `ValueError`/`TypeError` may surface if `multiplier` is not float-convertible.

### `set_sat_body_rotation_rate(rate, unit="arcsec")`

- **Purpose:** set constant inertial-frame body spin rate used for +z-axis orientation.
- **Parameters:**
  - `rate` (`float`-convertible): spin magnitude in the selected unit.
  - `unit` (`str`): one of `"arcsec"`, `"arcmin"`, `"deg"`.
- **Returns:** `None`.
- **Side effects:**
  - updates `sat_body_rotation_rate_rad_s` (internal rad/s value),
  - updates `sat_body_rotation_rate_label` (UI text).
- **Failure modes:**
  - raises `ValueError` for unsupported `unit`,
  - `ValueError`/`TypeError` may surface if `rate` is not float-convertible.

### `get_satellite_z_axis_dir(theta_now, elapsed_s)`

- **Purpose:** compute current body +z unit direction from initial angle and constant spin.
- **Parameters:**
  - `theta_now` (`float`): accepted but currently not used in computation.
  - `elapsed_s` (`float`): elapsed simulated time in seconds.
- **Returns:** `numpy.ndarray` shape `(2,)`, direction vector `[cos(angle), sin(angle)]`.
- **Side effects:** none.
- **Failure modes:** numeric conversion/runtime warnings if invalid numeric inputs are passed.

### `init()`

- **Purpose:** reset artists and simulation time before animation starts.
- **Parameters:** none.
- **Returns:** tuple of matplotlib artists:
  - `sat`, `obs_to_sat_line`, `trail`, `cone`, `z_axis_arrow`, `z_axis_label`, `info_text`.
- **Side effects:**
  - sets global `sim_time_s = 0.0`,
  - resets artist geometry/text.
- **Failure modes:** any matplotlib artist state errors propagate.

### `set_scene_at_time(sim_time_local, wrap_orbit=True, speed_label=None)`

- **Purpose:** render/update the full scene for an explicit simulation timestamp.
- **Parameters:**
  - `sim_time_local` (`float`, seconds): timestamp used to compute orbital angle and spin state.
  - `wrap_orbit` (`bool`, default `True`):
    - `True`: orbit angle wraps via modulo over configured span,
    - `False`: orbit angle clamps at end of span.
  - `speed_label` (`float | None`, default `None`): optional value used in info text instead of live multiplier.
- **Returns:** same artist tuple as `init()`.
- **Side effects:** mutates all scene artists (satellite point, LOS line, trail, cone, z-axis arrow/label, info bar).
- **Failure modes:** numeric errors or matplotlib artist update errors propagate.

### `update(frame)`

- **Purpose:** animation callback for live playback (`FuncAnimation`).
- **Parameters:**
  - `frame` (`int`): frame index (not otherwise used directly).
- **Returns:** same artist tuple as `set_scene_at_time(...)`.
- **Side effects:**
  - increments global `sim_time_s` by `animation_interval_ms/1000 * sim_speed_multiplier`,
  - updates all scene artists by delegating to `set_scene_at_time`.
- **Failure modes:** inherits failures from numeric update and `set_scene_at_time`.

### `save_one_pass_video_30x_to_project_root()`

- **Purpose:** export a non-looping MP4 pass using configured export speed.
- **Parameters:** none.
- **Returns:** `pathlib.Path` to output file (project root + configured filename).
- **Side effects:**
  - writes MP4 file to project root (`RENDER.export_filename`),
  - runs frame-by-frame rendering in the current matplotlib figure.
- **Writer behavior:**
  - uses matplotlib `ffmpeg` writer when available,
  - falls back to OpenCV writer (`mp4v`) when `ffmpeg` is unavailable.
- **Failure modes:**
  - raises runtime errors from writer initialization/saving,
  - raises `RuntimeError` if OpenCV fallback writer cannot be opened.

## CLI Interface

`first_plot.py` exposes a script entrypoint:

- **Default mode:** live interactive animation window.
- **Flag:** `--save-one-pass-30x`
  - runs export path instead of live window,
  - prints saved output path,
  - output file location resolves to project root (`Path(__file__).resolve().parents[2] / RENDER.export_filename`).

Example:

```bash
python backend/render/first_plot.py --save-one-pass-30x
```

## State and Side Effects

- Module import performs substantial initialization:
  - derives physical/orbital values,
  - creates `fig`, `ax`, static scene, widgets, and artists.
- API functions operate on module singleton state; this is not a stateless library API.
- Repeated imports/reloads can recreate figures and widgets.

## Known Constraints

- Designed around 2D circular orbit visualization assumptions.
- Uses matplotlib GUI/event-loop behavior for live mode.
- Export fallback requires `cv2` installed when `ffmpeg` is not present.
- Some function contracts are pragmatic rather than strict (for example `theta_now` is accepted in `get_satellite_z_axis_dir` but currently unused).
