# ml_mpo_episode_seed_diversity (Exp 15)

Per-episode env seed + paired deterministic baseline on every train/eval scenario.
Fork of Exp 14 (factored MPO + PD OBC); cloud bounds frozen.

## Run

```powershell
conda activate auto-sat
cd backend/scripts/experiments/ml_mpo_episode_seed_diversity

python run.py --verify
python run.py --smoke --show-progress
python run.py --full --show-progress --train-episodes 50
```

| Step | Command | What |
|------|---------|------|
| Verify | `--verify` | Action/conversion checks |
| Smoke | `--smoke` | 1 warmup + 2 train (distinct seeds + paired baseline) |
| Full | `--full` | 5 warmup + N train (default 50); baseline every train ep; paired 5-seed eval |
| Eval | `--eval-comparison` | Re-run paired eval from checkpoint |

`--no-pair-baseline-train` skips train-time baseline (eval still paired).

## Artifacts

| Path | Purpose |
|------|---------|
| `results/smoke.json` | Smoke KPIs |
| `results/full_summary.json` | Train rows + paired eval |
| `results/eval_comparison.json` | Standalone paired eval |
| `results/checkpoints/hp_explore/episode_seed_final.pt` | Final weights |
