# Hypothesis C — Fused multi-camera ray batch

## Statement

Replace three separate ray-march passes in `SensorKernel.evaluate` (strip 96 + primary line 100 + secondary line 200) with **one** fused `_batch_first_hit_earth_or_clouds` call per timestep, then slice results back into strip stats and observation lines.

## Falsification

- Any parity mismatch vs production on observation codes, cloud_blocked_fraction, or strip metadata
- `micro_benchmark.total_s` speedup < 1.5× on `low_cloud_dual`
- Episode `steps_per_s` not improved on `low_cloud_dual`

## Implementation

- Fork `sensor_kernel.py` only; import production `camera_2d` unchanged
- Keep cheap footprint earth rays (left/center/right) and center first-hit as production helpers
- Fuse cloud/earth batch for strip pixel rays + primary bins + secondary bins

## Success bar

- Primary KPI: `micro_benchmark.total_s` ≥ **1.5×** vs shared baseline
- Guardrail: exact parity on all sensor outputs

## Forbidden tunables

`simulation_timestep`, bin counts, `camera_pixel_ray_samples`, cloud count bounds
