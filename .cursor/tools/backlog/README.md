# Backlog workbook tool

Agent CLI for [`backlog.xlsx`](../../../backlog.xlsx) at repo root.

**Skill:** [pm-backlog-review](../../skills/pm-backlog-review/SKILL.md)

```powershell
conda activate auto-sat
python .cursor/tools/backlog/backlog_xlsx.py check
python .cursor/tools/backlog/backlog_xlsx.py list
python .cursor/tools/backlog/backlog_xlsx.py init --force   # bootstrap only
```

Compatibility: `python backend/scripts/backlog_xlsx.py` delegates here (for tests).

Routine row edits: Excel/LibreOffice or future `set-row` subcommand — not `backend/` code changes.
