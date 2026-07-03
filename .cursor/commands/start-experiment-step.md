# Start experiment step

Read and follow **`.cursor/skills/experiment-knowledge-pipeline/SKILL.md`** — **start phase** workflow.

## Steps

1. Read [`docs/experiments/pipeline/README.md`](../../docs/experiments/pipeline/README.md) and target `docs/experiments/pipeline/*/{NN}-{slug}.md` (`current_phase`).
2. Run `python .cursor/tools/pipeline/pipeline_doc.py check` — if mismatches, `sync-bin --slug <slug>` before work.
3. Confirm doc bin matches `current_phase` (reference.md § Bin resolver).
3. If `current_phase` is **2**: `pipeline_run_guard.check_pipeline_run_clear(slug)` — abort if blocked; offer `long-run-watch`.
4. Run phase checklist and **child skills** from [`skill-chain.md`](../../.cursor/skills/experiment-knowledge-pipeline/skill-chain.md).
5. **Phase 0 only:** Run atomic scope gate — if 0.1 has two independent tracks, **AskQuestion** to split into two slugs before documenting scope (see learnings.md `atomic-one-hypothesis-per-pipeline-slug`).
6. **Phase 1 only:** Run implement gate (Nike vs plan) per [`SKILL.md`](../../.cursor/skills/experiment-knowledge-pipeline/SKILL.md) § Implement mode — Nike → notify + justify before coding; plan or upstream bug → ask user first.
7. Delegate to child skill for this phase (see skill § Phase → child skill map).
8. Set `phases."N".status: in_progress` in frontmatter.

Do **not** append the phase block here — use `/document-experiment-step` when ready to write.

Do **not** advance `current_phase` — use `/close-experiment-step`.

Do not commit unless asked.
