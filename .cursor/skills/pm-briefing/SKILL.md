---
name: pm-briefing
description: Produce a project-manager briefing from the live backlog workbook, current git state, active plans, and remote branch context. Use when the user says "brief me", asks what was worked on recently, what is in the backlog or sprint, whether outside work or PRs need review, whether the sprint is on track, what to pick up today, or asks to separate unrelated uncommitted changes before continuing work.
disable-model-invocation: true
---

# PM Briefing

Use this when the user wants a quick PM/status readout of the repo.

## Rules

- Backlog truth comes from the live workbook, not chat or plan files.
- Git truth comes from the current tree plus recent history.
- Plans are supporting context for in-flight work.
- Do not commit or push unless the user explicitly asks.
- PowerShell on this machine uses `;`, not `&&`.

## Read in this order

### 1. Live backlog

Use `backend/scripts/backlog_xlsx.py`.

```powershell
$env:PYTHONPATH = "backend"
conda activate LRF
python -c "from ENV.PATHS import BACKLOG_XLSX; from scripts.backlog_xlsx import assert_backlog_workbook_healthy, read_backlog_entries; assert_backlog_workbook_healthy(BACKLOG_XLSX); print(len(read_backlog_entries()))"
```

Surface at least: `uid`, `Sprint`, `prio`, `Size`, `status`, `dep on`, `name`, `notes / blockers`.

### 2. Git state

```powershell
git status --short --branch
git log --since="14 days ago" --pretty=format:"%h|%ad|%an|%s" --date=short
git branch -a --sort=-committerdate
git for-each-ref --sort=-committerdate --format="%(refname:short)|%(objectname:short)|%(committerdate:short)|%(authorname)|%(subject)" refs/remotes/origin
```

If you need working-tree shape:

```powershell
git diff --name-only
git ls-files --others --exclude-standard
git diff --stat
git diff --cached --stat
```

### 3. Active plans

Scan:
- `.cursor/plans/01-building/`
- `.cursor/plans/02-debugging-in-review/`
- `.cursor/plans/00-initialized/`

Read only the plans that look active or newly captured.

### 4. PR state

If `gh` exists:

```powershell
gh pr list --limit 20 --state open
gh pr status
```

If not, say PR state is unavailable and fall back to remote branches/authors.

## Answer these questions

1. What was the latest meaningful work?
2. Are there PRs or external/incoming branches to review?
3. What is in the backlog and current sprint?
4. Are we on track, and what is the critical path?
5. What should we continue today?

Prefer 1-3 themes, not a changelog.

Call out:
- sprint items that are `wip`
- true blockers vs soft sequencing
- mismatch between active plans and backlog
- whether everything visible is self-authored

## Optional cleanup pass

If the user asks whether unrelated uncommitted changes exist:

1. Separate active-stream files from unrelated/supporting files.
2. Only commit unrelated files if the user explicitly asked.
3. Stage explicit paths only.
4. Re-read `git status` and say what remains.

Be careful with notebook-heavy WIP: untracked notebook helpers, hypotheses, or reports may still belong to the active stream.

## Related skills

- For backlog row updates or new idea capture: [pm-backlog-review](../pm-backlog-review/SKILL.md)
- For splitting off unrelated tree noise into its own commit: [minimal-feature-review](../minimal-feature-review/SKILL.md)
