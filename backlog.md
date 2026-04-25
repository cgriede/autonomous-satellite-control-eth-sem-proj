# Backlog

## Recently completed (latest refactor)
- [x] unified episode execution on canonical simulation pipeline (`SimulationStepper`)
- [x] `SimulationStateSeries` returned as mandatory episode artifact in training runtime
- [x] removed subprocess-based Sat Sim export reruns in train/eval; render now consumes in-memory episode series
- [x] moved timing ownership to explicit constants (`SIMULATION.simulation_timestep`, `SIMULATION.controller_update_interval`)
- [x] moved playback defaults to render constants (`RENDER.animation_interval`, `RENDER.default_speed_multiplier`)
- [x] made observation targets explicit mission objects (`MISSION.OBSERVATION_TARGETS`)
- [x] split simulation internals into kernels (`scheduler`, `dynamics_kernel`, `sensor_kernel`, `reward_kernel`)
- [x] added simulation loading progress bar (`tqdm`) in centralized rollout path

## Bugs
- 1d strip is updated incorrectly (still)
- clouds are not (visibly) moving in the simulation


## structural issues
- reduce mission/global constant coupling in `training_runtime` by passing scenario/config explicitly
- simplify/rename env adapter API to reflect non-Gym-physics behavior
- remove deprecated compatibility args in `run_simulation` once call sites are migrated

## features
- optimize simulation performance for fast ML iteration
- add telemetry: environment: avg cloud speed
 - [x] reward-over-time linear plot in simulation render (Matplotlib, x=time_s, source=SimulationStateSeries)



