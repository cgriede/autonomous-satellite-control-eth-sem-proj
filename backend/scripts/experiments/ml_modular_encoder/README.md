# ml_modular_encoder — Exp 2

**Pipeline:** [02-modular-encoder.md](../../../../docs/experiments/pipeline/4-documentation/02-modular-encoder.md)

## Hypothesis (H1)

SAC sparse with **vector compressors** on per-target bearing/mask fields (arm **A1**) learns better than production flat `ControllerEncoder` (arm **A0**) at dt **1.5 s / 1.5 s**, 7 train episodes.

## Arms

| Arm | Encoder | Agent |
|-----|---------|-------|
| `sac_a0` | Production `ControllerEncoder` (flat concat) | Overnight `SACAgent` fork |
| `sac_a1` | `CompressedControllerEncoder` — passthrough globals + `Linear(50→k)` on bearing/mask | `SACModularAgent` |

Default `k` (`--vector-embed-dim`): **8**.

## Entry point

```powershell
conda activate auto-sat
cd D:\code\sem-proj-asc\backend\scripts\experiments\ml_modular_encoder
python .\run_modular_encoder.py --smoke --allow-cpu          # quick check
python .\run_modular_encoder.py --show-progress --arms sac_a0,sac_a1
```

## Not overengineered

- One hook: encoder forward path only; SAC training loop unchanged from overnight fork.
- A2 split heads **deferred** unless A1 hits `learning_mode`.
- Reuses overnight `_reward_fork` (sparse), `_sim_constants_fork` (dt 1.5 s), `pipeline_run_guard`.

## Results

- Summary: `results/modular_encoder_summary.json`
- Analysis: `modular_encoder_analysis.md`
- Per-arm log: `results/modular_encoder.log`
