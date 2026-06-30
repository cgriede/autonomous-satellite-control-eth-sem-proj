# Presentation (PowerPoint) tool

Manifest-driven deck iteration for agent + user Q&A.

**Skill:** [create-update-presentation](../../skills/create-update-presentation/SKILL.md) · tools: [build-tool](../../skills/build-tool/SKILL.md)

**Default deck:** `docs/presentation/final/with-cursor/`

| File | Role |
|------|------|
| `slides_manifest.json` | Source of truth (slide ids, bullets, images) |
| `work_review_with_cursor.pptx` | Built output |
| `diagrams/*.mmd` | Editable flowchart source |
| `diagrams/*.png` | Embedded images (regenerate with `diagrams`) |

```powershell
conda activate auto-sat
python .cursor/tools/presentation/presentation_pptx.py check
python .cursor/tools/presentation/presentation_pptx.py list
python .cursor/tools/presentation/presentation_pptx.py set --id M12 --bullets "Bullet A|Bullet B"
python .cursor/tools/presentation/presentation_pptx.py append --id M17 --bullets "New evidence"
python .cursor/tools/presentation/presentation_pptx.py diagrams
python .cursor/tools/presentation/presentation_pptx.py build
```

Requires `python-pptx` (in `auto-sat`).
