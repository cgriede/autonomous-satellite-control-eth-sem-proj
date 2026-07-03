# ml_mpo_multienv_target_select (Exp 14)

Multi-env MPO target selection with factored action space (Categorical target + move + shutter), move-gated PD OBC, and mission score KPI.

## Action layout (52-dim applied action)

| Index | Field | Meaning |
|-------|-------|---------|
| 0–49 | target one-hot | sampled target index executed this step |
| 50 | move_gym | > 0 → PD engage; ≤ 0 → coast |
| 51 | shutter_gym | > 0 → fire shutter |

Canonical encode/decode: `_action_constants.py` only.

## Run (two stages — run in order)

| Step | Command | What it does |
|------|---------|----------------|
| **1 — Hparam sweep (Stage A)** | `python run.py --screen --export-artifacts --show-progress` | Trains **5 LR/batch/entropy arms** on one fixed env (5 warmup + 20 train + 1 eval each). **Exports reward plots + top-N MP4s** per arm. Picks a **winner** → `results/screen_summary.json` |
| **2 — Full training (Stage B)** | `python run.py --full --export-artifacts --show-progress` | Trains **only the screen winner** on **10 diverse envs** (5 warmup + 30 train per env = 350 ep). Run **after** Stage A passes |
| **3 — Baseline reference** | `python run.py --eval-baseline --show-progress` | Scripted PD baseline on 5 held-out eval seeds (no learning). Run once before comparing treatment |
| **4 — Treatment vs baseline** | `python run.py --eval-comparison --show-progress` | Greedy trained agent on same 5 seeds vs baseline |

**Optional:** `python run.py --check-mutex` — fails if another pipeline job is already running (your screen run holds the lock until it finishes).

**Subset screen (faster debug):** `python run.py --screen --arms hp_default,hp_explore --show-progress`

**Warmup baseline quality gate** — after warmup, screen checks mission score, shutter count, and peak capture efficiency (applied/latent at shutter frames). Fails before train if baseline is broken. Preview with:

```powershell
python run.py --export-warmup-preview --reward-plot-only --show-progress
```

See `warmup_quality` in `results/warmup_preview.json` or `results/arm_kpis/{arm}.json`.

**Warmup video / reward plot (while screen is running):** open a second terminal:

```powershell
# Fast: latent (cyan) + applied (gold) reward plot only (~4 s)
python run.py --export-warmup-preview --reward-plot-only --show-progress

# Full: same + MP4 encode (slow, several minutes)
python run.py --export-warmup-preview --show-progress
```

Outputs under `results/artifacts/warmup_preview/` (`episodes/*_latent_applied.png`, `videos/*.mp4`).

**Export during screen:** add `--export-artifacts` to `--screen` (warmup plot after warmup; train/eval at arm end).

**Override Stage B winner:** `python run.py --full --arm hp_default --show-progress` (if you skip reading `screen_summary.json`)

### `--show-progress` console layout

With `--show-progress`, each stage prints (same pattern as `training_workflow` / `TrainingProgressDisplay`):

1. **Env banner** — `=== ENV N | mission_seed=… cloud_seed=… ===` (Stage B per env; screen uses fixed `ENV screen-fixed`)
2. **Simulation info panel** — once per phase block (first episode)
3. **Phase tqdm** — `Warmup` / `Train` / `Eval` with episode counter
4. **Step tqdm** — live return during each episode rollout
5. **Episode summary** — `[train] ep K: return=… score=… steps=…` (train + eval; warmup gets phase summary at end)

Status lines go to the console only (`append_log` → stdout via `tqdm.write`). Durable KPIs live in `results/*.json`.

### Setup (every session)

```powershell
conda activate auto-sat
cd D:\code\sem-proj-asc\backend\scripts\experiments\ml_mpo_multienv_target_select
```

### Typical operator sequence

```powershell
# You are here if Stage A is running or not started:
python run.py --screen --show-progress

# After screen_summary.json has winner_arm_id and gates look OK:
python run.py --full --show-progress

# After full training (or in parallel with analysis):
python run.py --eval-baseline --show-progress
python run.py --eval-comparison --show-progress
```

### Build-only (skip unless you changed action space / actor code)

```powershell
python run.py --verify
python run.py --smoke --allow-cpu
```

## Artifacts

| Path | Purpose |
|------|---------|
| `results/verify.json` | Conversion checks A–G |
| `results/smoke.json` | Phase 1 smoke |
| `results/arm_kpis/{arm}.json` | Stage A screen arms |
| `results/screen_summary.json` | Screen winner |
| `results/stage_b_summary.json` | Stage B curriculum |
| `results/eval_baseline.json` | 5-seed baseline score |
| `results/eval_comparison.json` | Baseline vs treatment |
| `results/artifacts/warmup_preview/` | Standalone warmup MP4 + latent/applied reward PNG |
| `results/artifacts/screen/{arm}/` | Per-arm artifacts when using `--export-artifacts` |

## Predecessors

- Exp 8 (`ml_mpo_decoupled_dual_torque`) — MPO learner shell
- Exp 4 — vector OBC / baseline overflight warmup pattern
