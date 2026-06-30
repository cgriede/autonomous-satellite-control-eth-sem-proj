# Agent tools (`.cursor/tools/`)

Reusable Python CLIs for **Cursor agent ↔ user** workflows. Not part of the satellite sim / ML app runtime.

**Skill:** [`.cursor/skills/build-tool/SKILL.md`](../skills/build-tool/SKILL.md)

| Tool | Entry script | Purpose |
|------|--------------|---------|
| `backlog/` | `backlog_xlsx.py` | Live sprint board `backlog.xlsx` |
| `presentation/` | `presentation_pptx.py` | JSON manifest → PowerPoint iteration |
| `video_frame_inspect/` | `extract_frames.py` | MP4 → PNG for agent vision |

```powershell
conda activate auto-sat
python .cursor/tools/backlog/backlog_xlsx.py list
python .cursor/tools/presentation/presentation_pptx.py build
```

Legacy shim (tests): `backend/scripts/backlog_xlsx.py` re-exports the backlog tool.
