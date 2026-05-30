# 02 - Ubiquitous Naming + Physical Representation + Description

Use this as the naming contract for code, tests, docs, and PR language.

## Non-Negotiable Invariants

- One `Episode` = one canonical simulation rollout.
- `Train`/`Eval`/`Render` consume the same canonical simulation outputs.
- `Simulation` owns physics, camera simulation, and reward-critical world signals.
- `Render` is view-only.
- `SimulationStateSeries` is the episode-level artifact contract.

## Canonical Vocabulary

| Term | Canonical meaning | Prefer | Avoid |
|---|---|---|---|
| `Episode` | One canonical rollout | `episode_idx` | "render run" as separate physics run |
| `SimulationTimestepState` | One-step frozen snapshot | `timestep`/`step_state` | generic "frame state" |
| `SimulationStateSeries` | Episode-level arrays + metadata | `series`/`state_series` | ad-hoc episode dicts |
| `SimulationMetadata` | Episode metadata bundle | `metadata` | scattered loose metadata |
| `sim_time_s` | Simulation time seconds | `_s` suffix | unitless `time` |
| `theta_orbit_rad` | Orbital angle radians | `_rad` suffix | degree value in `_rad` var |
| `radius_km` | Orbital radius km | `_km` suffix | mixed unit same symbol |
| `body_z_angle_rad` | Body Z orientation radians | explicit axis + unit | generic `angle` |
| `omega_sat_rad_s` | Satellite angular rate | `_rad_s` suffix | unitless omega names |
| `camera_gsd_m` | Ground sample distance m | `_m` suffix | implicit pixel-size semantics |
| `camera_observation_line_codes` | Per-bin classification codes | plural `*_codes` | float/string labels |
| `camera_center_ray_observation_code` | Center-ray class code | singular `*_code` | plural name for scalar |
| `fixed_ground_line_codes` | Fixed-ground per-bin codes | explicit `fixed_ground_*` | conflated camera code names |
| `simulation_reward` | Per-step canonical reward | `simulation_reward` | recomputed reward in render |
| `RewardSignals` | Inputs to reward combiner | typed signal bundle | positional/anonymous tuples |
| `ControllerFeatureConfig` | Explicit selected feature keys | typed config | implicit/global feature list |
| `select_controller_inputs_from_timestep` | Deterministic key selection from one timestep | verb-led selector | generic `build_inputs` |
| `Mission-level control` | High-level architecture target | use as architecture term | mixing with low-level torque control |

## Naming Rules

- Reuse canonical terms above; avoid synonym drift.
- Encode units in symbol names unless type enforces units.
- Keep cardinality explicit: timestep (`SimulationTimestepState`) vs series (`SimulationStateSeries`).
- Use nouns for types, verbs for operations (`select_*`, `compute_*`, `run_*`).
- For codes: scalar uses `*_code`, vector/matrix uses `*_codes`.

## Physical Representation Rules

- Physical quantities should use pint where applicable.
- Define constants once with explicit units.
- Convert units at module/API boundaries, not ad hoc across consumers.
- If converting to plain float, keep explicit unit suffix in the field name.

### Anti-Patterns

- Unitless physical values with ambiguous names.
- Mixed units under one symbol name.
- Computing physics/camera/reward-critical signals in render.
- Re-running simulation for visualization when canonical outputs already exist.

## Data Representation Rules

### `SimulationTimestepState`
- Single-step immutable snapshot for step-local decisions and diagnostics.
- Not a substitute for episode-level artifact contracts.

### `SimulationStateSeries`
- Canonical episode artifact for train/eval/render.
- Shared timestep axis and dtype/shape consistency must be preserved.
- Extend this contract when new episode-level signals are needed.

## New Term Template (Copy/Paste)

```markdown
### `Term`
- Definition (one sentence):
- Why needed:
- Canonical artifact level (`SimulationTimestepState` / `SimulationStateSeries` / metadata / other):
- Owning layer (`simulation` / `autonomous_control` / `environment_definition` / `render(view-only)`):
- Unit rule (if physical):
- Allowed symbol/file examples:
- Forbidden synonyms/anti-pattern uses:
- Validation check (test/assertion):
```
