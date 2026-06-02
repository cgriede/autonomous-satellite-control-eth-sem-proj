# Cloud kernel speed experiments

Performance experiments for batched cloud raytracing (Tier A) and FOV culling (Tier D).
Separate from s01 notebook feature work (`backend/notebooks/s01/`).

**Promotion status:** Tier A (batched NumPy rays in `simulation/camera_2d.py`) is in production. Tier D (FOV cull) was **not** promoted — neutral on the frozen 108-cloud benchmark; cull code lives under `cloud_fov_cull.py` in this folder only.

## Frozen baseline

- s01 coast setup, `seed=0`, dual-camera
- Clouds from `cloud_formation_generator` with notebook bounds (`cloud_number_bounds=(5, 6)`)
- Production `camera_2d.py` — Tier A promoted; Tier D experiment-only

## Run commands (repo root, PowerShell)

```powershell
conda activate ASC; python backend/scripts/experiments/cloud_kernel_speed/run_baseline.py
conda activate ASC; python backend/scripts/experiments/cloud_kernel_speed/a_vectorized_line/run_a1.py
conda activate ASC; python backend/scripts/experiments/cloud_kernel_speed/b_fov_cull/run_b1.py
```

## Layout

| Path | Purpose |
|------|---------|
| `_frozen_baseline.py` | Shared cloud fixture + setup |
| `_runner_common.py` | Timing, parity, JSON output |
| `results/baseline.json` | Production timing evidence |
| `a_vectorized_line/` | Tier A fork |
| `b_fov_cull/` | Tier D on top of A1 |

## KPIs

- `wall_time_s`, `steps_per_s`, sensor breakdown (strip / primary line / secondary line)
- Parity: observation line codes vs `kernel_backend=python` (exact match)
- ASCII observation lines at sample timesteps

## Promotion

Supported changes port to `backend/simulation/camera_2d.py` only after parity + speedup gates pass.
