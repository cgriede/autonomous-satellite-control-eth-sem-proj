# Backlog (archive / narrative)

**Source of truth:** [`backlog.xlsx`](backlog.xlsx) — edit rows there; use `python backend/scripts/backlog_xlsx.py list|check|init`.

Columns: `uid`, `Sprint`, `prio`, `Size`, `status`, `dep on`, `name`, `notes / blockers`.

This file keeps session notes and cumulative history; do not treat it as the live sprint board.

After notable process mistakes or breakthroughs, run **`/learn-skill`** to update agent skills (see `.cursor/memory/learnings.md`).

## Session 2026-06-03 (review)
**Branch:** `feat/backend-stuff` (1 commit ahead of origin: `3695333` perf batch cloud raytracing in accelerated kernel). Large **uncommitted** WIP (~3.5k LOC) — not yet split into commits.

### Done today (substantive)

| Area | Outcome |
|------|---------|
| **S01 notebook 01 — target grid** | Orbit-disk / polar–meridian geometry (`orbit_disk_polar_meridian.py`), render framing fixes, notebook refresh. |
| **S01 notebook 02 — clouds** | `s01_utils/cloud_formation.py` + `cloud_verification.py`; coast sim + MP4 export path; cloud arc precompute in stepper. |
| **S01 notebook 03 — movement constraints** | `AttitudeSafetyController`, `ATTITUDE_SAFETY` constants, stepper hook, `DelayedMaxTorquePolicy` baseline, notebook + `movement_constraints_patch.py`; unit tests green. |
| **Sim performance (hypothesis cycle)** | **C** fused multi-camera ray batch → promoted `sensor_kernel.py` (~1.6× micro, ~1.18× episode). **D** tensor cloud hits → promoted `camera_2d.py` (~2.9× line kernel @ 63 clouds). Experiment harness under `backend/scripts/experiments/sensor_ray_batch/`. |
| **Profiling** | `sim_timing/` experiment: high_cloud ~189 steps/s; export dominates wall time (~82 s vs ~10 s sim). |
| **Video export experiments** | **A** `frame_stride=2` → ~2× export speedup (supported, not yet promoted to production render). **B** lite layout → measured; harness under `video_export/`. |
| **Render / UX** | Closeup, telemetry, torque plot, static orbit plane; `simulation_info` pre-rollout summary; notebook `video_archive` helper. |
| **Docs** | `environment-hyperparameters.md`, `technical-constants.md`, `render-api.md` touched for new constants/behavior. |

### In progress / not closed

- **03 movement constraints:** Human MP4 gate (`movement_constraints_delayed_max.mp4`) exists under `artifacts/video_archive/`; e2e tests **red** — `SimulationConfig` no longer accepts `controller_mode` (tests need update to current API).
- **02 clouds:** Formation generator works in notebook; `test_s01_cloud_formation_sim_integration` **red**; cloud arc precompute parity tests **red** (2).
- **Plan `clouds_and_target_grid`:** Many todos still open at production level (min observation time, stillness score, off-nadir damage log, secondary camera semantics in reward).
- **Promote video export wins:** Frame stride and/or lite export layout not wired into default `render_main` export path.

### Suggested next session (pick 1–2)

1. Fix integration test drift (`controller_mode`, cloud precompute parity) → green gates for notebooks 02–03.
2. Promote `frame_stride` (or notebook-only export flag) so cloud/movement MP4 iteration is tolerable.
3. Close movement-constraints plan acceptance (e2e + required artifact path stable).
4. Triage uncommitted tree into focused commits (notebooks/utils vs sim/render vs experiments vs cursor skills).

---

## Recently completed (cumulative)

- [x] unified episode execution on canonical simulation pipeline (`SimulationStepper`)
- [x] `SimulationStateSeries` returned as mandatory episode artifact in training runtime
- [x] removed subprocess-based Sat Sim export reruns in train/eval; render now consumes in-memory episode series
- [x] moved timing ownership to explicit constants (`SIMULATION.simulation_timestep`, `SIMULATION.controller_update_interval`)
- [x] moved playback defaults to render constants (`RENDER.animation_interval`, `RENDER.default_speed_multiplier`)
- [x] made observation targets explicit mission objects (`MISSION.OBSERVATION_TARGETS`)
- [x] split simulation internals into kernels (`scheduler`, `dynamics_kernel`, `sensor_kernel`, `reward_kernel`)
- [x] added simulation loading progress bar (`tqdm`) in centralized rollout path
- [x] reward-over-time linear plot in simulation render (Matplotlib, x=time_s, source=SimulationStateSeries)
- [x] **2026-06-03** sensor kernel: fused multi-camera ray batch (hypothesis C, promoted)
- [x] **2026-06-03** camera_2d: vectorized tensor cloud×ray hits (hypothesis D, promoted)
- [x] **2026-06-03** sim_timing experiment harness + high_cloud profile baseline
- [x] **2026-06-03** S01 cloud formation generator + notebook 02 verification utilities
- [x] **2026-06-03** attitude safety controller + `ATTITUDE_SAFETY` constants + unit tests (notebook 03 core logic)

## Bugs

- 1d strip is updated incorrectly (still)
- clouds are not (visibly) moving in the simulation — formation generator exists; kinematic motion / render feedback still weak or missing
- integration tests out of sync with `SimulationConfig` / cloud precompute (movement constraints + cloud formation + `test_cloud_arc_precompute`)

## Structural issues

- reduce mission/global constant coupling in `training_runtime` by passing scenario/config explicitly
- simplify/rename env adapter API to reflect non-Gym-physics behavior
- remove deprecated compatibility args in `run_simulation` once call sites are migrated
- add a strict JSON-driven simulation configuration loader that validates the full runtime config and throws hard errors for ill-defined inputs, including nested satellite, torque policy, and camera specs; do not rely on scattered constants
- commit and split today's uncommitted WIP (notebooks, experiments, sim/render, cursor skills)

## Features

- optimize simulation performance for fast ML iteration — **partial:** C/D promoted; profiling in place; export still bottleneck
- promote video export `frame_stride=2` (or configurable) after notebook validation
- add telemetry: environment avg cloud speed
- complete S01 notebook 03: e2e tests + stable required MP4 artifact path
- complete S01 notebook 02: sim integration test green + visible cloud motion
- clouds_and_target_grid plan: min observation time, stillness, area score, off-nadir damage (main camera), secondary FOV semantics — see `.cursor/plans/v2/clouds_and_target_grid_808c8677.plan.md`


#TODO: Move Todos out of backlog into done production

#TODO(fr) make telemetry box nicer. Plot the most interesting values