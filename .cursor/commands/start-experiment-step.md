# Start experiment step

Read and follow **`.cursor/skills/experiment-knowledge-pipeline/SKILL.md`** — **start phase** workflow.

## Steps

1. Read [`docs/experiments/pipeline/README.md`](../../docs/experiments/pipeline/README.md) and target `docs/experiments/pipeline/*/{NN}-{slug}.md` (`current_phase`).
2. Confirm doc bin matches `current_phase` (reference.md § Bin resolver).
3. If `current_phase` is **2**: `pipeline_run_guard.check_pipeline_run_clear(slug)` — abort if blocked; offer `long-run-watch`.
4. Run phase checklist and **child skills** from [`skill-chain.md`](../../.cursor/skills/experiment-knowledge-pipeline/skill-chain.md).
5. Delegate to child skill for this phase (see skill § Phase → child skill map).
6. Set `phases."N".status: in_progress` in frontmatter.

Do **not** append the phase block here — use `/document-experiment-step` when ready to write.

Do **not** advance `current_phase` — use `/close-experiment-step`.

Do not commit unless asked.
