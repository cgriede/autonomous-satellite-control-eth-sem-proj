# Build tool — reference

## Why separate from `backend/`

Agent workflows are **high-churn, low-production-critical**: slide wording, backlog status, frame extracts. Shipping them inside `backend/scripts/` blurs:

- CI / import boundaries (`PYTHONPATH`, `ENV`)
- Review expectations (app code vs agent ergonomics)
- Ownership (semester sim vs Cursor operator tooling)

Production training, simulation, and experiments stay in `backend/`. Operator CLIs stay in `.cursor/tools/`.

## CLI design patterns

### Preflight + mutate + validate

```
check → (read state) → mutate command → check again
```

Example: backlog row update — `list` → edit xlsx or future `set-row` → `check`.

### Manifest as source of truth

JSON/YAML beside user-facing output (`.pptx`, `.xlsx`):

| Manifest | Output |
|----------|--------|
| `slides_manifest.json` | `WRITE_Final_presentation.pptx` (layout ref: `READ_Final_presentation.pptx`) |
| `backlog.xlsx` rows | (workbook is both) |

Agent edits manifest via CLI; `build` regenerates binary formats.

### Pipe-separated bullets

`--bullets "Line one|Line two"` avoids shell JSON escaping for quick agent patches.

## Shim policy

Keep `backend/scripts/<name>.py` **only when**:

- `backend/tests/` imports `scripts.<name>`
- External docs not yet updated

Shim body: insert tool dir on `sys.path`, `from <module> import *`, delegate `main()`.

Remove shim once tests import from `.cursor/tools` directly.

## Anti-patterns

| Don't | Do instead |
|-------|------------|
| One-off 40-line Python in chat to patch xlsx | Extend `backlog_xlsx.py` or edit workbook once via tool |
| `backend/autonomous_control/presentation_export.py` | `.cursor/tools/presentation/` |
| Hardcode paths in skill only | Tool defaults + `--path` / `--manifest` overrides |
| Skip `check` after edit | Always validate before telling user "done" |

## Adding presentation decks

1. Copy seed pattern from `presentation_seed_final_review.py` or new seed module in same folder.
2. `init --force --manifest docs/presentation/<deck>/slides_manifest.json`
3. Document deck path in tool README.

## Future tools (candidates)

- `backlog_xlsx.py set-row --uid FEAT-004 --status done`
- `presentation_pptx.py pull --id M12 --query "SafetyController"` (search + append — agent implements search, tool appends)
- Generic `external_run.py` wrapper with allowlisted commands
