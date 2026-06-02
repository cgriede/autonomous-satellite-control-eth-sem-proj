# Performance optimization — reference

## sim_timing implementation

| File | Role |
|------|------|
| `_timing_collector.py` | `TimingCollector`, `CATEGORY_LABELS`, `report(top_n=7)` |
| `_hooks.py` | Patches kernels; restores on `uninstall()` |
| `_profile_runner.py` | `run_instrumented_episode`, optional `run_instrumented_with_render` |
| `_frozen_baseline.py` | Re-exports `sensor_ray_batch` setups |
| `run_profile.py` | CLI: `--scenario`, `--with-render` |

### Hook targets (production, patched only during run)

- `DynamicsKernel.propagate` → `robotics_dynamics`
- `compute_cloud_arc_specs_at_time` on **`camera_2d` and `sensor_kernel`** → `environment_clouds`
- `_evaluate_fused_accelerated` / `_evaluate_legacy` → `sensor_camera_rays`
- `RewardKernel.evaluate` → `reward_ml`
- `disk_xy_km_to_geodetic_deg` on **`orbit_disk_wgs84` and `stepper`** → `geodesy`
- `batch_disk_xy_rows_km_to_geodetic_deg` → `geodesy`
- `circle_stripe_footprint_overlap_ratio` → `footprint_target`
- `SimulationStepper._satellite_xy_km` → `orbit_kinematics`
- `SimulationStepper.step` → residual → `stepper_bookkeeping`
- Controller loop in `_profile_runner` → `controller_actuator`
- `render_from_series` / `save_one_pass_video_30x` → `render` / `export_video`

### Report JSON fields

- `sim_loop_wall_s`, `n_steps`, `steps_per_s`, `per_step_wall_ms`
- `measured_in_loop_s`, `unaccounted_in_loop_s`
- `categories[]`: `key`, `label`, `total_s`, `per_step_ms`, `pct_of_sim_loop`
- `top_7_consumers[]`

## Interpreting “bookkeeping”

High `stepper_bookkeeping` usually means **unpatched work** (stale imports, array writes, classify paths), not mysterious overhead. Fix hooks before optimizing bookkeeping.

## Game engines vs this stack

Game engines optimize GPU rasterization at ~2M pixels/frame. This project’s coast loop is mostly **CPU analytic ray tests** and **per-step cloud spec builds**. A game engine does not replace `run_simulation()` semantics without a full reimplementation.

## Micro-benchmarks vs episode profile

| Tool | Measures |
|------|----------|
| `sim_timing` | Full episode, realistic mix, top categories |
| `sensor_ray_batch/run_baseline.py` | `micro_sensor_evaluate`, isolated sensor calls |
| `cloud_kernel_speed/` | Cloud kernel tiers, cull experiments |

Use **episode profile** to choose what to optimize; use **micro** to validate a kernel change in isolation.

## Tests

`backend/tests/test_sim_timing_hooks.py` — hook install/uninstall restore, low-cloud smoke profile.
