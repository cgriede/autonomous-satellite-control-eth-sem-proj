# %%
"""
S01 MPO training — integrate notebooks 01–07 mission context.

Scenario:
  - Same mission profile as notebook 07 baseline overflight (50-target meridian grid,
    seeded clouds over the corridor, dual camera, attitude safety on, image quality)
  - Controller features selected via ControllerFeatureConfig (see cell below)
  - 10× baseline overflight warmup (sliced target windows per ep, wrap mod n_chunks) → train → eval
  - Preflight: inline feature checks + full ML training pytest suite

Verification: s01_utils/training_workflow.py
Artifacts: autonomous_control/runs/nb-s01-08-<timestamp>/
Export: eval_best.mp4 in run directory
"""

# %%
def setup_notebook_paths():
    """
    Configure Python paths and working directory for running the S01 training notebook.

    - Walks up directories from the current working directory until it finds the 'simulation' folder,
      which marks the backend root.
    - Changes the working directory to the backend root to ensure relative paths are correct.
    - Adds both the backend root and the S01 notebook utilities directory to sys.path for imports.

    This setup is required for importing backend modules and utility code in other cells.
    """
    import os
    import sys
    from pathlib import Path

    notebook_dir = Path.cwd()
    backend_root = notebook_dir
    for _ in range(6):
        if (backend_root / "simulation").is_dir():
            break
        backend_root = backend_root.parent
    os.chdir(backend_root)
    sys.path.insert(0, str(backend_root))
    _s01_dir = backend_root / "notebooks" / "s01"
    sys.path.insert(0, str(_s01_dir))
    print(f"backend_root={backend_root}")

setup_notebook_paths()

# %%
import importlib

import s01_utils.training_workflow as tw

importlib.reload(tw)

# Fast gate: inline checks + unit pytest (~3s). Re-runs are skipped via session/disk cache.
# For full serial episode-runner tests (~80s): tw.run_s01_training_preflight_gate(integration_pytest=True, force=True)
tw.run_s01_training_preflight_gate()

# %%
from dataclasses import replace

# Single source of truth: s01_utils/training_workflow.py (timestep keys + mission scalars).
# Customize with replace(), e.g. replace(tw.S01_TRAINING_FEATURE_CONFIG, include_capture_budget=False)
FEATURE_CONFIG = tw.S01_TRAINING_FEATURE_CONFIG

WORKFLOW_CONFIG = tw.TrainingWorkflowConfig(
    seed=7,
    feature_config=FEATURE_CONFIG,
    ###########
    warmup_targets_per_episode=10,
    warmup_episodes=5,
    use_warmup_bundle_cache=True,
    rebuild_warmup_bundle_cache=True,
    ##########
    train_episodes=3,
    ##########
    eval_episodes=1,
)

# Mission profile for layout tables (same as training).
_mission_resolved = tw.build_s01_training_mission_setup(seed=WORKFLOW_CONFIG.seed).resolve(
    require_camera=True
)
_secondary_bins = int(_mission_resolved.secondary_camera_observation_line_n_bins)
_n_targets = len(_mission_resolved.target_areas or ())
tw.display_feature_tables(
    FEATURE_CONFIG,
    secondary_camera_bins=_secondary_bins,
    n_mission_targets=_n_targets,
)

# %%
setup = tw.build_training_workflow_setup(WORKFLOW_CONFIG)
tw.print_training_setup_summary(setup)
tw.display_feature_snapshot_tables(setup)

# %%
ctx = tw.open_training_workflow(setup, show_progress=True)

# %%
tw.run_warmup(ctx)

# %%
tw.run_training(ctx)

# %%
result = tw.run_eval(ctx)  # finalizes artifacts; closes ctx

# %%
tw.print_training_kpis(result)

# %%
from utils.notebook.video import init_video_cell, play_saved_video

init_video_cell()

from utils.notebook.video import init_video_cell, play_saved_video

init_video_cell()
tw.display_training_artifacts(result)
video_path = result.artifact_paths["eval_best_video"]
if video_path.exists():
    play_saved_video(video_path)


