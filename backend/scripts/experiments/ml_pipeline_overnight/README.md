# ml_pipeline_overnight — Exp 3–6 sequential orchestrator

Runs pipeline experiments **one at a time** (global `pipeline_run_guard`). Each step delegates to its slug’s own `run_*.py`.

**Watch:** [`.cursor/skills/long-run-watch/profiles/ml-pipeline-overnight.md`](../../../../.cursor/skills/long-run-watch/profiles/ml-pipeline-overnight.md)

## Steps (order)

| Step | Slug | Runner | Completion artifact |
|------|------|--------|---------------------|
| exp3 | `ml_sac_mpo_compare` | `run_sac_mpo_compare.py` | `results/compare_sac_mpo.json` |
| exp4 | `ml_agent_reference_pointing` | `run_agent_reference.py` | `results/agent_reference.json` |
| exp5 | `ml_mpo_model_size` | `run_mpo_model_size.py` | `results/mpo_model_size_summary.json` |
| exp6 | `ml_modular_encoder_r2` | `run_modular_encoder_r2.py` | `results/modular_encoder_r2_summary.json` |

Gates: exp4 & exp5 require exp3 summary; exp6 requires exp5 summary (override with `--ignore-gates`).

## Commands (PowerShell)

```powershell
$env:KMP_DUPLICATE_LIB_OK='TRUE'
conda activate auto-sat
cd D:\code\sem-proj-asc\backend\scripts\experiments\ml_pipeline_overnight

# Readiness (runners + smoke + summaries)
python .\run_pipeline_overnight.py --preflight

# Smoke each built slug
python .\run_pipeline_overnight.py --smoke-all --allow-cpu

# Full queue — charter protocol (exp3 default 20 ep unless overridden)
python .\run_pipeline_overnight.py --show-progress

# Learnable protocol (50 train ep, patience 20, exp5 sparse reward)
python .\run_pipeline_overnight.py --show-progress --protocol learnable

# Resume from exp5, skip completed
python .\run_pipeline_overnight.py --from exp5 --show-progress

# Subset
python .\run_pipeline_overnight.py --steps exp3,exp5 --show-progress --protocol learnable
```

## Orchestrator artifacts

- `results/pipeline_overnight.log`
- `results/pipeline_overnight_summary.json`
- `results/exp*_error.json` on step failure

## Notes

- Steps with **missing runners** or **failed smoke** are skipped (or stop the queue unless `--continue-on-error`).
- Do not start another pipeline training job while a step is running ([D-012](../../../../docs/research/DECISIONS.md)).
- Exp 4 / Exp 6 runners wire in automatically once subagent scaffolds land — re-run `--preflight`.
