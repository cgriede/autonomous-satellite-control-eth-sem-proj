# User Manual: Controllers and Rendering

This manual explains how to run controller experiments and how rendering maps to simulation behavior.

## Project semantics (must hold)

- One episode is one canonical simulation rollout over the configured overflight window.
- `SimulationStateSeries` is the required episode-level artifact.
- Train/eval/render are expected to consume the same simulation core outputs.
- Renderer is strictly view-only and must not run numeric simulation logic.

## Environment Setup

From the repository root:

```bash
conda activate auto-sat
cd backend
```

## Simulation Setup API (SimulationRunner v1)

The `EnvironmentSetup` + `EpisodeRunner` API is the canonical way to configure and run episodes.
It replaces hand-assembling 10+ kwargs to `SimulationStepper` in each caller.

### Concepts

| Type | Responsibility |
|---|---|
| `EnvironmentSetup` | Declarative config (satellite, orbit, cameras, overrides). Call `.resolve()` to validate and fill defaults. |
| `OrbitConfig` | Altitude and orbit shaping params (all optional; omitted → SIMULATION constants). |
| `SimulationOverrides` | Per-run overrides for kernel params and `RewardConfig`. |
| `ResolvedSimulationSetup` | Frozen, fully-populated result of `.resolve()`. Passed to the stepper factory. |
| `build_stepper(resolved, *, simulation_config)` | Shared factory in `simulation/stepper_factory.py`. Sole constructor of `SimulationStepper` from a resolved setup. |
| `EpisodeRunner(setup).run_serial(agent, mode=…)` | Agent loop in `autonomous_control/episode_runner.py`. Returns `EpisodeResult` with `SimulationStateSeries`. |
| `build_setup(seed=, include_cameras=)` | Convenience builder in `mission_profiles/s01_multiple_targets_fwd_fish.py`. |

### Minimal episode (Python / notebook)

```python
from environment_definition.mission_profiles.s01_multiple_targets_fwd_fish import build_setup
from autonomous_control.episode_runner import EpisodeRunner

setup = build_setup(seed=7)                          # samples altitude, attaches cameras
result = EpisodeRunner(setup).run_serial(            # returns EpisodeResult
    agent,
    mode="warmup",
    warmup_controller="random",
)
series = result.simulation_series                    # SimulationStateSeries
```

### Export a render video after a run

```python
from utils.notebook.video import _export_render_video

_export_render_video(simulation_series=result.simulation_series, out_path=video_path)
```

### Custom orbit altitude

```python
from simulation.setup_types import OrbitConfig, EnvironmentSetup
from environment_definition.constants.UNIT_REGISTRY import UREG as ureg
from environment_definition.mission_profiles.s01_multiple_targets_fwd_fish import SATELLITE

setup = EnvironmentSetup(
    satellite=SATELLITE,
    orbit=OrbitConfig(altitude=540 * ureg.km),
)
result = EpisodeRunner(setup).run_serial(agent, mode="train")
```

### Override reward config or kernel params

```python
from simulation.setup_types import SimulationOverrides
from autonomous_control.reward import RewardConfig

setup = build_setup(seed=7, include_cameras=False)
setup = EnvironmentSetup(
    satellite=setup.satellite,
    orbit=setup.orbit,
    simulation_overrides=SimulationOverrides(
        reward_config=RewardConfig(enable_area_novelty=True, k_area_novelty=2.0),
        camera_pixel_ray_samples=32,
    ),
)
result = EpisodeRunner(setup).run_serial(agent, mode="train")
```

### Bus-only / payload-agnostic episode (no cameras)

```python
setup = build_setup(seed=0, include_cameras=False)   # cameras=()
result = EpisodeRunner(setup).run_serial(agent, mode="train")
```

### run_simulation (baseline/random rollout, no RL agent)

```python
from environment_definition.mission_profiles.s01_multiple_targets_fwd_fish import build_setup
from environment_definition.constants.SIMULATION import SimulationConfig, RenderMode
from simulation.run_simulation import run_simulation

setup = build_setup(seed=0, include_cameras=False)
series = run_simulation(
    setup=setup,
    simulation_config=SimulationConfig(render_mode=RenderMode.HEADLESS, controller_mode="random"),
)
```

### Validation rules enforced by `.resolve()`

| Condition | Error |
|---|---|
| `satellite` not set | `SimulationSetupError` |
| `orbit.altitude` not set | `SimulationSetupError` |
| `cameras` empty + `require_camera=True` | `SimulationSetupError` |

### What `.resolve()` auto-fills (payload-agnostic defaults)

| Field | Source |
|---|---|
| `clouds` | `SIMULATION.clouds` |
| `target_areas` | `MISSION.OBSERVATION_TARGET_AREAS` |
| `theta_center_rad` | `SIMULATION.theta_center` |
| `start_angle_deg`, `end_angle_deg` | `los_theta_offsets_deg(altitude, margin)` |
| `sat_motion_span_scale` | `SIMULATION.sat_motion_span_scale` |
| `sat_z_offset_deg` | `SIMULATION.sat_z_offset` |
| `camera_pixel_ray_samples` | `SIMULATION.camera_pixel_ray_samples` |
| `camera_observation_line_n_bins` | `SIMULATION.camera_observation_line_n_bins` |

Cameras are **never** auto-filled; they remain `()` unless set in `build_setup()` or the config.

### Backward compatibility

`run_episode(env, agent, ...)` in `training_runtime` still works unchanged.
It now internally delegates to `EpisodeRunner`. The optional `setup=` parameter lets callers pass a `EnvironmentSetup` directly:

```python
from autonomous_control.training_runtime import run_episode

result = run_episode(env, agent, mode="warmup", setup=build_setup(seed=7))
```

---

## Controller Modes

Training/evaluation scripts support:

- `mpo`: learned MPO policy (`MPOAgent`), supports checkpoint load/save.
- `baseline`: deterministic max-torque sweep policy.
- `random`: uniform random torque policy.

Note:
- The long-term architecture target is hierarchical mission control over OBC low-level control.
- Current direct wheel-torque control is an interim experimental interface.

## Train Controllers

```bash
python scripts/train_sat_agent.py --controller-mode mpo --seed 0 --train-episodes 20 --warmup-episodes 0
python scripts/train_sat_agent.py --controller-mode baseline --seed 0 --train-episodes 20
python scripts/train_sat_agent.py --controller-mode random --seed 0 --train-episodes 20
```

Notes:

- `--controller-mode mpo` is the only mode that writes an MPO checkpoint (`agent.pt`).
- Baseline/random runs are controller rollouts without MPO weight updates.

## Evaluate Controllers

```bash
python scripts/eval_sat_agent.py --controller-mode mpo --checkpoint autonomous_control/runs/<run_id>/agent.pt --eval-episodes 5
python scripts/eval_sat_agent.py --controller-mode baseline --eval-episodes 5
python scripts/eval_sat_agent.py --controller-mode random --eval-episodes 5
```

## Rendering and Export

Render CLI currently supports simulation controller modes:

- `baseline`
- `random`

Run interactive render:

```bash
python render/render_main.py --render-mode interactive --controller-mode random
```

Export one-pass video:

```bash
python render/render_main.py --render-mode export --controller-mode baseline --save-one-pass-30x
```

Optional output path:

```bash
python render/render_main.py --render-mode export --controller-mode random --save-one-pass-30x --output-path autonomous_control/runs/my_run/sat_sim_export.mp4
```

## Fidelity Rule (What You See Is What Runs)

- Rendered behavior must come from the real simulation model and selected controller mode.
- No hidden substitute controller is used in visualization.
- If a model component exists (for example reaction-wheel dynamics), that same modeled behavior drives both simulation state and rendered output.

## Reward authority

- Runtime reward behavior in code is canonical.
- The semester project PDF is design context.
- Any intentional delta between PDF and code must be documented (for example, energy term implementation controlled via flags).

## VS Code Launch Configs

Useful launch entries in `.vscode/launch.json`:

- `Sat Sim Interactive`
- `Sat Sim Export`
- `MPO: Train satellite agent`
- `MPO: Eval satellite agent`
