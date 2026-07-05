# Create / update presentation

Read and follow [`.cursor/skills/create-update-presentation/SKILL.md`](../skills/create-update-presentation/SKILL.md).

Use the presentation tools to read the current deck (`slides_manifest.json`), research the repo for what the user asked to improve, patch slides via CLI, and rebuild `.pptx`.

**Manifest:** `docs/presentation/final/with-cursor/` · **READ layout:** `docs/presentation/READ_Final_presentation.pptx` · **WRITE output:** `docs/presentation/WRITE_Final_presentation.pptx`

```powershell
conda activate auto-sat
python .cursor/tools/presentation/presentation_pptx.py check
python .cursor/tools/presentation/presentation_pptx.py list
```

Then apply user-guided updates → `set` / `append` → `build`.

Do not commit unless asked.
