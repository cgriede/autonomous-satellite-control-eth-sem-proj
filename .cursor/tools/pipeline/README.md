# Pipeline doc tool

Keeps `docs/experiments/pipeline/{bin}/{NN}-{slug}.md` in the folder that matches `current_phase`.

```powershell
conda activate auto-sat
python .cursor/tools/pipeline/pipeline_doc.py check
python .cursor/tools/pipeline/pipeline_doc.py sync-bin
python .cursor/tools/pipeline/pipeline_doc.py sync-bin --slug ml_sac_shutter_reward_split
python .cursor/tools/pipeline/pipeline_doc.py close-phase --slug ml_mpo_decoupled_dual_torque
```

**`/close-experiment-step`** must run `close-phase` (or `sync-bin` after manual frontmatter edits).
