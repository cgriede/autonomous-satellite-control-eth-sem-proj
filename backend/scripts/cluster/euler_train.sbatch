#!/usr/bin/env bash
#SBATCH --job-name=auto-sat-s01
#SBATCH --time=24:00:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem-per-cpu=4g
#SBATCH --output=cluster_logs/slurm-%j.out
#SBATCH --error=cluster_logs/slurm-%j.err

# GPU shareholders only (public share has no GPUs). Uncomment one line:
# #SBATCH --gpus=rtx_3090:1
# #SBATCH --gpus=rtx_4090:1
# #SBATCH --account=<your-share-name>

# Optional per-node local scratch ($TMPDIR, deleted when job ends). Start small; raise if needed.
# #SBATCH --tmp=10g

set -euo pipefail

REPO_ROOT="${AUTO_SAT_REPO:-${HOME}/auto-sat-train}"
BACKEND="${REPO_ROOT}/backend"
ENV_NAME="${AUTO_SAT_CONDA_ENV:-auto-sat}"
RUN_TAG="euler-${SLURM_JOB_ID:-local}"

export PYTHONUNBUFFERED=1
export MPLBACKEND=Agg

# Training artifacts under the repo clone (not $SCRATCH; override with AUTO_SAT_MODELS_ROOT).
export AUTO_SAT_MODELS_ROOT="${AUTO_SAT_MODELS_ROOT:-${REPO_ROOT}/data}"
mkdir -p "${AUTO_SAT_MODELS_ROOT}"

# shellcheck source=/dev/null
source "${HOME}/miniconda3/etc/profile.d/conda.sh"
conda activate "${ENV_NAME}"

# Matplotlib FFMpegWriter needs ffmpeg on PATH (imageio-ffmpeg alone is not enough).
# module spider ffmpeg/6.0 on Euler → requires stack/2024-06 + gcc/12.2.0
module load stack/2024-06 gcc/12.2.0
module load ffmpeg/6.0
command -v ffmpeg >/dev/null || { echo "ffmpeg not on PATH after module load"; exit 1; }

cd "${BACKEND}"
echo "host=$(hostname) job=${SLURM_JOB_ID:-} models=${AUTO_SAT_MODELS_ROOT}"
python -c "import torch; print('cuda', torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else '')"

python scripts/run_s01_training.py \
  --seed 7 \
  --warmup-episodes 10 \
  --train-episodes 20 \
  --eval-episodes 2 \
  --run-id "${RUN_TAG}"

echo "done run_dir=${AUTO_SAT_MODELS_ROOT}/${RUN_TAG}"
