# Create / update presentation — reference

## Manifest slide fields

| Field | Required | Purpose |
|-------|----------|---------|
| `id` | yes | Stable key (`M12`, `B04`) |
| `section` | yes | `main` \| `admin` \| `backup` |
| `title` | yes | Slide title (without id prefix in manifest; CLI adds id in pptx) |
| `bullets` | yes | List of strings; one bullet per line in deck |
| `status` | yes | `draft` \| `ready` \| `placeholder` |
| `notes` | no | Speaker notes; agent provenance |
| `image` | no | Path relative to manifest dir (e.g. `diagrams/ml_agents_flow.png`) |

## CLI reference

All commands accept `--manifest PATH` and `build` accepts `--output PATH`.

| Command | Action |
|---------|--------|
| `check` | Validate manifest schema and unique ids |
| `list` | Print slide table |
| `init --force` | Bootstrap from `presentation_seed_final_review.py` |
| `set --id ID [--title] [--bullets a\|b] [--notes] [--status]` | Replace fields |
| `append --id ID --bullets a\|b` | Append bullets |
| `diagrams` | Regenerate PNGs from matplotlib renderer |
| `build` | Write `.pptx` |

Pipe separator for bullets avoids JSON escaping in PowerShell.

## Research → slide mapping (examples)

| User asks | Likely slides | Sources |
|-----------|---------------|---------|
| "What did Exp4 show?" | M16, M17–M19, B04 | `docs/experiments/pipeline/1-built/04-agent-reference-pointing.md`, run `config.json`, `summary_metrics.json` |
| "Explain safe mode" | M12 | `simulation/attitude_controller.py`, `ATTITUDE_SAFETY.py` |
| "Add eval video proof" | M17, B01 | `runs/*/videos/eval_best.mp4` + video-frame-inspect |
| "Reward terms" | M10 | `docs/presentation/machine-learning.md`, `autonomous_control/reward.py` |

## New deck bootstrap

1. Copy or fork `presentation_seed_final_review.py` in `.cursor/tools/presentation/`.
2. `init --manifest docs/presentation/<name>/slides_manifest.json --force`
3. Point user to new folder; document in tool README if recurring.

## Anti-patterns

| Don't | Do |
|-------|-----|
| Paraphrase KPIs from memory | Read `summary_metrics.json` or pipeline verdict |
| Skip `build` after `set` | Always `check` → `build` |
| Put tool code in `backend/scripts/` | `.cursor/tools/presentation/` |
| Close behavioral claims without frames | video-frame-inspect when MP4 exists |
