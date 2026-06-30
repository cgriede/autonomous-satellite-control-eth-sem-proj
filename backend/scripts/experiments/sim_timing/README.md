# Simulation timing profiler

Experiment-only instrumentation for the coast simulation loop. Production kernels are **not** modified; hooks monkey-patch during the profile run and restore on exit.

## Categories (binned)

| Key | Meaning |
|-----|---------|
| `controller_actuator` | Policy / controller `get_action` (zero for coast) |
| `robotics_dynamics` | `DynamicsKernel.propagate` (RW + attitude) |
| `orbit_kinematics` | Precomputed orbit XY lookup per step |
| `environment_clouds` | `compute_cloud_arc_specs_at_time` |
| `sensor_camera_rays` | Fused / legacy camera ray kernel |
| `geodesy` | Disk ↔ geodetic transforms |
| `footprint_target` | Target stripe overlap & novelty |
| `reward_ml` | `RewardKernel.evaluate` |
| `stepper_bookkeeping` | Residual per-step overhead |
| `render` | Render setup & frame draw (optional) |
| `export_video` | MP4 encode (optional) |

Output includes **top 7 consumers** by total wall time.

## Run (repo root, PowerShell)

Documented in `.cursor/skills/performance-optimization/SKILL.md` and `python-runtime-environment` (env: **auto-sat**).

```powershell
conda activate auto-sat
python backend/scripts/experiments/sim_timing/run_profile.py
python backend/scripts/experiments/sim_timing/run_profile.py --scenario high_cloud
python backend/scripts/experiments/sim_timing/run_profile.py --scenario high_cloud --with-render
```

Results: `results/{scenario}_timing.json` and `.md`.

Fixtures reuse `sensor_ray_batch/_frozen_baseline.py` (5–6 clouds low, 50–200 high notebook). Use `--scenario sat_sim_interactive` to mirror **Sat Sim Interactive** (`simulation_runner.py`).

## Layout

| Path | Purpose |
|------|---------|
| `_timing_collector.py` | Category bins + top-N report |
| `_hooks.py` | Install / uninstall monkey-patches |
| `_profile_runner.py` | Instrumented rollout + optional render |
| `_timing_fixtures.py` | Frozen setups + `sat_sim_interactive` mirror |
| `run_profile.py` | CLI entry point |

## Notes

- Orbit propagation is **precomputed** at stepper init; only array lookup is timed under `orbit_kinematics`.
- ML **training** is out of scope (coast episode only). `reward_ml` covers reward scoring per step.
- Render/export are episode-level and only run with `--with-render`.
