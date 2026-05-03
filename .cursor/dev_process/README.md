# Dev Process Hub

This directory is the project-local process library for AI-assisted development.

## Purpose

- Keep reusable process documentation and rule templates for the workflow style used in this repository.
- Keep project-specific examples under `examples/`.
- Keep reusable process rule sources under `rules/`.

## Runtime Enforcement

- Active Cursor runtime rules live in `.cursor/rules/`.
- Matching copies of selected rules are intentionally maintained in `.cursor/dev_process/rules/` as the process-library source set for this project.
- If one copy is changed, update the other copy in the same change.

## 4-Step Workflow Focus

- Shared understanding first ("grill me" style clarification before coding).
- Ubiquitous language in prompts, code, and discussions.
- Strict TDD with small verifiable vertical slices.
- AI-friendly architecture with deep modules and feature-slice ownership.
