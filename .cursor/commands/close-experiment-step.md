# Close experiment step

Advance pipeline **phase** and move bin. Requires phase block already appended via `/document-experiment-step`.

Read **`.cursor/skills/experiment-knowledge-pipeline/SKILL.md`** — **close phase** workflow.

## Steps

1. Locate `docs/experiments/pipeline/*/{NN}-{slug}.md`; read `current_phase` = **N**.
2. Verify `## Phase N` exists with all mandatory subsections (reference.md).
3. Set `phases."N".status: done` and `completed_utc` in frontmatter.
4. Advance `current_phase` to **N+1** (stay at **4** when experiment fully closed).
5. **Move to correct bin** per reference.md § Bin resolver.
6. Update [`docs/experiments/pipeline/README.md`](../../docs/experiments/pipeline/README.md) (Doc path, Phase, Verdict).
7. Grep repo; fix stale pipeline paths.
8. **Phase 2 close:** clear `run_lock_holder`.
9. **Phase 3 close:** set `overall_verdict` in frontmatter.
10. **Phase 4 close:** run [`document-research`](../../.cursor/skills/document-research/SKILL.md) if not already done.

Do not commit unless asked.
