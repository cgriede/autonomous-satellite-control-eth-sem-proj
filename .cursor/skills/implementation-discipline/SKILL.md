---
name: implementation-discipline
description: Clarify scope before coding, implement in small red-green-refactor slices, keep terminology aligned with the repository, and avoid scraping source files for constants. Use when implementing, refactoring, reviewing code changes, or translating a request into concrete edits.
---

# Implementation Discipline

Use this workflow for day-to-day code changes.

## 1. Clarify before editing

Before touching code, ask about:

- the requested outcome and success criteria,
- scope boundaries and non-goals,
- edge cases and failure behavior,
- dependencies and impacted areas,
- test or verification expectations.

If critical ambiguity remains, do not implement yet.

**Pipeline experiment implement (Phase 1):** Run the Nike-vs-plan gate in [`experiment-knowledge-pipeline`](../experiment-knowledge-pipeline/SKILL.md) — do not ask "need a build plan?" when Nike criteria pass; do ask the user when plan mode or upstream-bug signals fire (learnings.md `pipeline-implement-nike-vs-plan-gate`).

**Pipeline promote requests:** if the user asks to merge an experiment fork to production, confirm pipeline closeout is done (`4-documentation/`, verdict set) before editing `autonomous_control/` / `simulation/` — see learnings.md `pipeline-closeout-before-promote`.

**Pipeline charter scope:** one atomic hypothesis per slug — if Phase 0 names two independent tracks, stop and split via AskQuestion (see learnings.md `atomic-one-hypothesis-per-pipeline-slug`).

## 2. Reflect back the working understanding

State the concrete behavior you are about to change and the limits of the change. Keep the implementation aligned to that scope; avoid opportunistic refactors.

## 3. Work in the smallest verifiable slice

Follow strict red-green-refactor:

1. Add one failing test or the smallest equivalent verification for the next behavior slice.
2. Implement the minimum code needed to pass.
3. Refactor only after the slice is green.
4. Report what slice was completed and how it was verified before moving on.

Do not batch multiple behaviors into one jump.

## 4. Keep terminology stable

- Reuse repository terms when names already exist.
- If a new concept is necessary, define it once and reuse the same term everywhere.
- If near-synonyms compete, ask which term is canonical before broad edits.
- Keep production code, tests, comments, and docs on the same vocabulary.

## 5. Treat constants and config as APIs

Never scrape Python source text with regex or string parsing to recover constants or config.

Preferred order:

1. Use constants exported by this repository.
2. Use explicit exported APIs from dependencies.
3. Add a small adapter or mapping layer when dependency values need translation.
4. Ask the user for a structure decision when ownership is unclear.

Bad pattern to block:

- `read_text(...)` plus regex to extract runtime constants from implementation files.
