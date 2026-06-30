# ml_mpo_model_size

Exp 5 — MPO policy/critic **width ablation** (S / M / L) with production `MPOAgent` and fixed `ControllerEncoder`.

## Grid (3 arms)

| Arm | Actor | Critic | Layers actor | Layers critic |
|-----|-------|--------|--------------|---------------|
| `mpo_s` | 90 | 140 | 1 | 2 |
| `mpo_m` | 140 | 256 | 2 | 2 |
| `mpo_l` | 256 | 512 | 2 | 3 |

Shared raised LRs (placeholder r2 protocol): `learning_rate_pi=4.5e-4`, `learning_rate_q=1e-3`, `actor_dropout=0`.

Protocol: dt 1.5 s / 1.5 s, **50 train + 2 eval** (workflow defaults in `profile.json`), 3 train + 2 eval videos.

## Protocol ambiguity (read before Phase 2)

| Knob | Phase 0 charter | Scaffold default | Notes |
|------|-----------------|------------------|-------|
| Train episodes | **7** + 2 eval | **50** + 2 eval | Aligns with winning SAC hparam grid; defer width-first per [D-005](../../../docs/research/DECISIONS.md) until learnable signal |
| Reward mode | **dense** (H6) unless Exp 3 sparse MPO learns | **`--reward-mode sparse`** (default) | Exp 3 not closed; freeze reward before full grid |
| Width ablation | Primary lever | Implemented (S/M/L) | Encoder fixed; only `MPOConfig` head widths vary |

Use `--reward-mode dense` to run the charter-default dense fork. Document final choice in DECISIONS before Phase 2.

## Run

```powershell
conda activate auto-sat
cd D:\code\sem-proj-asc\backend\scripts\experiments\ml_mpo_model_size
python .\run_mpo_model_size.py --smoke --allow-cpu --arms mpo_s
python .\run_mpo_model_size.py --show-progress --arms mpo_s
python .\run_mpo_model_size.py --show-progress --reward-mode dense
```

Results: `results/mpo_model_size_summary.json`, `results/arm_kpis/{arm}.json`, smoke → `results/smoke.json`.

## References

- Charter: [05-mpo-model-size.md](../../../docs/experiments/pipeline/0-initialized/05-mpo-model-size.md)
- Investigation: [model-size-investigation.md](../../../docs/research/model-size-investigation.md)
- Template: `ml_sac_hparam_grid/` (size presets), `ml_sac_mpo_compare/` (production MPO wiring)
