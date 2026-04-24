# Autonomous Satellite Control (ETH SEM Project)

## Architecture spec: simulation vs rendering

This repository separates **numeric simulation** from **rendering/visualization**.

- **Simulation** (`backend/simulation/*`)
  - Owns all numeric propagation / integration.
  - Produces typed simulation outputs such as `simulation.state_types.SimulationStateSeries`.
  - Canonical entrypoint for rendered runs: `simulation.run_simulation.run_simulation()`.

- **Rendering** (`backend/render/*`)
  - View-only: consumes simulation outputs and draws/exports visuals.
  - Must not run numeric propagation/integration itself.
  - If additional data is needed for visuals, extend the simulation output and/or the simulation entrypoint.

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

- Render module API: `docs/render-api.md`
- User manual (controllers + rendering): `docs/user-manual.md`

## Semester Project Simplifications

- Start with a simplified physics setup to validate the pipeline quickly.
- Model Earth as a perfect sphere.
- Model clouds as opaque, non-see-through blocks/segments.
- Start from a realistic control boundary where the model outputs a target orientation vector and the OBC executes control.
- Keep direct low-level actuator control by the neural network as an optional later extension.