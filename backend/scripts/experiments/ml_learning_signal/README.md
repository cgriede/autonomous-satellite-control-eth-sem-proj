# ML learning signal — hypothesis cycle

**Goal:** MPO policy using current S01 observation features must beat zero reward during train episodes and show an increasing return curve on episodes 1–3 (all non-zero; ep2 or ep3 > ep1).

**Reference run today:** `nb-s01-08-2026-06-27_12-19-52` — train return 3.73 on 1 episode (sparse capture credit). Most 10-ep runs show train return 0.

## Frozen baseline

| Knob | Value |
|------|-------|
| seed | 7 |
| warmup episodes | 5 (cached `nb_bundle`) |
| train episodes | **3** (branch budget) |
| eval episodes | 0 |
| features | `S01_TRAINING_FEATURE_CONFIG` |
| reward | `enable_image_quality_capture=True` only |

## Success bar (strong lead)

```text
train_return[0] > 0
train_return[1] > 0
train_return[2] > 0
train_return[1] > train_return[0] OR train_return[2] > train_return[0]
```

Baseline deterministic warmup mean ≈ 89 (cached baseline overflight captures).

## Commands (PowerShell, repo root)

```powershell
conda activate auto-sat; python backend/scripts/experiments/ml_learning_signal/run_baseline.py
conda activate auto-sat; python backend/scripts/experiments/ml_learning_signal/a_fundamental_limit/run_a1.py
conda activate auto-sat; python backend/scripts/experiments/ml_learning_signal/b_bug_hunt/run_b1.py
conda activate auto-sat; python backend/scripts/experiments/ml_learning_signal/c_hparam_search/run_c1.py
```

## Branches

| Branch | Hypothesis | Max runs |
|--------|------------|----------|
| `a_fundamental_limit` | Structural reason current approach cannot learn | 3 |
| `b_bug_hunt` | Wiring bug fix restores learning | 3 |
| `c_hparam_search` | Dropout / init / LR unlock learning | 3 |

Shared baseline JSON: `results/baseline.json`.

Probe NDJSON (optional): `results/ml_learning_signal_fundamental.ndjson`.
