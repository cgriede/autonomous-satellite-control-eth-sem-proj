# Autonomous Satellite Control (ETH SEM Project)

## Project aim

The project aims to build autonomous mission-oriented satellite control that maximizes observation value while respecting physical constraints.

- Near-term: fast, cloud-aware 2D simulation and control development.
- Long-term: hierarchical mission planner over OBC low-level control, with extension to 3D, real imagery, and area targets.

See the formal charter in `docs/project-charter.md`.

## Architecture spec: simulation vs rendering

This repository separates **numeric simulation** from **rendering/visualization**.

- **Simulation** (`backend/simulation/*`)
  - Owns all numeric propagation / integration.
  - Owns physics, camera/cloud sensing, and reward signal computation.
  - Produces typed simulation outputs such as `simulation.state_types.SimulationStateSeries`.
  - Canonical entrypoint for rendered runs: `simulation.run_simulation.run_simulation()`.

- **Rendering** (`backend/render/*`)
  - View-only: consumes simulation outputs and draws/exports visuals.
  - Must not run numeric propagation/integration itself.
  - Mission geometry comes from `backend/environment_definition/constants/MISSION.py`; the polar target stripe is rendered as a red arc on Earth, not a point marker.
  - If additional data is needed for visuals, extend the simulation output and/or the simulation entrypoint.

## Core invariants

- One episode equals one canonical simulation rollout.
- Train/eval/render must consume the same simulation core outputs.
- `SimulationStateSeries` is the mandatory episode-level artifact.
- Rendering remains view-only.

## Model-to-render fidelity

- Rendered behavior must reflect the real modeled implementation selected for a run.
- Do not use hidden substitute logic for visualization (for example, no proxy "MPO-like" controller in render simulation).
- If a component model is defined (for example, reaction-wheel dynamics), the same model must drive both simulated system behavior and rendered outputs.

## Common commands

- Run interactive renderer (uses simulation entrypoint under the hood):
  - Use the VSCode launch config: `Sat Sim Interactive`

- Export one-pass MP4:
  - Use the VSCode launch config: `Sat Sim Export`

# autonomous-satellite-control-eth-sem-proj

## Documentation

- Project charter: `docs/project-charter.md`
- Render module API: `docs/render-api.md`
- User manual (controllers + rendering): `docs/user-manual.md`

## Semester Project Simplifications

- Start with a simplified physics setup to validate the pipeline quickly.
- Model Earth as a perfect sphere.
- Model clouds as opaque, non-see-through blocks/segments.
- Start from a realistic control boundary where the model outputs a target orientation vector and the OBC executes control.
- Keep direct low-level actuator control by the neural network as an optional later extension.