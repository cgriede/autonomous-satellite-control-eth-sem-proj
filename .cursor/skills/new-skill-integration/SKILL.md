---
name: new-skill-integration
description: Sweep .cursor/rules/, .cursor/memory/, and .cursor/dev_process/ when a new skill is added so the repo's global agent context stays lean. Identifies overlaps with the new skill, extracts unique logic before deletion, removes redundant files, and trims surviving rules to skill-pointer form. Use after authoring or installing a new skill, when reducing always-applied context, or when the user mentions "integrate this skill", "sweep rules", "reduce .cursor context", or "prune rules now that we have a skill".
---

# New Skill Integration Sweep

When a new skill lands, the rules and dev-process docs that previously carried that workflow become bloat. Sweep them so the new skill is the canonical home and the global always-applied context shrinks.

## Phase 1 — Confirm scope and aggressiveness

**Before authoring:**

1. **Ask skill location** — user (`~/.cursor/skills/`) vs project (`.cursor/skills/`) unless the user already stated (see `learnings.md` → `ask-skill-location-before-create`).
2. Glob **both** skill trees and project `.cursor/commands/` — if a matching skill or command exists, extend it instead of creating a duplicate (see `check-existing-before-create-skill`).

Ask the user two narrow scoping questions before doing any work:

1. **Scope**: which trees does the sweep cover?
   - `.cursor/rules/` only (biggest context savings)
   - `.cursor/rules/` + `.cursor/memory/`
   - All three: `.cursor/rules/` + `.cursor/memory/` + `.cursor/dev_process/`
2. **Approach** when a rule overlaps the new skill:
   - Conservative — trim to a one-liner pointing at the skill; no deletions unless 100% redundant
   - Moderate — if key logic is already in the skill, delete the rule; if extra logic exists, move it into the skill first, then delete
   - Aggressive — also demote always-applied rules to globbed/on-demand where the skill covers them

Default to AskQuestion. Do not survey before the user picks scope and approach — the answers change which files you touch.

## Phase 2 — Survey

Map every file in the chosen trees against the new skill. For each file capture: full path, type (`always-applied` / `globbed (pattern)` / `agent-requestable` / `memory-note` / `example` / `other`), approximate line count, and one verdict.

Verdicts (rubric in [reference.md](reference.md)):

| Verdict | Meaning |
|---------|---------|
| KEEP | Universal or domain-specific rule the skill does not cover |
| TRIM | Significant overlap with the skill; shrink to one-line skill pointer plus enforcement-critical bullets |
| EXTRACT | Skill is missing logic this rule carries; move sentences into the skill before deletion |
| DELETE | Fully redundant with the skill (or off-domain template superseded by it) |

For surveys covering more than ~20 files, delegate to an explore subagent rather than walking the trees inline.

Order the output DELETE → EXTRACT → TRIM → KEEP, then by tree.

## Phase 3 — Extract (preserve unique content first)

Run before any deletion. For each EXTRACT candidate:

1. Identify the specific sentences not yet in the skill.
2. Move them into the skill's `reference.md` (usually the right home for detail) or into a surviving rule (when the content is about plan files, lifecycle, or another global concern).
3. Reconcile path or terminology conflicts. The skill is canonical; surviving rules align to it. If the skill is wrong, fix the skill — do not preserve the stale rule.
4. Re-read the extraction target to confirm the sentence reads cleanly in its new home.

## Phase 4 — Delete

After Phase 3 closes:

1. Delete EXTRACT-then-DELETE files and DELETE files.
2. Remove now-empty directories.
3. Off-domain templates (mentioning entities or modules that do not exist in this repo) qualify for DELETE even if the plan says "archive or trim" — note the deviation in the summary.

## Phase 5 — Trim

For each TRIM candidate, collapse to a small file that:

- Keeps the enforcement-critical bullets only (the mandate sentence, the N/A example, a glob-scoped instruction).
- Points at the relevant skill phase with a one-line link.
- Drops the worked examples, motivation paragraphs, and any content the skill now carries.

Prioritise **always-applied rules** — they ship on every session. Globbed rules (`**/*.ipynb`, `**/*.py`) save context only when those files are touched. Library rules under `.cursor/dev_process/rules/` are hygiene, not runtime savings.

## Phase 6 — Verify

1. Grep for every deleted file's name across the workspace. Expect 0 hits.
2. Read the new skill's `SKILL.md` and `reference.md`. Update any cross-reference that names a now-deleted rule.
3. Count surviving always-applied rules under `.cursor/rules/`. Compare to the pre-sweep count from the survey.
4. Read each edited file in full. Confirm the pointer + remaining bullets are still sufficient to enforce the gate without the skill loaded.
5. Run the lint check on every edited file.

## Principles

- **Memory is usually out of scope.** `.cursor/memory/` holds long-term domain notes (nomenclature, edge-case logs). Skills rarely overlap.
- **Domain rules are usually KEEP.** Frontend stack rules, backend typing rules, database design rules, training data layouts — the skill does not touch these unless it is itself a domain skill.
- **Always-applied is the lever.** Trimming three always-applied rules saves more per-session context than deleting twenty globbed examples.
- **Never delete before extracting.** A rule's one unique sentence is easy to lose and hard to notice missing.
- **Reconcile, do not preserve.** When the skill and a rule disagree (paths, terminology), the skill wins and the rule updates — or the skill is wrong and gets fixed.

## Quick checklist

```
Sweep progress:
- [ ] Phase 1: scope + approach confirmed via AskQuestion
- [ ] Phase 2: every file in chosen trees has a verdict
- [ ] Phase 3: unique content moved into skill or surviving rule
- [ ] Phase 4: redundant files deleted; empty directories removed
- [ ] Phase 5: TRIM rules collapsed; always-applied prioritised
- [ ] Phase 6: 0 grep hits for deleted paths; cross-refs fixed; lint clean
```

## Sweep flow

```mermaid
flowchart LR
  newSkill[New skill lands] --> scope[Phase 1: scope + approach]
  scope --> survey[Phase 2: classify every file]
  survey --> extract[Phase 3: extract unique content]
  extract --> delete[Phase 4: delete redundant]
  delete --> trim[Phase 5: trim TRIM candidates]
  trim --> verify[Phase 6: grep + lint + count]
```

## Pointers

- Verdict rubric, three-tree details, anti-patterns: [reference.md](reference.md).
- The minimal-feature-cycle integration sweep as a worked example: [examples.md](examples.md). Read on request.
