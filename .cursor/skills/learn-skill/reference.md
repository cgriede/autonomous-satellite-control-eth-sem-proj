# Learn-skill reference

## Context priority (same as SKILL.md)

1. **Search match** — user named a topic/mistake with `/learn-skill`
2. **Three latest messages** — bare `/learn-skill`
3. **`learnings.md`** — `Status: pending`
4. **`backlog.md`** session notes — optional

## Applicability rubric

Ask for each skill/rule:

1. **Could this learning change agent behavior** if the user invokes that skill or hits that rule in the same situation?
2. **Does the skill mention** the same artifact, command, or workflow (backlog, notebook, sim, render, conda, tests, plans)?
3. If yes to either → **UPDATE** or **POINTER**, not silent N/A.

When in doubt, **POINTER** at minimum: `See [learn-skill](../learn-skill/SKILL.md) and learnings.md entry \`short-id\`.`

## Project skills (re-scan on each run)

| Skill | Typical learning domains |
|-------|---------------------------|
| `architecture-planning` | boundaries, APIs, vertical slices |
| `bulk-change-triage-commit` | git hygiene, unrelated WIP |
| `debug-workflow` | probes, logs, root-cause loop |
| `hypothesis-experiment-cycle` | experiment harness, promotion |
| `experiment-knowledge-pipeline` | phases 0–4, closeout before promote, **atomic one-hypothesis-per-slug**, Nike vs plan implement gate |
| `long-run-watch` | overnight monitoring, **charter scope audit at closeout**, **visual artifact gap audit** |
| `implementation-discipline` | scope, constants, terminology |
| `isolated-notebook-hypotheses` | notebook-only logic, reload |
| `learn-skill` | meta — record format, sweep completeness |
| `minimal-feature-cycle` | backlog uid, plan, promote, gates |
| `minimal-feature-review` | cleanup, commits, **human confirm before ship** |
| `new-skill-integration` | rules vs skills overlap; check before duplicate skill |
| `notebook-hparam-sweep` | notebook experiments |
| `performance-optimization` | profiling, bottlenecks |
| `pm-backlog-review` | backlog.xlsx, preflight, row updates |
| `review-experiment-build` | fork review gate, stage-runner wiring, ML pitfalls |
| `pm-briefing` | backlog.xlsx, sprint readout |
| `python-runtime-environment` | conda ASC, PYTHONPATH |
| `targeted-cleanup-pass` | focused refactors |
| `visual-output-verification` | MP4/plot human gates |

Re-scan the glob on each run; add new skills to this table when they appear.

## Always-applied rules (re-scan on each run)

| Rule | Typical learning domains |
|------|---------------------------|
| `units.mdc` | pint, physical quantities |
| `simulation-single-source-of-truth.mdc` | duplicate sim paths |
| `render-is-view-only.mdc` | sim in render |
| `math-physics-technical-docs.mdc` | presentation doc updates |
| `python-runtime-environment.mdc` | ASC env |

## Canonical example (backlog-xlsx-preflight)

Learning `backlog-xlsx-preflight` in `learnings.md` — anti-pattern: silent `backlog.md` fallback when xlsx workflow exists.

| Surface | Verdict | Note |
|---------|---------|------|
| pm-briefing | UPDATE | Mandatory preflight + forbidden backlog.md |
| pm-backlog-review | UPDATE | Source-of-truth table + missing workbook ask |
| minimal-feature-cycle | UPDATE | Phase 1 preflight; Phase 5 status=done |
| learn-skill | UPDATE | Step 0: ask user vs project location; glob both trees before duplicate skill |
| new-skill-integration | UPDATE | Phase 1: ask location, then pre-create glob |
| minimal-feature-review | POINTER | learn-skill + pm-backlog-review after review |
| debug-workflow | N/A | No backlog surface |
| render-is-view-only | N/A | No backlog surface |
