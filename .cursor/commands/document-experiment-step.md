# Document experiment step

**Append only** the current phase block to the pipeline experiment doc.

Read **`.cursor/skills/experiment-knowledge-pipeline/SKILL.md`** — **document phase** workflow and [`reference.md`](../../.cursor/skills/experiment-knowledge-pipeline/reference.md) § Mandatory subsections.

## Steps

1. Locate `docs/experiments/pipeline/*/{NN}-{slug}.md`; read `current_phase` = **N**.
2. Confirm `## Phase N` is **not** already present (do not overwrite).
3. **Append** (at end of file) per [`reference.md`](../../.cursor/skills/experiment-knowledge-pipeline/reference.md).
4. Run any child skills listed in [`skill-chain.md`](../../.cursor/skills/experiment-knowledge-pipeline/skill-chain.md) for phase N **before** writing (e.g. analysis card before Phase 3; video-frame-inspect before Phase 3/4 video claims).
5. Fill content from session work, plan, code, or runs — **only** for this phase.
6. Set `phases."N".documented_utc` in frontmatter; keep `status: in_progress` until `/close-experiment-step`.
7. Where relevant, add **Follow-up experiment** under 0.3, 3.3, or 4.2 if inconclusive.

## Rules

- **Never** edit or delete prior `## Phase 0` … `## Phase N-1` blocks.
- **Never** append more than one phase per invocation.
- **Never** pre-fill future phases.

Do not advance `current_phase` or move bins — that is `/close-experiment-step`.

Do not commit unless asked.
