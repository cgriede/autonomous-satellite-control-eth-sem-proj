# Grill-Me Prompt Template (Project-Specific)

Use this in a fresh Agent conversation for new work **before** asking for implementation.

## Primary Prompt (Paste as User Message)

```text
Grill me relentlessly on this task until we have complete shared understanding.

Ask clarifying questions about:
- outcomes and measurable success criteria,
- edge cases and failure behavior,
- impacted modules (simulation vs render vs control vs env),
- test and verification expectations,
- explicit non-goals.

Do not write code until I explicitly say “Implement”.

Repository constraints to preserve:
- One episode = one canonical simulation rollout.
- Train, eval, and render consume the same simulation core outputs where episode semantics apply.
- Simulation owns physics, camera/sensing semantics, and reward-critical world signals assembled for the combiner.
- Render is view-only: consume canonical artifacts; do not run integration/propagation or alternate reward paths.
- `SimulationStateSeries` is the episode-level artifact contract for full rollouts.
- Physical quantities exposed across boundaries should stay unit-consistent with project conventions (e.g. pint where the codebase already uses it).

After we align, implement in strict TDD and small vertical slices (see `.cursor/dev_process/examples/tdd-vertical-slice-template.md`).
```

## Optional: Question Bank You Can Paste for the Agent

```text
1) What is the single sentence behavior we are changing or adding?
2) What artifact is authoritative after the change (`SimulationTimestepState` fields, `SimulationStateSeries`, env obs only)?
3) Who computes reward inputs—simulation stepper/kernel only, or is a simplified Gym env Path allowed?
4) Does render need any new telemetry? If yes, which fields must simulation produce?
5) What is intentionally out of scope for this slice?
6) What breaks if someone duplicates this logic in render or scripts?
7) What is the smallest test that proves the slice (file + assertion shape)?
```

## Follow-Up After Alignment (Starts Implementation Gate)

```text
Implement now using strict TDD:
1) Write one failing test for the smallest behavior.
2) Write minimal code to pass.
3) Refactor only if tests remain green.
4) Report what was verified before proposing the next slice.
```
