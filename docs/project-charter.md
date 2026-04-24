# Project Charter: Autonomous Satellite Control

## Mission

Build a mission-oriented autonomous satellite control stack that maximizes observation value under realistic constraints, starting from a fast 2D simulation and evolving toward 3D operations, area targets, and real-world imagery.

Near-term optimization focus:
- Mission science yield (target/area observation value and image usefulness).
- Pointing and timing performance during overflight.

## North-Star Architecture

The declared long-term target is a hierarchical control architecture:
- High-level mission planner/autopilot decides observation intent and maneuver goals.
- On-board low-level control (OBC domain) executes actuator-level stabilization and tracking.

Current direct torque-learning setup is an interim experimental interface for rapid development and dynamics learning, not the final system architecture.

## Scope (Current Phase)

In scope:
- Single-satellite 2D overflight simulation.
- Cloud-aware sensing and reward feedback.
- RL and baseline controller experimentation with reproducible run artifacts.

Out of scope:
- Real flight hardware integration.
- Multi-satellite coordination/planning.

## Architecture Invariants (Must Hold)

1. Episode semantic invariant:
   - One episode equals one canonical simulation rollout.
   - For the current mission profile, that rollout is one overflight window (with a pre-maneuver segment).

2. Pipeline invariant:
   - Train, eval, and render must consume the same simulation core outputs.

3. Ownership invariant:
   - Simulation owns physics, camera/cloud sensing, and reward signal computation.
   - Rendering is view-only and may only consume simulation outputs.

4. Artifact invariant:
   - `SimulationStateSeries` is the required episode-level artifact.

5. Scope invariant:
   - Hierarchical mission-control is the primary architectural target.
   - Direct low-level torque learning remains an interim interface.

## Reward Authority

Canonical reward behavior is the current implementation in code.

The semester-project PDF remains design context, but code is the runtime source of truth. Any intentional differences between the PDF and runtime implementation must be documented explicitly. Current known intentional difference: energy-related terms are implemented and controlled by flags.

## Success Criteria for Upcoming Refactor Phase

- Single canonical simulation pipeline for train/eval/render.
- No duplicated simulation/export logic across scripts.
- Clear API boundaries that enforce simulation ownership and render view-only behavior.

## Refactor TODOs (Next Phase)

1. Episode semantic invariant (`one episode = one canonical simulation rollout`)
   - Make episode execution return/use the canonical rollout artifact instead of parallel episode-only state paths.
   - Ensure overflight window definition (including pre-maneuver segment) is shared between train and eval.

2. Pipeline invariant (`train/eval/render share same simulation core outputs`)
   - Remove script-local duplicate simulation/export logic.
   - Replace subprocess-style reruns with direct reuse of canonical outputs.

3. Ownership invariant (`simulation computes physics/camera/reward; render visualizes`)
   - Keep all reward-critical sensing and world-state computation in simulation modules.
   - Restrict render modules to consumption, panel updates, and export encoding only.

4. Artifact invariant (`SimulationStateSeries` mandatory for episode-level runs`)
   - Define and enforce API contracts so episode-level runs expose `SimulationStateSeries`.
   - Update training/evaluation runtime interfaces to propagate this artifact cleanly.

5. Scope invariant (hierarchical mission-control north star)
   - Document low-level wheel-torque control as interim experimental interface in train/eval codepaths.
   - Add extension hooks/interfaces that support future migration toward mission-planner-over-OBC architecture.
