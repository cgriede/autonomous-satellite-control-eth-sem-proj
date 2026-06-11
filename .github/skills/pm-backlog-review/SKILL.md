---
name: pm-backlog-review
description: Update the live backlog workbook after a work session, sprint review, or when the user asks to update the backlog. Use when the user says "update the backlog", "review what we did and update backlog", "close out sprint items", "add a backlog item", or after completing a minimal-feature cycle slice. Always read backlog.xlsx first — never treat backlog.md as source of truth.
---

# PM Backlog Review

Use when capturing session outcomes into the **live backlog workbook**.

## Source of truth

| File | Role |
|------|------|
| [`backlog.xlsx`](../../../backlog.xlsx) | **Live sprint board** — edit this |
| [`backlog.md`](../../../backlog.md) | Narrative archive / session notes only |
| `.cursor/plans/` | Supporting context, not the board |

**Never** update only `backlog.md` when the user asked to update the backlog.

## Preflight (mandatory)

Run before reading or editing backlog rows:

```powershell
$env:PYTHONPATH = "backend"
conda activate ASC
python backend/scripts/backlog_xlsx.py check
```

### If check fails

| Failure | Action |
|---------|--------|
| `FileNotFoundError` (workbook missing) | **Ask the user** where the backlog `.xlsx` should live. Default in this repo: repo root `backlog.xlsx` via `ENV.PATHS.BACKLOG_XLSX`. Offer `python backend/scripts/backlog_xlsx.py init` only after they confirm path (or accept default). |
| `ModuleNotFoundError: openpyxl` | `pip install openpyxl` (already in `requirements.txt`). |
| `ModuleNotFoundError: ENV` | Workbook infra missing — see `backend/ENV/PATHS.py` and `backend/scripts/backlog_xlsx.py`. |
| User gave a **custom path** | Update `backend/ENV/PATHS.py` (`BACKLOG_XLSX`) or pass `--path` on CLI; re-run check. |

**Do not** fall back to `backlog.md`, chat memory, or plan todos as the live board without telling the user.

## Read current board

```powershell
python backend/scripts/backlog_xlsx.py list
```

Or programmatically:

```powershell
python -c "from ENV.PATHS import BACKLOG_XLSX; from scripts.backlog_xlsx import read_backlog_entries; import json; print(json.dumps(read_backlog_entries(BACKLOG_XLSX), indent=2))"
```

Columns: `uid`, `Sprint`, `prio`, `Size`, `status`, `dep on`, `name`, `notes / blockers`.

Allowed **status**: `todo`, `wip`, `done`, `blocked`, `icebox`  
Allowed **prio**: `P0`–`P3` · **Size**: `S`, `M`, `L`, `XL`

## Session update workflow

1. **Read** live rows (`list` or `read_backlog_entries`).
2. **Reconcile** git state + plans + user summary against existing `uid`s — prefer updating rows over duplicating.
3. **Edit** the workbook:
   - Set `status` (`wip` → `done` when acceptance met).
   - Refresh `notes / blockers` with concrete next step or blocker.
   - Add new rows with new `uid`s (`BUG-`, `FEAT-`, `STR-`, `DONE-` prefixes match existing convention).
4. **Validate**: `python backend/scripts/backlog_xlsx.py check`
5. **Optional narrative**: append a short dated section to `backlog.md` (session summary only — not a substitute for xlsx).

### uid conventions

- `BUG-###` — defects
- `FEAT-###` — features / notebook slices
- `STR-###` — structural / tech debt
- `DONE-###` — recently completed (or reuse original uid with `status=done`)

Keep `uid` stable; do not rename once referenced in plans or chat.

## Adding rows

Edit `backlog.xlsx` directly (Excel / LibreOffice), or extend seed in `backend/scripts/backlog_xlsx.py` only for **template/bootstrap** — not for routine session updates.

Minimum for a new row: unique `uid`, `name`, `status`. Set `Sprint`, `prio`, `Size`, `dep on` when known.

## After minimal-feature close

When a notebook slice is promoted or accepted:

1. Set matching backlog row `status=done`.
2. Update `notes / blockers` with commit/PR ref or plan path if useful.
3. Move follow-ups to new `todo`/`wip` rows instead of leaving stale notes.

## Related skills

- Status readout: [pm-briefing](../pm-briefing/SKILL.md)
- Feature delivery: [minimal-feature-cycle](../minimal-feature-cycle/SKILL.md)
- Capture process learnings: [learn-skill](../learn-skill/SKILL.md)
