# Reference — New Skill Integration

Deep dive on the rubric and patterns named in SKILL.md. Read when the high-level rule isn't enough.

## The three trees

| Tree | What it holds | Loaded by agent | Typical disposition |
|------|---------------|-----------------|---------------------|
| `.cursor/rules/` | Cursor runtime rules (`*.mdc` with frontmatter) | `alwaysApply: true` ships every session; `globs: "..."` loads only when matching files are touched | Highest-leverage target for sweeps |
| `.cursor/memory/` | Long-term domain notes, nomenclature, dev research | Loaded as memory when referenced | Usually out of scope — domain notes rarely overlap a workflow skill |
| `.cursor/dev_process/` | Project-local process library, examples, mirrored rule sources | Not automatically loaded unless mirrored into `.cursor/rules/` | Hygiene; trim or delete off-domain artefacts |

## Classification rubric

Apply per file. One verdict per file. When in doubt between TRIM and EXTRACT, EXTRACT — losing a sentence is harder to recover from than carrying one extra paragraph.

### KEEP

The skill does not cover this rule's subject. Examples:

- Frontend stack rules (Svelte, TypeScript strictness, data fetching) when the skill is backend-only.
- Backend domain conventions (database design, typed inputs, training data layout) when the skill is about a different concern.
- Planning rules (clarifying questions, backward-compatibility scale, reprompt updates) that fire across all skills.

### TRIM

The skill carries the same logic in equal or better form, but the rule still needs to exist as a runtime gate (always-applied or globbed). Collapse the body to:

- The mandate sentence (one line).
- Any enforcement-critical bullet not in the skill (e.g., a one-line N/A example).
- A pointer at the relevant skill phase.

Drop motivation paragraphs, worked examples, and bulleted restatements of what the skill says.

### EXTRACT

The rule carries one or more sentences the skill does not have. Before deletion:

1. Quote the sentences verbatim into the skill's `reference.md` (usually the right home for detail) — or into a surviving rule when the content is about cross-skill concerns (plan lifecycle, debug logging convention, etc.).
2. Reconcile path or terminology differences. The new skill is canonical; align the rest. If the new skill is wrong, fix the skill — do not keep the stale rule.
3. Re-read the new home and confirm the sentence reads cleanly.

Only then proceed to DELETE.

### DELETE

The rule is fully redundant with the skill or is an off-domain template superseded by it. Examples seen in past sweeps:

- A 4-step TDD walkthrough pack referencing modules that do not exist in this repo.
- A stale rule whose path convention contradicts the new skill's canonical path.
- An empty README index whose entire content is "see the examples below" (and the examples themselves are also being deleted).

## Always-applied priority

Look at frontmatter to spot the lever:

```yaml
---
description: ...
alwaysApply: true   # loaded every session — HIGH leverage
---
```

vs.

```yaml
---
description: ...
globs: "**/*.ipynb"  # loaded only when an .ipynb file is open — LOW leverage
alwaysApply: false
---
```

Trimming one always-applied rule from ~25 lines to ~6 lines saves more cumulative agent context over a week than deleting 10 globbed examples.

Aggressive-mode option: demote an always-applied rule to globbed by removing `alwaysApply: true` and adding a `globs:` pattern. Only do this if the user picked the aggressive approach and the rule's intent maps cleanly to a file pattern.

## Survey delegation

For ≥20 files across the chosen trees, delegate the survey to an `explore` subagent (readonly). Prompt the subagent to:

1. Read the new skill's `SKILL.md`, `reference.md`, and `examples.md` first.
2. Walk each chosen tree and classify every file.
3. Order output DELETE → EXTRACT → TRIM → KEEP, then by tree.
4. List the residual always-applied set at the end.

For ≤20 files, do the survey inline — the parallel subagent overhead is not worth it.

## Extraction patterns

### Path canonicalisation

Two files name different canonical paths for the same artefact (debug logs, helper modules, fixture directories). The new skill is canonical. Update the surviving rule to match before deleting the stale one. Add a one-line note in the skill's `reference.md` if the convention is non-obvious.

### Cross-rule references

A rule body cites a sibling rule by relative path. After trimming, verify the cite still resolves. After deleting, verify nothing else cites the deleted file (`rg` for the filename across the workspace).

### Skill self-references

The new skill's own `SKILL.md` or `reference.md` may cite a rule that you are about to delete. Update those cites before deletion. The `rg` sweep in Phase 6 catches this if you miss it during edits.

## Anti-patterns

- **Deleting before extracting.** A rule's one unique sentence is invisible in a green grep and surfaces only when an agent later asks for it. Always extract first.
- **Trimming with no enforcement left.** A trimmed rule that contains only "see the skill" is worse than no rule — it occupies a slot in always-applied context without contributing a gate. Keep the mandate sentence in the trimmed body.
- **Conflating always-applied and globbed.** They have different runtime weight. A globbed `**/*.ipynb` rule is "free" most of the time; an always-applied rule ships every session.
- **Treating off-domain templates as TRIM.** A template that references modules or entities that do not exist in this repo is not salvageable by trimming. DELETE it and note the deviation.
- **Mirror drift.** `.cursor/dev_process/rules/` holds mirrors of select `.cursor/rules/` files. If you trim a rule that exists in both places, update both copies or delete one. The dev_process README documents the sync policy.

## Sweep summary template

When the sweep is done, summarise as:

```
Deleted (<N> files):
- <path> — <one-line reason>
...

Trimmed to skill pointers (<N> files):
- <path>: <before>→<after> lines, <one-line reason>
...

Untouched (out of scope):
- <count> files in <tree> — <one-line reason>

Verification:
- rg "<deleted-path-pattern>" → 0 hits
- <N> always-applied rules survive under .cursor/rules/
- skill cross-references resolved
- lint clean on edited files
```
