# Analysis — sac_vector_budget_penalty (Exp 7)

**Pipeline closeout:** [07-sac-vector-budget-penalty.md](../../../../docs/experiments/pipeline/4-documentation/07-sac-vector-budget-penalty.md)  
**Source JSON:** `results/sac_vector_budget.json`  
**Baseline (read-only):** Exp 4 Ref1 `9998217182442815_ml_ref_ref1_vector_11-05-57`

## Hypothesis

SAC sparse + vector OBC + **budget-exhausted shutter penalty** improves eval return vs Exp 4 Ref1, cuts post-budget shutter spam, and preserves mid-episode capture scheduling.

## Verdict table

| Claim | Criterion | penalty_on | Ref1 baseline | **Verdict** |
|-------|-----------|------------|---------------|-------------|
| **H7a** | Post-budget shutter cmds ↓ ≥30% vs Ref1 | train cmds **478** (−93% vs 7071); proxy — formal `post_budget_shutter_cmds_total` null (replay pending) | train cmds **7071** | **Supported** (proxy) |
| **H7b** | Eval ≥ −24.08 or learning_mode + ↑ best train | eval **+10.58**; best train **+124.57** | eval **−24.08**; best **+95.77** | **Supported** |
| **H7c** | Mid-ep meaningful shutter fraction not worse | train **0.220**; eval **0.400** | train **0.015**; eval **0.012** | **Supported** |
| **H7d** | Post-peak train return std ↓ | after ep 42: std **17.5**, mean **+3.3** (n=7) | after ep 11: std **28.4**, mean **−53.5** (n=38) | **Supported** |

**Overall H7: supported** — penalty_on meets gate (H7a proxy + H7b + H7c).

## Arms (summary JSON)

```json
{
  "penalty_on": {
    "learning_mode": true,
    "eval_return_mean": 10.581257604467492,
    "post_budget_shutter_cmds_total": null,
    "run_dir": "D:\\code\\sem-proj-asc\\backend\\autonomous_control\\runs\\9998217172220712_ml_sac_vector_budget_13-56-17",
    "finalized_from_crash": true
  },
  "baseline_ref1": {
    "eval_return_mean": -24.08097393950901,
    "train_shutter_cmd_count": 7071,
    "train_meaningful_fraction": 0.01513223023617593
  }
}
```

## Video / frame evidence

| Clip | Path | Agent pre-check |
|------|------|-----------------|
| Eval best | `...\videos\eval_ep_0_rank1.mp4` | Mid-orbit reward bursts ~200–500 s; end nadir coast — no shutter spam on reward trace |
| Train best (ep 42) | `...\videos\train_ep_42_rank1.mp4` | Same sparse window; return +124.6 |
| Frame manifests | `.cursor/video_frame_inspect/data/eval_ep_0_rank1_20260630T150624Z/manifest.json`, `.../train_ep_42_rank1_20260630T150758Z/manifest.json` | Operator sign-off pending |

## Mechanism

Penalty applies `−k_shutter_waste` (`REWARD_SHUTTER_WASTE_PENALTY = 5.0`) on shutter commands when `budget.remaining ≤ 0` (experiment fork patches `SimulationStepper.apply_shutter_capture`). Distinct from production `enable_shutter_waste_penalty` (zero-applied-capture within budget).

## Follow-up

- **Promote** fork logic to production `reward.py` / `stepper.py` (default on) — not merged at closeout.
- **Replay finalize** with `replay_train_for_shutter_stats=True` to lock H7a formal counter.
