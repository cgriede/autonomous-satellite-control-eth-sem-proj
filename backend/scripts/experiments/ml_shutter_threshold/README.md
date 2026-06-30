# ml_shutter_threshold

**Exp 1** in the [ML status board](../../../../docs/ml/experiments/STATUS_2026-06.md).

MPO sparse training with shutter threshold **0.5 vs 0.9** and a **15 s** capture-credit window fork.

## Run

```powershell
$env:KMP_DUPLICATE_LIB_OK='TRUE'
conda activate auto-sat
cd D:\code\sem-proj-asc\backend\scripts\experiments\ml_shutter_threshold
python .\run_shutter_threshold.py --smoke
python .\run_shutter_threshold.py --show-progress
```

## Outputs

- `results/shutter_threshold_summary.json`
- `results/plots/*.png`
- `shutter_threshold_analysis.md`

See [`SUBAGENT_CHARTER.md`](SUBAGENT_CHARTER.md) and [`H1-shutter-threshold.md`](H1-shutter-threshold.md).
