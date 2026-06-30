# Training loop timing profiler

Experiment-only instrumentation for **one MPO train episode** after warmup. Measures where wall time goes in the serial rollout + learner loop (sim, obs, `get_action`, `store`, `train`, progress).

Production `episode_runner.py` accepts an optional `EpisodeTimingCollector`; no permanent timing code in the hot path unless a collector is passed.

## Categories

| Key | Meaning |
|-----|---------|
| `sim_step` | `stepper.step` + shutter capture |
| `obs_build` | `build_controller_observation_from_timestep` |
| `state_copy` | `collect_states` copy path |
| `get_action` | Policy inference |
| `controller_baseline` | Warmup baseline only |
| `store` | Replay `store()` |
| `train` | `agent.train()` |
| `progress` | Live feed / progress display |

Output includes **top 7 consumers** by % of episode wall time.

## Run (repo root, PowerShell)

```powershell
conda activate auto-sat
python backend/scripts/experiments/train_timing/run_profile.py
python backend/scripts/experiments/train_timing/run_profile.py --dt-label dt_1.5s --tag prod
python backend/scripts/experiments/train_timing/run_profile.py --updates-per-step 4 --tag ups4
python backend/scripts/experiments/train_timing/run_profile.py --train-every-n-steps 5 --tag stride5
```

Results: `results/train_episode_{tag}.json` and `.md`.

## Compare knobs (strategy search)

Re-run with different `--updates-per-step`, `--train-every-n-steps`, `--batch-size`, or `--dt-label` and diff JSON `top_7_consumers` + `steps_per_s`. Warmup wall time is recorded separately and excluded from episode buckets.

**Duty-cycle sweep** (`train_every_n_steps` = collect, `updates_per_step` = burst):

```powershell
python backend/scripts/experiments/train_timing/run_duty_cycle_compare.py
```

Results: `results/duty_cycle_compare.md`.

## Layout

| Path | Purpose |
|------|---------|
| `backend/autonomous_control/episode_timing.py` | Shared collector + report |
| `_fixtures.py` | S01 setup + dt profile |
| `_profile_runner.py` | Warmup + timed train episode |
| `_cpu_budget.py` | Thread cap (same as overnight) |
| `run_profile.py` | CLI |
| `run_duty_cycle_compare.py` | Multi-variant duty-cycle sweep |

## Related

- `sim_timing/` — simulation-only (no MPO train)
- `ml_algo_overnight/_phases/h0_dt.py` — end-to-end steps/s gate (no category split)
