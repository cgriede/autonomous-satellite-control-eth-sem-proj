---
name: build-tool
description: >-
  Author and use reusable Python CLIs under .cursor/tools/ for agent–user
  workflows (presentations, backlog xlsx, external apps). Use when iterating
  on PowerPoint decks, editing backlog rows, wrapping Office/filesystem actions,
  or whenever re-implementing the same script each chat would be inefficient.
  Do not put these tools in backend/ app logic.
---

# Build Tool (agent CLIs)

## Rule

**Agent interaction tools live in `.cursor/tools/` — not in `backend/` or other app runtime packages.**

Re-implementing Python for every chat action (add one backlog row, update one slide, export one diagram) is inefficient. Build a small CLI once; skills point agents at it forever.

| Layer | Location | Examples |
|-------|----------|----------|
| **Agent tools** | `.cursor/tools/<name>/` | `backlog_xlsx.py`, `presentation_pptx.py` |
| **Skills** | `.cursor/skills/<workflow>/` | `pm-backlog-review`, `build-tool` |
| **User artifacts** | `docs/`, repo root | `backlog.xlsx`, `slides_manifest.json` |
| **App / sim / ML** | `backend/` | `run_simulation`, `MPOAgent`, training |

**Forbidden:** New presentation/backlog/Excel/Office helpers under `backend/scripts/` unless they are true production runtime (they are not for agent iteration).

`backend/scripts/backlog_xlsx.py` is a **compatibility shim** only (tests + old paths). Canonical code: `.cursor/tools/backlog/`.

## When to use this skill

- User wants **PowerPoint** (or similar) iteration with Q&A → search repo → patch slides.
- User wants **backlog / workbook / CSV / JSON manifest** CRUD without manual Excel each time.
- User wants to **wrap an external app** (ffmpeg, opencv extract, pandoc) for repeatable agent use.
- You are about to run the **same multi-step Python** in chat for the third time — stop and extend a tool instead.

## Tool layout

```
.cursor/tools/
├── README.md
├── backlog/
│   └── backlog_xlsx.py      # check | list | init
├── presentation/
│   ├── presentation_pptx.py # check | list | set | append | diagrams | build
│   ├── presentation_diagrams.py
│   └── presentation_seed_final_review.py
└── video_frame_inspect/
    └── extract_frames.py
```

Each tool folder gets a short **README.md** with conda env, commands, and artifact paths.

## Authoring checklist (new tool)

1. **Create** `.cursor/tools/<slug>/` + `README.md`.
2. **CLI contract:** `check` (validate), `list` (read), mutators (`set`, `append`, `build`, …). Idempotent where possible.
3. **Paths:** Resolve repo root via `Path(__file__).resolve().parents[3]` from `.cursor/tools/<slug>/`. No `backend/ENV` unless the tool truly needs app imports (avoid).
4. **Deps:** Use packages already in `auto-sat` / `requirements.txt`; ask before new `pip install`.
5. **Skill:** Add or extend a workflow skill (e.g. `pm-backlog-review`) with preflight + commands — not chat-only instructions.
6. **Do not** duplicate logic in `backend/` — shim re-export only if tests or legacy paths require it.

## Runtime

```powershell
conda activate auto-sat
# No PYTHONPATH needed for .cursor/tools (self-contained)
python .cursor/tools/backlog/backlog_xlsx.py check
python .cursor/tools/presentation/presentation_pptx.py list
```

## Catalog (this repo)

| Tool | Skill / use | Artifact |
|------|-------------|----------|
| [backlog](../../tools/backlog/) | [pm-backlog-review](../pm-backlog-review/SKILL.md) | `backlog.xlsx` |
| [presentation](../../tools/presentation/) | [create-update-presentation](../create-update-presentation/SKILL.md) | `docs/presentation/final/with-cursor/` |
| [video_frame_inspect](../../tools/video_frame_inspect/) | [video-frame-inspect](../video-frame-inspect/SKILL.md) | `.cursor/video_frame_inspect/data/` |

Detail: [reference.md](reference.md)

## Presentation iteration

Use [create-update-presentation](../create-update-presentation/SKILL.md) — not ad-hoc steps here.

## Related

- New skill sweep: [new-skill-integration](../new-skill-integration/SKILL.md)
- Python env: [python-runtime-environment](../python-runtime-environment/SKILL.md)
