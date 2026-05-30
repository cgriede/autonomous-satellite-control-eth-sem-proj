---
name: python-runtime-environment
description: Run Python tooling in the configured conda environment and resolve environment ambiguity before execution. Use before running python, pip, pytest, notebooks, or other Python commands in this repository.
---

# Python Runtime Environment

## Rule

Activate the configured project conda environment before any Python command.

## Default behavior

- Repository default: `conda activate ASC`
- Run `python`, `pip`, `pytest`, notebooks, and similar tooling only after activation.
- Reuse the same activated environment within the shell session unless the user asks to switch.

## When the default is not enough

- If the user explicitly names an environment for the current task, use the user's choice.
- If the default environment is unavailable, inspect `conda env list`.
- If more than one plausible environment exists, ask the user which one is the project environment before running Python commands.
- Do not silently assume an unrelated environment name.

## Goal

Python execution should be reproducible and tied to the environment the project or user selected, not whichever interpreter happens to be active.
