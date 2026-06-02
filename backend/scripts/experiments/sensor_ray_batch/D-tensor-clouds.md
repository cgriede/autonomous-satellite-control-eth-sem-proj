# Hypothesis D — Tensorized cloud×ray intersection

## Statement

Replace the `for cloud_spec in cloud_arc_specs` loop in `_batch_cloud_hits_t_best` with one vectorized `(n_clouds, n_rays)` pass (broadcast radii, vectorized arc masks, `nanmin` along cloud axis).

## Falsification

- Parity failures vs production `kernel_backend=accelerated`
- `line_speedup_per_call` < 2× on `high_cloud_notebook` fixture
- Regression > 5% at 5 clouds on `low_cloud_dual`

## Implementation

- Fork `camera_2d.py` in `d_tensor_clouds/camera_2d_fork.py`
- Patch import site in runner only (same pattern as Tier A)

## Success bar

- Primary KPI: `line_benchmark.line_speedup_per_call` ≥ **2×** at high cloud count
- Guardrail: exact parity on observation lines + strip cloud fraction

## Forbidden tunables

Same as hypothesis C
