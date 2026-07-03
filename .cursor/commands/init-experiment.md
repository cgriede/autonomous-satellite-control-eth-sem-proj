# Init experiment

Allocate a new pipeline experiment doc (title + frontmatter only).

Read **`.cursor/skills/experiment-knowledge-pipeline/SKILL.md`** and [`reference.md`](../../.cursor/skills/experiment-knowledge-pipeline/reference.md) § Init new experiment.

## Steps

0. **Atomic scope check:** If the user describes two independent experiment directions (e.g. cadence + hyperparams, two unrelated arm matrices), use **AskQuestion** — default **two** `/init-experiment` calls (two slugs). Do not create one mixed charter unless the user explicitly chooses a single sequential slug with overnight coverage for every track (see learnings.md `atomic-one-hypothesis-per-pipeline-slug`).
1. Read [`docs/experiments/pipeline/README.md`](../../docs/experiments/pipeline/README.md) for next `NN`, gating (`blocked_by`), and slug.
2. Create `docs/experiments/pipeline/0-initialized/{NN}-{kebab-slug}.md`:
   - Frontmatter: `current_phase: 0`, all `phases."0"`…`"4"` `status: pending`
   - Body: `# Exp N — Title (\`slug\`)` + one-line placeholder only
   - **Do not** add `## Phase` blocks
3. Add README row (`Phase` = 0, `Verdict` = pending, `Doc` = `0-initialized/{NN}-{slug}.md`).
4. Scaffold `backend/scripts/experiments/<slug>/` only if user asked — otherwise Phase 0 doc work only.

Phase 0 content comes later via `/document-experiment-step`.

Do not commit unless asked.
