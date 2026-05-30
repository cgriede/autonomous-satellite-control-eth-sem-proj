---
name: architecture-planning
description: Plan and structure changes as testable vertical slices with explicit boundaries and small stable APIs. Use when the user asks for a plan, when shaping new modules or folders, when splitting code, or when deciding whether to extend existing code versus create something new.
---

# Architecture Planning

Use this skill when the task needs design choices before implementation.

## 1. Start with questions

Ask at least three clarifying questions before proposing a plan or implementation approach.

Cover:

- desired outcome and acceptance criteria,
- in-scope versus out-of-scope work,
- affected files or subsystems,
- testability and human review expectations,
- backward-compatibility constraints.

## 2. Update the active plan instead of restarting it

While still planning, treat new user comments as requests to revise the current plan unless the user explicitly changes direction.

## 3. Prefer vertical slices

- Organize around one coherent behavior at a time.
- Co-locate types, tests, domain logic, and interfaces near the feature they support.
- Keep boundaries explicit and avoid broad utility dumping grounds.
- Favor deep modules: a small public surface hiding internal complexity.
- Split oversized files once responsibility boundaries stop being obvious.

## 4. Ask when structure is unclear

Do not guess about structure decisions that materially affect the repo:

- ask whether to extend existing code or create something new,
- ask where new files or directories should live when the answer is not obvious,
- ask before changing a boundary that may affect other workflows.

## 5. Keep the plan inspectable

A good plan should produce code that is easy for a human to read and easy to verify in small steps.

Preserve project-specific architectural invariants enforced elsewhere in the repo. Do not use planning to smuggle in alternate ownership boundaries or duplicate execution paths.
