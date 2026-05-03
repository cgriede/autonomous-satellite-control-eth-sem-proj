# 01 - Drill / Shared Understanding

Use this drill before writing code. Goal: remove ambiguity, lock scope, and protect architecture invariants.

## Starter Prompt (Copy/Paste)

```text
I want to implement: <one-sentence behavior change>.

Context:
- User-visible outcome: <what should be different>
- In-scope files/modules: <paths>
- Out-of-scope files/modules: <paths>
- Constraints: <performance, timeline, compatibility, etc.>

Repository invariants to preserve:
- one episode = one canonical simulation rollout
- train/eval/render consume the same simulation outputs
- simulation owns physics/camera/reward-signal computation
- render is view-only (no integration/alternate simulation path)
- SimulationStateSeries is the episode-level artifact contract
- physical quantities remain pint-consistent where applicable

Please grill this request:
1) Ask focused clarifying questions until implementation is safe.
2) Produce explicit assumptions + risks.
3) Define smallest testable vertical slice and acceptance checks.
4) Block implementation if any invariant would be violated.
```

## Clarifying Questions

1. What exact behavior changes for the user/operator after this work?
2. What is the smallest vertical slice that proves the behavior?
3. Which module owns this behavior (`simulation`, `autonomous_control`, `render`, `environment_definition`)?
4. Does this change alter episode semantics in any way?
5. Will canonical rollout ownership remain in simulation?
6. Do train/eval/render consume the same simulation outputs after this change?
7. Is any reward-critical signal being computed outside simulation?
8. Does render remain a pure consumer of canonical artifacts?
9. Does this require extending `SimulationStateSeries`?
10. If yes, which consumers must be updated together?
11. Which physical quantities are introduced/changed and what are their units?
12. Are conversions explicit and dimensionally valid?
13. What failure behavior is required for invalid or missing inputs?
14. What failing test will be written first?
15. What deterministic verification is required?
16. What are explicit non-goals for this slice?
17. What compatibility constraints matter?
18. What runtime/performance budget must be preserved?

## Implementation Gate Checklist

- [ ] Requested outcome is one sentence and measurable.
- [ ] In-scope and out-of-scope paths are explicit.
- [ ] Ownership is clear (simulation vs render vs control).
- [ ] No unresolved invariant conflict remains.
- [ ] `SimulationStateSeries` impact is identified.
- [ ] Unit expectations are explicit for changed quantities.
- [ ] First failing verification step is defined.
- [ ] Edge-case and failure behavior is agreed.
- [ ] Assumptions and risks are written and accepted.

## Acceptance Criteria Checklist

- [ ] Behavior matches requested outcome in agreed scenario.
- [ ] Episode semantics remain canonical.
- [ ] Train/eval/render remain on shared outputs.
- [ ] Simulation remains owner of physics/camera/reward signals.
- [ ] Render remains view-only.
- [ ] `SimulationStateSeries` contract remains intact (or intentionally extended).
- [ ] Pint unit consistency is preserved.
- [ ] New/updated tests pass for the slice.
- [ ] No unrelated behavior changed.

## Non-Goals Checklist

- [ ] No shadow/parallel simulation for render/export/tooling.
- [ ] No reward-critical computation moved into render.
- [ ] No hidden mode remapping that changes behavior silently.
- [ ] No broad refactor outside agreed slice.
- [ ] No undocumented constant/unit changes.
- [ ] No ad-hoc replacement for `SimulationStateSeries`.
