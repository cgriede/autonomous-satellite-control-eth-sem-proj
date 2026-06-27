#!/usr/bin/env bash
# One-time Euler setup for auto-sat training.
# Run on a login node (not for training itself):  bash euler_setup.sh
#
# ETH guidance (https://docs.hpc.ethz.ch/software/package-managers/conda/):
#   - Install conda envs in $HOME (not $SCRATCH /cluster/work — many small files hurt Lustre).
#   - Training run outputs default to $REPO_ROOT/data (inside your git clone).
#   - Use sbatch for all compute; never run training on login nodes.

set -euo pipefail

REPO_ROOT="${1:-${HOME}/auto-sat-train}"
ENV_NAME="${AUTO_SAT_CONDA_ENV:-auto-sat}"

echo "Repo target: ${REPO_ROOT}"

if [[ ! -d "${REPO_ROOT}/backend" ]]; then
  echo "Clone the repo first, e.g.:"
  echo "  mkdir -p ${HOME}/auto-sat-train && cd ${HOME}/auto-sat-train"
  echo "  git clone <your-remote> autonomous-satellite-control-eth-sem-proj"
  exit 1
fi

if [[ ! -f "${HOME}/miniconda3/etc/profile.d/conda.sh" ]]; then
  echo "Install Miniconda in \$HOME first: https://docs.conda.io/en/latest/miniconda.html"
  exit 1
fi

# shellcheck source=/dev/null
source "${HOME}/miniconda3/etc/profile.d/conda.sh"

if ! conda env list | awk '{print $1}' | grep -qx "${ENV_NAME}"; then
  conda create -n "${ENV_NAME}" python=3.13 -y
fi
conda activate "${ENV_NAME}"

pip install --upgrade pip
pip install -r "${REPO_ROOT}/requirements.txt"
# CUDA wheels: pick the index matching the GPU driver on Euler (shareholder GPU nodes).
pip install torch --index-url https://download.pytorch.org/whl/cu124

mkdir -p "${REPO_ROOT}/data"
mkdir -p "${REPO_ROOT}/backend/scripts/cluster/cluster_logs"
echo "Run outputs (set in sbatch): AUTO_SAT_MODELS_ROOT=${REPO_ROOT}/data"
echo "Setup done. Submit with:  cd ${REPO_ROOT}/backend/scripts/cluster && sbatch euler_train.sbatch"
