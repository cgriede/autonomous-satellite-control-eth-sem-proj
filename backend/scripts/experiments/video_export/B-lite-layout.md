# Hypothesis B — lite export layout

## Claim

Disabling **telemetry, reward, torque, and secondary 1D cam** panels during `RenderMode.EXPORT` reduces per-frame matplotlib work enough for **≥1.2×** export speedup while keeping orbit + closeup + primary cam strip.

## Treatment

- Set `SHOW_TELEMETRY`, `SHOW_REWARD_PLOT`, `SHOW_TORQUE_PLOT`, `SHOW_1D_SAT_VIEW_SECONDARY` to `False` before `render_from_series` builds panels
- Same frame count and DPI as baseline

## Speed gate

≥1.2× baseline `export_wall_s` reduction on `high_cloud_notebook` fixture.

## Parity

- H.264 output required
- Layout differs from full dashboard (by design); orbit/cloud story retained

## Promotion target

Export-only panel toggles in `render_from_series` when `render_mode == RenderMode.EXPORT`.
