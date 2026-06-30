# ml_sac_mpo_compare — Exp 3 SAC vs MPO (same-day)

**Pipeline:** [03-sac-mpo-compare.md](../../../../docs/experiments/pipeline/1-built/03-sac-mpo-compare.md)

## Hypothesis

SAC sparse vs MPO dense @ dt 1.5s — see [H3-sac-mpo-compare.md](H3-sac-mpo-compare.md).

## Run

```powershell
$env:KMP_DUPLICATE_LIB_OK='TRUE'
conda activate auto-sat
cd D:\code\sem-proj-asc\backend\scripts\experiments\ml_sac_mpo_compare
python .\run_sac_mpo_compare.py --smoke
python .\run_sac_mpo_compare.py --show-progress
```

Default artifact mode follows `TrainingWorkflowConfig` (3 train + 2 eval MP4s). Use `--trim-artifacts` for a faster export slice.

## Mutex

Wait until `pipeline_run_guard` is clear before full training ([D-012](../../../../docs/research/DECISIONS.md)).
