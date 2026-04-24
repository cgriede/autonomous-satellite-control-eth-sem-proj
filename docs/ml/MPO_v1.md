# MPO v1 Integration Notes

This document describes the first wired integration of the MPO (Maximum a Posteriori Policy Optimization) controller in this repository.

## Code layout

- `backend/autonomous_control/controller_actor.py`: Gaussian actor network.
- `backend/autonomous_control/controller_critic.py`: twin Q critics.
- `backend/autonomous_control/controller_agent.py`: MPO training loop, action selection, replay usage (`MPOAgent`).
- `backend/autonomous_control/mpo_config.py`: central hyperparameter/config source.
- `backend/autonomous_control/training_runtime.py`: replay buffer, environment factory, episode loop.
- `backend/utils/ml_training/ml_training_utils.py`: run directory, checkpoint pathing, run logs, aggregate JSONL.
- `backend/paths.py`: pathlib constants including `MODELS_ROOT` (`backend/autonomous_control/models`).
- `backend/scripts/train_sat_agent.py`: training entrypoint.
- `backend/scripts/eval_sat_agent.py`: evaluation entrypoint + optional trace/render video export.
- `backend/render/render_main.py`: Sat Sim visualization/export pipeline (`Sat Sim Export`).

## MPO flow in this project

1. Collect transitions from `SatelliteAttitudeControlEnv` episodes.
2. Store transitions in `ReplayBuffer`.
3. Critic target:
   - sample `K_q` actions from target actor at `next_obs`,
   - evaluate target critics and average sampled target values,
   - build Bellman target.
4. Critic update:
   - optimize `q1` and `q2` with MSE to target.
5. Actor update:
   - sample `K_pi` actions using reparameterization,
   - importance weights from critic values and temperature `eta`,
   - weighted log-likelihood objective.
6. Temperature update:
   - decoupled KL (`mu` + `sigma`) by default (configurable).
7. Polyak updates:
   - soft-update actor/critic target networks.

## Architectural position

- Long-term target architecture is hierarchical mission control (high-level planner over OBC low-level control).
- Current MPO setup with direct wheel-torque action is an interim experimental interface for rapid iteration.
- Episode semantics target: one episode equals one canonical simulation rollout artifact (`SimulationStateSeries`).

## Hyperparameter source of truth

All tunable MPO constants are centralized in `backend/autonomous_control/mpo_config.py`:

- learning rates (`learning_rate_q`, `learning_rate_pi`, `learning_rate_eta`)
- KL targets (`target_kl_mu`, `target_kl_sigma`)
- architecture knobs (`num_layers_actor`, `num_units_actor`, `num_layers_critic`, `num_units_critic`, `actor_dropout`)
- sampling counts (`num_samples_q`, `num_samples_pi`)
- optimization and rollout settings (`tau`, `gamma`, `batch_size`, `warmup_episodes`, etc.)
- actor log-std bounds (`LOG_STD_MIN`, `LOG_STD_MAX`)

## Artifact and logging structure

Artifact root is resolved from `backend/paths.py`:

- `backend/autonomous_control/models/<timestamp>/`
  - `agent.pt` (default checkpoint name)
  - `run_log.md` (human-readable run log)
  - `policy_trace.mp4` (optional state-trace video)
  - `sat_sim_export.mp4` (optional rendered world-effect video)
- `backend/autonomous_control/models/runs.jsonl`
  - append-only global run records for train/eval runs

Primary episode-level artifact contract:
- `SimulationStateSeries` is required for episode-level simulation semantics.

Timestamp run IDs use UTC format:

- `YYYY-MM-DD_HH-MM-SS`

## Train and eval usage

From `backend/`:

```bash
python scripts/train_sat_agent.py --seed 0 --train-episodes 20 --warmup-episodes 0
```

Optional video exports on train:

```bash
python scripts/train_sat_agent.py --seed 0 --train-episodes 20 --save-video
```

```bash
python scripts/eval_sat_agent.py --checkpoint autonomous_control/models/<run_id>/agent.pt --eval-episodes 5
```

Optional video exports on eval:

```bash
python scripts/eval_sat_agent.py --checkpoint autonomous_control/models/<run_id>/agent.pt --save-video policy_trace.mp4
```

```bash
python render/render_main.py --render-mode export --controller-mode baseline --save-one-pass-30x
```

- `--save-video ...` writes the state-trace rollout video.
- Sat Sim render export is available for simulation-native controller modes (`baseline`, `random`).

## Reward authority and document alignment

- Runtime reward behavior in code is canonical for this phase.
- Semester-project PDF is design reference; explicit deltas must be documented.
- Current known intentional delta: energy-related reward terms exist in code and are enabled/disabled through flags.
