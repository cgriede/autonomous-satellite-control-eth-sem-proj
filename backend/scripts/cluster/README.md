# Euler cluster (ETH)

Docs: [HPC getting started](https://docs.hpc.ethz.ch/tutorials/getting-started/), [Slurm](https://docs.hpc.ethz.ch/batchsystem/slurm/), [Conda](https://docs.hpc.ethz.ch/software/package-managers/conda/), [Storage](https://docs.hpc.ethz.ch/hardware/storage/).

## Quick start

```bash
# login node — once
cd ~/auto-sat-train
git clone <remote> autonomous-satellite-control-eth-sem-proj
bash autonomous-satellite-control-eth-sem-proj/backend/scripts/cluster/euler_setup.sh

# submit job (always sbatch, never run training on login nodes)
cd autonomous-satellite-control-eth-sem-proj/backend/scripts/cluster
sbatch euler_train.sbatch
squeue -u "$USER"
```

## Environment install (ETH rules)

| What | Where |
|------|--------|
| Conda / `auto-sat` env | `$HOME` (you already have `~/miniconda3`) |
| Training runs, videos, checkpoints | `$SCRATCH/auto-sat-runs` via `AUTO_SAT_MODELS_ROOT` |
| Optional fast temp I/O | Node `$TMPDIR` — request with `#SBATCH --tmp=10g` |

Do **not** put conda envs on `$SCRATCH` or `/cluster/work` (many small files).

## GPU

GPUs require a **shareholder** account ([shareholders](https://docs.hpc.ethz.ch/users/shareholders/)). Uncomment `--gpus=...` and `--account=...` in `euler_train.sbatch`. Without GPU, training falls back to CPU (slow but works for smoke tests).

## Scratch sizing

`$SCRATCH` holds up to ~2.5 TB per user; files older than ~15 days are deleted. Start without `--tmp`; add `--tmp=10g` only if you need node-local scratch for heavy temp I/O.
