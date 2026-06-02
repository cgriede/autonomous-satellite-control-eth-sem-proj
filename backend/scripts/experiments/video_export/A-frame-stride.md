# Hypothesis A — frame stride

## Claim

Exporting every **2nd** sim-time sample halves matplotlib `canvas.draw()` calls and yields **≥1.5×** lower `export_wall_s` with acceptable motion coarseness for notebook previews.

## Treatment

- `frame_stride=2` in forked `save_one_pass_video_fork`
- Same `export_fps`, `export_dpi`, full dashboard layout
- Video duration shrinks (~half frames); motion is coarser

## Speed gate

≥1.5× baseline `export_wall_s` reduction on `high_cloud_notebook` fixture.

## Parity

- Output must re-encode to **H.264** for notebook playback
- Not pixel-identical to baseline (by design)

## Promotion target

`SIMULATION.export_frame_stride` or `RENDER.export_frame_stride` used in production `save_one_pass_video_30x`.
