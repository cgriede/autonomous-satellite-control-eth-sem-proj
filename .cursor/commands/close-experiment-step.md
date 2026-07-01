# Close experiment step

Advance pipeline **phase** and move bin. Requires phase block already appended via `/document-experiment-step`.

**Agent default:** Run this workflow **proactively** after run evaluation or operator verdict in chat — not only when the user types `/close-experiment-step` (see learnings.md `pipeline-advance-after-run-evaluation`).

Read **`.cursor/skills/experiment-knowledge-pipeline/SKILL.md`** — **close phase** workflow.

## Steps

1. Locate `docs/experiments/pipeline/*/{NN}-{slug}.md`; read `current_phase` = **N**.
2. Verify `## Phase N` exists with all mandatory subsections (reference.md).
3. Set `phases."N".status: done` and `completed_utc` in frontmatter.
4. Advance `current_phase` to **N+1** (stay at **4** when experiment fully closed).
5. **Move to correct bin** — run the tool (do not move by hand):

```powershell
conda activate auto-sat
python .cursor/tools/pipeline/pipeline_doc.py close-phase --slug <experiment-slug>
```

Or after manual frontmatter edits only: `sync-bin --slug <experiment-slug>`.

6. Update [`docs/experiments/pipeline/README.md`](../../docs/experiments/pipeline/README.md) (Phase, Verdict) — tool updates **Doc** column; you still set Phase/Verdict.
7. Grep repo; fix any remaining stale pipeline paths the tool missed.
8. **Phase 2 close:** clear `run_lock_holder`.
9. **Phase 3 close:** set `overall_verdict` in frontmatter.
10. **Phase 4 close:** run [`document-research`](../../.cursor/skills/document-research/SKILL.md) if not already done.

Do not commit unless asked.
