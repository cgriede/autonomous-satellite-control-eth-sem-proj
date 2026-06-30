# Euler cluster (ETH)

Docs: [HPC getting started](https://docs.hpc.ethz.ch/tutorials/getting-started/), [Slurm](https://docs.hpc.ethz.ch/batchsystem/slurm/), [Conda](https://docs.hpc.ethz.ch/software/package-managers/conda/), [Storage](https://docs.hpc.ethz.ch/hardware/storage/).

## Quick start

```bash
# login node — once
cd ~
git clone <remote> auto-sat-train
bash auto-sat-train/backend/scripts/cluster/euler_setup.sh

# submit job (always sbatch, never run training on login nodes)
cd auto-sat-train/backend/scripts/cluster
mkdir -p cluster_logs
sbatch euler_train.sbatch
squeue -u "$USER"
```

Set `AUTO_SAT_REPO` if your clone lives elsewhere.

## Environment install (ETH rules)

| What | Where |
|------|--------|
| Conda / `auto-sat` env | `$HOME` (you already have `~/miniconda3`) |
| Training runs, videos, checkpoints | `$REPO_ROOT/data` via `AUTO_SAT_RUNS_ROOT` / `AUTO_SAT_MODELS_ROOT` (default: `~/auto-sat-train/data`) |
| Slurm stdout/stderr | `backend/scripts/cluster/cluster_logs/` |
| Optional fast temp I/O | Node `$TMPDIR` — request with `#SBATCH --tmp=10g` |

Do **not** put conda envs on `$SCRATCH` or `/cluster/work` (many small files).

## Run output retention

`data/` lives in your repo clone under `$HOME`, so runs persist until you delete them (unlike `$SCRATCH`, which ETH auto-purges after ~15 days). `data/` is gitignored — sync checkpoints elsewhere if you need backups.

## GPU

GPUs require a **shareholder** account ([shareholders](https://docs.hpc.ethz.ch/users/shareholders/)). Uncomment `--gpus=...` and `--account=...` in `euler_train.sbatch`. Without GPU, training falls back to CPU (slow but works for smoke tests).

## Scratch sizing

`$SCRATCH` is unused for training outputs by default. Add `#SBATCH --tmp=10g` only if you need node-local scratch for heavy temp I/O during a job.

## Episode video export

Training exports MP4s via matplotlib's FFMpegWriter, which requires a system `ffmpeg` on `PATH`. `euler_train.sbatch` loads `stack/2024-06`, `gcc/12.2.0`, and `ffmpeg/6.0` after conda activate. On a login node, smoke-test with:

```bash
module load stack/2024-06 gcc/12.2.0 ffmpeg/6.0
conda activate auto-sat
python -c "import matplotlib.animation as a; print('ffmpeg writer', a.writers.is_available('ffmpeg'))"
```

Expected: `ffmpeg writer True`.
