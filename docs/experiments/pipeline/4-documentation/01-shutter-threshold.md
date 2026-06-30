---
experiment_id: 1
slug: ml_shutter_threshold
title: "Exp 1 — Shutter threshold"
current_stage: closeout
overall_verdict: not_supported
blocked_by: null
code_path: backend/scripts/experiments/ml_shutter_threshold/
stages:
  charter:    { status: done, completed_utc: "2026-06-28T10:00:00Z" }
  literature: { status: done, completed_utc: "2026-06-28T11:00:00Z" }
  design:     { status: done, completed_utc: "2026-06-28T12:00:00Z" }
  implement:  { status: done, completed_utc: "2026-06-28T14:00:00Z" }
  run:        { status: done, completed_utc: "2026-06-29T15:30:00Z", arms: [mpo_t05, mpo_t09] }
  closeout:   { status: done, completed_utc: "2026-06-29T16:00:00Z" }
run_lock_holder: null
decision_ids: [D-009, D-010, D-011]
---

# Exp 1 — Shutter threshold (`ml_shutter_threshold`)

**Agent:** MPO · **Reward:** sparse + **15 s** capture-credit window (experiment fork)  
**Closed:** 2026-06-29 · **Decision IDs:** [D-009](../../research/DECISIONS.md), [D-010](../../research/DECISIONS.md), [D-011](../../research/DECISIONS.md)  
**Deep dive:** [shutter-threshold-investigation.md](../../research/shutter-threshold-investigation.md)

---

## Charter

### Hypothesis (H1)

> Raising the shutter decision threshold from **0.5 → 0.9** reduces MPO shutter spam (~968 cmds/ep in overnight H1a) **and** improves learning when combined with a **15 s** sparse capture-credit window.

**Arms:** `mpo_t05` (threshold **0.5**) vs `mpo_t09` (threshold **0.9**) · dt **1.5 s / 1.5 s** · 7 train + 2 eval episodes.

**Gates:** Exp 0 dt profile fixed (D-002); production modules read-only (D-003).

---

## Literature

- MPO sparse credit assignment; overnight H1a shutter spam baseline (~968 cmds/ep).
- Literature basis in fork: `backend/scripts/experiments/ml_shutter_threshold/H1-shutter-threshold.md`
- Highlights: [LITERATURE_HIGHLIGHTS.md](../../research/LITERATURE_HIGHLIGHTS.md) (reward sparsity / action saturation context).

---

## Design

- Experiment slug: `backend/scripts/experiments/ml_shutter_threshold/`
- Forks: reward capture window, shutter threshold in runner spec, `_sim_constants_fork` for dt 1.5 s
- JSON contract: `results/shutter_threshold_summary.json`, per-arm `results/arm_kpis/*.json`
- Analysis card: `shutter_threshold_analysis.md`

---

## Implement

- Entrypoint: `run_shutter_threshold.py` → `_shutter_runner.py`
- Global pipeline mutex: `_run_guard.py` → `pipeline_run_guard.acquire_pipeline_run_lock`
- Smoke: `--smoke` arm before full matrix
- Artifact manifest: standard training workflow (eval/train videos, reward plots)

---

## Run

**Mutex:** Only one pipeline training job per host ([D-012](../../research/DECISIONS.md)); lock at `backend/scripts/experiments/.pipeline_run.lock`.

```powershell
conda activate auto-sat
cd D:\code\sem-proj-asc\backend\scripts\experiments\ml_shutter_threshold
python .\run_shutter_threshold.py --show-progress --arms mpo_t05,mpo_t09
```

| Arm | Valid run dir | Notes |
|-----|---------------|-------|
| `mpo_t05` | `backend/autonomous_control/runs/ml_shutter_mpo_t05_14-04-49` | Invalid: `ml_shutter_mpo_t05_11-12-19` (pre–dt-fix, 1936 steps) |
| `mpo_t09` | `backend/autonomous_control/runs/9998217254656575_ml_shutter_mpo_t09_15-02-22` | Videos + artifacts_manifest |

---

## Closeout

### Verdict — hypothesis claims

| # | Claim tested | Success criterion | `mpo_t05` (0.5) | `mpo_t09` (0.9) | **Verdict** |
|---|--------------|-------------------|-----------------|-----------------|-------------|
| **H1a** | Higher threshold **cuts shutter spam** vs 0.5 arm | Mean train cmds/ep **&lt; 50%** of t05 baseline (516) | **516.0** cmds/ep (516 every ep) | **514.9** cmds/ep (−0.2%); fire@0.9 **99.8%** of steps | **Rejected** |
| **H1b** | Spam reduction comes from policy **below** saturation, not threshold alone | `shutter_unit` distribution materially below 1.0 at 0.9 | (not re-sampled) | mean **0.999**, median **1.0**, `shutter_gym` mean **+0.999** | **Rejected** |
| **H1c** | 15 s window + threshold change **enables learning** | `learning_mode` **true** OR sustained eval return improvement | `learning_mode` **false**; eval **−101.6** | `learning_mode` **false**; eval **−101.6** | **Rejected** |
| **H1d** | Meaningful captures after training | `shutter_meaningful_fraction` **&gt; 0** | **0.0** | **0.0** | **Rejected** |

### Overall H1 verdict: **Not supported**

Threshold tuning is **not an effective lever** while MPO saturates the shutter action dimension. The capture window fires **mechanically** (mid-episode latent reward bursts) but does not fix credit assignment.

**Partial signal (not H1 success):** Late-episode torque is not constant max (torque penalty + training); video shows calmer applied RW torque after ~600 s — policy moves, mission does not.

### Results snapshot

| Arm | Threshold | Mean cmds/ep | Best train return | Eval return mean | `learning_mode` | Valid run dir |
|-----|-----------|--------------|-------------------|------------------|-----------------|---------------|
| `mpo_t05` | 0.5 | 516.0 | −99.87 | −101.6 | false | `backend/autonomous_control/runs/ml_shutter_mpo_t05_14-04-49` |
| `mpo_t09` | 0.9 | 514.9 | −99.90 | −101.6 | false | `backend/autonomous_control/runs/9998217254656575_ml_shutter_mpo_t09_15-02-22` |

---

## Artifacts

| Artifact | Path |
|----------|------|
| Summary JSON | `backend/scripts/experiments/ml_shutter_threshold/results/shutter_threshold_summary.json` |
| Analysis card | `backend/scripts/experiments/ml_shutter_threshold/shutter_threshold_analysis.md` |
| Plots | `backend/scripts/experiments/ml_shutter_threshold/results/plots/` |
| Per-arm KPI cache | `results/arm_kpis/mpo_t05.json`, `mpo_t09.json` |
| Hypothesis (fork) | `backend/scripts/experiments/ml_shutter_threshold/H1-shutter-threshold.md` |
| Re-finalize summary | `python _finalize_summary.py` in experiment folder |

---

## Mechanism (reference)

`shutter_unit = 0.5 × (clip(shutter_gym, −1, 1) + 1)` · fire when `shutter_unit > threshold`.

At **0.5**: any `shutter_gym > 0` fires. At **0.9**: need `shutter_gym > 0.8`. Policy trained to **≈ +1** on both arms → threshold barely matters.

---

## Pipeline next step

**Exp 2** — modular encoder (`ml_modular_encoder`) · **Exp 3** — SAC sparse vs MPO dense (unblocked).
