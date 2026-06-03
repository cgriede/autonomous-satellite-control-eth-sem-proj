---
name: bulk-change-triage-commit
description: Triage a large git working tree by deciding per file if it needs human review (y) or can be bundled (n), then commit. Use when the user has many uncommitted changes and says "commit them", "triage these changes", or similar.
disable-model-invocation: true
---

# Bulk Change Triage & Commit

## Triage

For each file in `git status`, output `filename: y/n`.

- **n** (bundle): configs, docs, `__init__.py`, deleted files, notebooks, scripts, tests accompanying a logic change
- **y** (review): API routes, DB services, trading/financial logic, core extraction/pipeline modules

Group by bucket and summarize: "X can bundle, Y need review."

## Commit

Only after the user confirms triage and asks to commit. Do not commit because tests passed or the agent regenerated artefacts — see learnings.md `human-confirm-before-review-ship` and [minimal-feature-review](../minimal-feature-review/SKILL.md) Phase 5.

PowerShell — use `$msg = @"..."@`, not bash heredoc:

```powershell
$msg = @"
refactor: <summary>

- bullet 1
"@
git add -A ; git commit -v -m $msg
```
