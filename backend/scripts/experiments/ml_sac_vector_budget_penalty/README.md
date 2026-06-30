# ml_sac_vector_budget_penalty — Exp 7 SAC vector + budget shutter penalty

**Pipeline:** [07-sac-vector-budget-penalty.md](../../../../docs/experiments/pipeline/4-documentation/07-sac-vector-budget-penalty.md)

## Hypothesis

SAC sparse + **vector** OBC with a **penalty for shutter commands when capture budget ≤ 0** reduces end-of-episode shutter spam vs Exp 4 Ref1 baseline (read-only comparison — no `penalty_off` re-run).

## Arms

| Arm | Runs? | Notes |
|-----|-------|-------|
| **penalty_on** | **Yes** | Treatment — budget-exhausted shutter penalty fork |
| penalty_off | **No** | Baseline = Exp 4 Ref1 `9998217182442815_ml_ref_ref1_vector_11-05-57` |

## Protocol

| Knob | Value |
|------|-------|
| dt | 1.5 s / 1.5 s |
| seed | 7 |
| warmup | 5 (rebuild) |
| train | **50** |
| eval | 2 |
| SAC | `lr_pi=4.5e-4`, `lr_q=1e-3` (match Ref1) |
| TensorBoard | **on by default** (`--no-tensorboard` to disable) |

## Run

```powershell
$env:KMP_DUPLICATE_LIB_OK='TRUE'
conda activate auto-sat
cd D:\code\sem-proj-asc\backend\scripts\experiments\ml_sac_vector_budget_penalty
python .\run_sac_vector_budget.py --smoke --allow-cpu
python .\run_sac_vector_budget.py --show-progress
```

TensorBoard (after run):

```powershell
tensorboard --logdir D:\code\sem-proj-asc\backend\autonomous_control\runs\<run_dir>\tensorboard
```

## Mutex

Global `pipeline_run_guard` ([D-012](../../../../docs/research/DECISIONS.md)).

## Results

- `results/smoke.json`
- `results/sac_vector_budget.json`
- Run dir: `ml_sac_vector_budget_*` under `backend/autonomous_control/runs/`
