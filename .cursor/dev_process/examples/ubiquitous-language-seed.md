# Ubiquitous Language Seed

Starter glossary for prompts, commits, PRs, code, and tests. Extend with the naming discipline in [.cursor/skills/implementation-discipline/SKILL.md](../../skills/implementation-discipline/SKILL.md).

## Core Terms

- **`Episode`** — One canonical simulation rollout from start to termination/truncation; not a parallel re-run invented for visualization or export.
- **`SimulationStateSeries`** — Episode-level canonical trajectory and sensor payloads produced by simulation; consumed by train/eval/render for full-episode tooling.
- **`SimulationTimestepState`** — Frozen snapshot for a single simulation index inside a rollout (subset of quantities exposed for stepping control or diagnostics).
- **`SimulationStepper` / canonical simulation runtime`** — The code path that advances time, updates dynamics/camera payloads, and attaches per-step rewards in simulation ownership (`backend/simulation/`).
- **`Train / Eval / Render`** — Pipeline modes that must rely on the same simulation outputs whenever they represent the same modeled episode.

## Boundary Terms

- **`Render`** — View-only framing, panels, codecs, overlays. Reads `SimulationStateSeries` or equivalent precomputed payloads; must not substitute hidden simulation physics.
- **`Mission-level control`** — Target architecture north star (planner autopilot → OBC/low-level tracking). Distinct from interim torque-learning experiments.
- **`Controller` / policy input bundle`** — The numeric or structured inputs fed to learned or baseline controllers after **feature selection** from timestep or series fields (explicit key lists, no magic globals).

## Sensing And Reward Terms (Current Codebase Orientation)

- **`RewardSignals`** (`backend/autonomous_control/reward.py`) — Typed bundle passed into `compute_reward`; combinational logic stays here while **who fills distance/visibility** should stay aligned with charter (simulation for canonical rollout).
- **`RewardKernel`** (`backend/simulation/reward_kernel.py`) — Simulation-side adapter that derives inputs for `RewardSignals` from geometry and observation-line codes during rollout.
- **Observation-line codes / target codes** — Discrete camera footprint classification along the modeled sensor line (see simulation/camera conventions and constants such as observation target markers).

## Usage Rules

- Reuse terms above verbatim in new symbols and tests when they match the concept.
- If you need a synonym, resolve it once: either adopt an existing charter term or add a **New term** block below—then delete the synonym from active vocabulary.
- When a term spans simulation and UI, declare which layer **owns** the computation (simulation vs render-only derivation for labels).

## New Term Entry Template

```markdown
### `Term`

- Definition (one sentence):
- Owned by layer (simulation / render / autonomous_control / env): 
- Forbidden uses (anti-patterns):
- Example symbols or files:

```
