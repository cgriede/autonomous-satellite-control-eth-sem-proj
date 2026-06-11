---
name: pm-briefing
description: Produce a project-manager briefing from the live backlog workbook (backlog.xlsx — preflight required), current git state, active plans, and remote branch context. Use when the user says "brief me", asks what was worked on recently, what is in the backlog or sprint, whether outside work or PRs need review, whether the sprint is on track, what to pick up today, asks to update the backlog, or asks to separate unrelated uncommitted changes before continuing work.
disable-model-invocation: true
---

# PM Briefing

Use this when the user wants a quick PM/status readout of the repo.

## Rules

- Backlog truth comes from the **live workbook** ([`backlog.xlsx`](../../../backlog.xlsx)), not chat, plan files, or [`backlog.md`](../../../backlog.md).
- **Preflight the workbook before any backlog read or update** — see [Backlog preflight](#backlog-preflight-mandatory) below.
- Git truth comes from the current tree plus recent history.
- Plans are supporting context for in-flight work.
- Do not commit or push unless the user explicitly asks.
- PowerShell on this machine uses `;`, not `&&`.

## Backlog preflight (mandatory)

Before answering backlog/sprint questions or updating the board:

1. Run `python backend/scripts/backlog_xlsx.py check` (see commands below).
2. If check **passes** → read rows from `BACKLOG_XLSX` via `read_backlog_entries`.
3. If workbook **missing** → **ask the user** where the live `.xlsx` lives; do not silently use `backlog.md`. Default path: repo root `backlog.xlsx` (`backend/ENV/PATHS.py`). Offer `init` only after confirmation.
4. If user names a **different path** → update `ENV.PATHS.BACKLOG_XLSX` or use `--path`, then re-check.

**Forbidden:** treating `backlog.md` as the sprint board when an xlsx workflow exists or was requested.

## Read in this order

### 1. Live backlog

Use `backend/scripts/backlog_xlsx.py` after preflight passes.

```powershell
$env:PYTHONPATH = "backend"
conda activate ASC
python backend/scripts/backlog_xlsx.py check
python backend/scripts/backlog_xlsx.py list
python -c "from ENV.PATHS import BACKLOG_XLSX; from scripts.backlog_xlsx import read_backlog_entries; print(len(read_backlog_entries(BACKLOG_XLSX)))"
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
- After a backlog/process mistake: [learn-skill](../learn-skill/SKILL.md)
- For splitting off unrelated tree noise into its own commit: [minimal-feature-review](../minimal-feature-review/SKILL.md)
