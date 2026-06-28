# ML algorithm overnight hypothesis cycle

One-command overnight runner to test whether RL can learn satellite EO control (torque + shutter) under a frozen S01 contract.

## Run (PowerShell, repo root)

```powershell
conda activate auto-sat; python backend/scripts/experiments/ml_algo_overnight/run_overnight.py
```

Optional flags:

```powershell
python backend/scripts/experiments/ml_algo_overnight/run_overnight.py --smoke-only
python backend/scripts/experiments/ml_algo_overnight/run_overnight.py --from h6
python backend/scripts/experiments/ml_algo_overnight/run_overnight.py --phases h1a,h6
python backend/scripts/experiments/ml_algo_overnight/run_overnight.py --allow-cpu
```

## Queue (serial)

1. **Smoke** — CUDA, imports, mini warmup, one `train()`, ffmpeg probe
2. **H0** — dt sweep → `results/dt_profile.json` (train episodes 7 or 10)
3. **H1a** — MPO + sparse reward
4. **H1b** — MPO + fixed η (no dual optimizer)
5. **H6** — MPO + dense latent + 10× applied shutter (warmup cache rebuild)
6. **H4** — SAC fixed α=0.2 + sparse reward

Deferred: H2 PPO, H3 V-MPO, H5 P-DQN — see `docs/deferred_phases.md`.

## Primary KPI — `learning_mode`

Not “beat baseline ~89”. Pass when:

- Any non-zero train return
- Improving train curve (last > first or max later eps > first)
- Finite MPO KL (< 1e4) for MPO arms

See `_runner_common.evaluate_learning_mode`.

## Morning readout

1. `results/overnight_summary.json` — ranked by `learning_mode`
2. Phase JSON + `*_analysis.md` cards
3. Videos under each phase `run_dir/videos/` (top-3 train + 2 eval)

## Decision tree

| Outcome | Action |
|---------|--------|
| H6 `learning_mode`, H1 not | Reward/credit blocker; promote dense fork |
| H1b yes, H1a no | η dual was the issue |
| H4 yes, MPO not | Algorithm swap; deep SAC or deferred H3 |
| Nothing learns | Wiring/scale bug; try deferred H2 PPO |

## Frozen contract

| Knob | Value |
|------|-------|
| seed | 7 |
| warmup | 5 cached baseline overflight |
| eval | 2 episodes, actor mean |
| features | `S01_TRAINING_FEATURE_CONFIG` (406-dim) |
| reward (default) | sparse applied capture only |

Production code is **read-only**; forks live in this folder only.
