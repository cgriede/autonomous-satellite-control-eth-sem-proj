# User rule — paste into Cursor Settings → Rules

Copy the block below into your **global User Rules** (applies across projects).

---

## Respect defaults on self-built functions

When calling **project-owned** functions, configs, and workflows (e.g. `TrainingWorkflowConfig`, `frozen_training_config`, `run_training_workflow`, experiment runners), use **declared defaults** unless the user explicitly asks to override a specific parameter in the current chat.

- Do **not** silently replace defaults in wrapper/runner code (e.g. forcing `train_episode_videos=0` when the dataclass default is `3`).
- Only pass non-default arguments when the user requested them or a profile/config file explicitly sets them for that run.
- If a performance shortcut exists (trimmed artifacts, fewer exports), make it **opt-in** (e.g. `--trim-artifacts`), not the default path.
- When unsure whether to override a default, ask once rather than guessing.

**Training workflow defaults** (`s01_utils/training_workflow.py::TrainingWorkflowConfig`):

| Field | Default |
|-------|---------|
| `eval_episodes` | 2 |
| `train_episode_videos` | 3 (top train episodes by return) |
| `eval_episode_videos` | 2 |
| `export_episode_reward_plots` | true |

Episode simulation is expensive (~30 s/episode); skipping video export after a long train run wastes that effort unless the user opts into a trim mode.
