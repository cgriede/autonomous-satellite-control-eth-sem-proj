# Architecture Slice Pattern (Project-Specific)

Feature slices align with [.cursor/skills/architecture-planning/SKILL.md](../../skills/architecture-planning/SKILL.md) **and** the charter invariants in [docs/project-charter.md](../../../docs/project-charter.md).

## Principles

- One vertical slice = one coherent behavior travelers can trace end-to-end.
- Prefer deep modules (`index.py`-style façade + hidden internals).
- **Simulation computes** propagated state, optics/camera payloads, reward inputs for canonical rollout.
- **Render draws** canonical series/timesteps; telemetry labels may format values but must not launder alternate physics.
- **Autonomous_control** houses policy/feature wiring and reward *combination*, not alternate world simulation.

## Where Slices Typically Live (`backend/`)

| Concern | Package | Notes |
|---|---|---|
| Canonical rollout mechanics | `backend/simulation/` | `SimulationStateSeries`, stepper/dynamics kernels, reward kernel feeding `compute_reward`.
| Observation → controller tensors | `backend/autonomous_control/` | Explicit feature selection keyed off timestep artifacts.
| Visualization | `backend/render/` | Consumption + layout only.
| Simplified RL gym surface | `backend/environment_definition/` | Document when geometry is proxy vs cinematic simulation.

Slices may start in **one folder** plus **focused tests beside or under** `backend/tests/` or feature-local tests—matching existing repo patterns.

## Suggested Slice Layout (When Adding a Named Feature Folder)

Use when a capability grows beyond a single module file.

```text
feature_name/
  __init__.py         # thin re-export of stable public symbols
  types.py            # dataclasses / protocols owned by slice
  service.py          # orchestration callable from CLI/training/etc.
  tests/
    test_feature_name.py
```

For small slices, `_service.py`-style sibling files next to callers are acceptable; promote to folder once boundaries blur.

## Anti-Patterns to Block During Review

- Introducing `"shadow simulation"` helpers under `backend/render/`.
- Recomputing episode-wide signals in scripts when `SimulationStateSeries` already carries them—or should be extended instead.
- Leaking Gym env proxies into tooling that assumes full orbital fidelity without labeling the shortcut.

## Slice Implementation Checklist

- Behavior is definable in one sentence (ties to ubiquitous language seed).
- A failing test exists before implementation merges.
- Minimal code passes locally / CI for that slice only.
- Charter invariants still hold (`SimulationStateSeries` contract untouched or improved intentionally).
- The next slice boundary is spelled out (“after this merges, slice N+1 touches X only”).

## Cross-References

- Clarify scope first: [.cursor/dev_process/examples/grill-me-prompt-template.md](grill-me-prompt-template.md).
- Naming alignment: [.cursor/dev_process/examples/ubiquitous-language-seed.md](ubiquitous-language-seed.md).
- Delivery cadence: [.cursor/dev_process/examples/tdd-vertical-slice-template.md](tdd-vertical-slice-template.md).
