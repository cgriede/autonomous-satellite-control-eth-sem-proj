# MPO model size (Exp 5) — investigation closeout

**Pipeline:** [Exp 5](../experiments/pipeline/4-documentation/05-mpo-model-size.md)  
**Parent synthesis:** [model-size-investigation.md](model-size-investigation.md)

## Run summary (2026-06-30)

- **Reward:** sparse (not charter dense — Exp 3 showed dense does not sustain MPO learning)
- **Train:** 50 ep per arm (not charter 7)
- **Result:** S/M/L **identical** eval **−51.6**, flat after ep 1; KL → 0

## Verdict

**not_supported** on H5a/H5b; **H5d supported** — capacity ruled out; identical collapse across 90/140 through 256/512 heads.

## Decision

[D-018](DECISIONS.md) — do not pursue MPO width ablation further until MPO achieves a learnable reward/algorithm regime (e.g. vector action space Ref2).

## Artifacts

- `backend/scripts/experiments/ml_mpo_model_size/results/mpo_model_size_summary.json`
- Run dirs: `9998217218692971_ml_mpo_model_size_mpo_s_01-01-46`, `..._mpo_m_01-34-47`, `..._mpo_l_02-08-18`
