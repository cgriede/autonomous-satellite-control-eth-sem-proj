# Sensor ray batch experiments

Isolated hypothesis cycle for sensor-kernel performance: fused multi-camera ray batch (C) and tensorized cloud×ray intersection (D).

Production code stays read-only until promotion.

## Frozen fixtures

| Fixture | Clouds | Purpose |
|---------|--------|---------|
| `low_cloud_dual` | 5–6, seed=42 rng | Parity + episode speed |
| `high_cloud_notebook` | 50–200, pickled `fixtures/high_cloud_seed42.pkl` | Cloud scaling |

## Run commands (repo root, PowerShell)

```powershell
conda activate ASC; python backend/scripts/experiments/sensor_ray_batch/run_baseline.py
conda activate ASC; python backend/scripts/experiments/sensor_ray_batch/c_fuse_cameras/run_c1.py
conda activate ASC; python backend/scripts/experiments/sensor_ray_batch/d_tensor_clouds/run_d1.py
```

## Layout

| Path | Purpose |
|------|---------|
| `_frozen_baseline.py` | Frozen setups + high-cloud fixture |
| `_runner_common.py` | Timing, parity, fixed-contract JSON |
| `run_baseline.py` | Shared production baseline |
| `c_fuse_cameras/` | Hypothesis C fork |
| `d_tensor_clouds/` | Hypothesis D fork |
| `results/` | baseline.json, analysis cards |

## KPIs

- `micro_benchmark.total_s` (strip + primary + secondary)
- `steps_per_s` on full coast episode
- Parity: exact match on observation codes and cloud_blocked_fraction

## Promotion status

- **D tensor cloud hits** — promoted to `backend/simulation/camera_2d.py` (`_batch_cloud_hits_t_best`)
- **C fused ray batch** — promoted to `backend/simulation/sensor_kernel.py` (accelerated path)

Fork runners remain for regression comparison against frozen baselines.
