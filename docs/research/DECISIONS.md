# Research & experiment decisions

Living log of **what we chose, rejected, or deferred** and why. Prevents scope creep and duplicate work.

**Rule:** Before proposing a new experiment or architecture fork, read this file. To **reverse** a decision, append a new row (do not delete old rows).

| Status | Meaning |
|--------|---------|
| **accepted** | Current plan or promoted choice |
| **rejected** | Considered; not pursuing unless user reverses |
| **deferred** | Plausible later; blocked by priority or missing prerequisite |
| **superseded** | Replaced by a newer decision (link new row) |

---

## Decision log

| ID | Date | Status | Topic | Decision | Rationale | Evidence / links |
|----|------|--------|-------|----------|-----------|------------------|
| D-001 | 2026-06 | rejected | MPC pointing experiment | Retire standalone MPC pointing slug | Replaced by agent-reference pointing (PD OBC, not QP/MPC); lower scope | [sac_vs_mpo_compare plan](../../.cursor/plans/sac_vs_mpo_compare_821ab4d5.plan.md) |
| D-002 | 2026-06 | accepted | Compare dt profile | Fixed **1.5 s / 1.5 s** sim + controller interval for ML compare arms | H0 dt sweep winner; single profile for fair SAC vs MPO | [STATUS_2026-06.md](../ml/experiments/STATUS_2026-06.md) |
| D-003 | 2026-06 | accepted | Hypothesis runs | Production `backend/autonomous_control/`, `simulation/`, `render/` **read-only** until promote | Isolated experiment folders; avoid prod drift | Experiment SUBAGENT_CHARTER pattern |
| D-004 | 2026-06 | accepted | ML pipeline order | Run shutter → encoder → SAC vs MPO → agent-reference **in sequence** | Each exp gates the next; no parallel matrix until prior closeout | [STATUS_2026-06.md](../ml/experiments/STATUS_2026-06.md) |
| D-005 | 2026-06 | **superseded** | MPO width ablation | Do **not** lead with `num_units_actor/critic` sweep | Superseded by [D-018](DECISIONS.md) Exp 5 closeout — width ruled out | [model-size-investigation.md](model-size-investigation.md); Exp 5 |
| D-006 | 2026-06 | accepted | Encoder before width | Test **modular encoder** (A0 vs A1) before raw MLP width tuning | Entity-based + Gorishniy + SRL survey: structure before capacity | [model-size-investigation.md](model-size-investigation.md); `ml_modular_encoder` |
| D-007 | 2026-06 | rejected | Lighter dense reward variant | No “latent-only” dense fork; use **`dense`** (H6 formula) only | H6 tested 10× applied; did not alone unblock learning | H6 analysis; plan dense rename |
| D-008 | 2026-06 | deferred | Quantitative abstract claims | Report stays **qualitative** until final matched baseline vs MPO metrics frozen | User direction; avoid stale numbers | [report-direction-log.md](../report/semester-project/report-direction-log.md) |
| D-009 | 2026-06-29 | rejected | Shutter threshold 0.5 → 0.9 (H1) | Do **not** rely on raising `DEFAULT_SHUTTER_THRESHOLD` to fix MPO shutter spam | `mpo_t09`: mean 514.9 vs 515 cmds/ep; fire@0.9 99.8%; policy saturates `shutter_gym≈+1`; no `learning_mode` | [shutter-threshold-investigation.md](shutter-threshold-investigation.md); `ml_shutter_threshold/results/shutter_threshold_summary.json` |
| D-010 | 2026-06-29 | rejected | 15 s capture-credit window alone | Do **not** expect sparse MPO + window fork alone to unblock learning | Latent bursts visible; applied capture ~0; returns flat −101.6; `shutter_meaningful_fraction=0` | Same investigation note; t05/t09 run dirs |
| D-011 | 2026-06-29 | accepted | Exp 1 closeout | **Exp 1 done** — pipeline proceeds to **Exp 2** (modular encoder) and **Exp 3** (SAC vs MPO) | H1 tested both arms at dt 1.5 s; hypothesis not supported | [STATUS_2026-06.md](../ml/experiments/STATUS_2026-06.md) closeout |
| D-012 | 2026-06-29 | accepted | Pipeline compute mutex | At most **one** ML pipeline training process per host | Experiments are GPU-heavy; parallel slugs risk OOM and confound monitoring | `backend/scripts/experiments/pipeline_run_guard.py`; [pipeline README](../experiments/pipeline/README.md) |
| D-013 | 2026-06-29 | deferred | Training-run video export | **Improve MP4 encode perf** — videos remain **required behavioral evidence**; trim only when user opts in | Export slow / async lag; KPI JSON insufficient for pointing/shutter/learning claims; frame-inspect + user MP4 review per [experiment-visual-evidence](../../.cursor/rules/experiment-visual-evidence.mdc) | [pipeline README](../experiments/pipeline/README.md) § Platform issues; `training_workflow.py`, `training_run_artifacts.py`, `backend/render/` |
| D-014 | 2026-06-29 | accepted | Exp 2 encoder closeout | **H1 not supported** — `CompressedControllerEncoder` (A1) **no meaningful benefit** vs flat A0 in SAC sparse 7-ep | Both `learning_mode=false`; A1 worse eval; q_loss diverges; stop rule — no split-head encoder | [02-modular-encoder.md](../experiments/pipeline/4-documentation/02-modular-encoder.md); unblocks Exp 5 width per [D-006](model-size-investigation.md) |
| D-015 | 2026-06-29 | **superseded** | Modular encoder — deferred high interest | Was: revisit A0 vs A1 when `learning_mode` achieved — **done in Exp 6** ([D-027](DECISIONS.md)) | v1 not_supported in non-learnable slice | [06-modular-encoder-r2.md](../experiments/pipeline/4-documentation/06-modular-encoder-r2.md) |
| D-016 | 2026-06-30 | accepted | Exp 4 vector OBC v1 | Promote **hold-last** nadir-relative pointing (`f_n = max_safe·u`, `max_safe = 45°`) to `simulation/obc_pointing_request.py`; invalidate pre-fix ref1 runs | Torque-passthrough warmup was invalid science; shared limit with torque-path hard stop | [04-agent-reference-pointing.md](../experiments/pipeline/4-documentation/04-agent-reference-pointing.md); `backend/tests/test_obc_pointing_request.py` |
| D-017 | 2026-06-30 | accepted | Exp 3 SAC vs MPO closeout | **SAC sparse learns** at dt 1.5 s; **MPO dense does not** sustain learning; dense raises floor vs H6 but plateaus −51.6 with KL blow-up | Fair algorithm×reward compare; H3a+H3c supported | [03-sac-mpo-compare.md](../experiments/pipeline/4-documentation/03-sac-mpo-compare.md); [sac-mpo-compare-investigation.md](sac-mpo-compare-investigation.md) |
| D-018 | 2026-06-30 | rejected | MPO width ablation (Exp 5) | **Do not** pursue S/M/L head width as next MPO lever | Identical −51.6 plateau across 90/140 → 256/512; KL freeze — capacity ruled out (H5d) | [05-mpo-model-size.md](../experiments/pipeline/4-documentation/05-mpo-model-size.md); [mpo-model-size-investigation.md](mpo-model-size-investigation.md) |
| D-019 | 2026-06-30 | accepted | Exp 4 H4 closeout | **Partial** — vector OBC valid; both arms learn; **ref1 eval below ref0** on KPI slice; video shows promising pointing + sparse shutter scheduling (train ep 11) | H4a not met; behavioral signal warrants ASC follow-up on reward/budget | [04-agent-reference-pointing.md](../experiments/pipeline/4-documentation/04-agent-reference-pointing.md); [agent-reference-pointing-investigation.md](agent-reference-pointing-investigation.md) |
| D-020 | 2026-06-30 | accepted | Shutter cmd when budget ≤ 0 | Charter **Exp 7** (`ml_sac_vector_budget_penalty`) — SAC vector + budget-exhausted shutter penalty fork | User video Exp 4 ref1 ep 11; end spam after budget zero | [07-sac-vector-budget-penalty.md](../experiments/pipeline/4-documentation/07-sac-vector-budget-penalty.md) |
| D-022 | 2026-06-30 | accepted | Exp 7 H7 closeout | **Supported** — budget-exhausted shutter penalty improves eval (+10.6 vs −24.1 Ref1), cuts shutter spam (−93% train cmds), preserves meaningful captures; **promote** penalty to production kernel (default on) | Treatment `9998217172220712_ml_sac_vector_budget_13-56-17` vs Ref1 baseline | [07-sac-vector-budget-penalty.md](../experiments/pipeline/4-documentation/07-sac-vector-budget-penalty.md); [sac_vector_budget_analysis.md](../../backend/scripts/experiments/ml_sac_vector_budget_penalty/results/sac_vector_budget_analysis.md) |
| D-021 | 2026-06-30 | **superseded** | Exp 6 encoder r2 | **Defer** charter vs Exp 7 priority (archive) — overnight run already completed same day | Low priority vs budget-penalty path; closeout postponed | [superseded by D-027](DECISIONS.md) |
| D-027 | 2026-07-23 | accepted | Exp 6 encoder r2 closeout | **Supported** — structured target-array encoding (bearing/mask \(50\to 8\)) beats flat concat on return (eval +80.9 vs −3.9); **no production promote**; not baseline win; no video artifacts | Overnight `ml_modular_encoder_r2` KPIs; Exp 2 null was protocol-limited | [06-modular-encoder-r2.md](../experiments/pipeline/4-documentation/06-modular-encoder-r2.md); [modular-encoder-r2-investigation.md](modular-encoder-r2-investigation.md) |
| D-023 | 2026-06-30 | accepted | MPO KL = symptom; charter Exp 8 | KL/η blow-up is a **symptom** of an unconstrained M-step; charter **Exp 8** to test decoupled-KL dual | Pre-fix traces; SAC learns same sparse reward (D-017) | [mpo-learning-collapse-investigation.md](mpo-learning-collapse-investigation.md); [08-mpo-decoupled-dual-fix.md](../experiments/pipeline/4-documentation/08-mpo-decoupled-dual-fix.md) |
| D-024 | 2026-06-30 | accepted | Exp 8 H8 closeout | **Partial** — decoupled-KL dual **unblocks MPO learning** (KL bounded, `learning_mode=true`); mission KPIs still poor (eval −81, saturation ~0.95); **no further prod promote** (fix already merged `d5af20c`) | `9998217164480175_ml_mpo_decoupled_dual_torque_sparse_16-05-19` | [08-mpo-decoupled-dual-fix.md](../experiments/pipeline/4-documentation/08-mpo-decoupled-dual-fix.md); [mpo_torque_analysis.md](../../backend/scripts/experiments/ml_mpo_decoupled_dual_torque/results/mpo_torque_analysis.md) |
| D-025 | 2026-06-30 | accepted | Exp 9 SAC shutter split closeout | **Supported** — `enable_shutter_waste_penalty=false` + budget-exhausted **on** beats Exp 7 eval (+106 vs +10.6); **promote** nb08 default waste-off to match production `RewardConfig` | `9998217165798903_ml_sac_shutter_split_15-43-20` vs Exp 7 | [09-sac-shutter-reward-split.md](../experiments/pipeline/4-documentation/09-sac-shutter-reward-split.md); [sac_shutter_reward_split_analysis.md](../../backend/scripts/experiments/ml_sac_shutter_reward_split/results/sac_shutter_reward_split_analysis.md) |
| D-026 | 2026-07-10 | accepted | Exp 15 charter — episode seed diversity | Charter **Exp 15** (`ml_mpo_episode_seed_diversity`): per-episode `derive_seed` env redraw + paired baseline/treatment on identical cloud scenarios; **defer** richer cloud-condition knobs to a follow-up slug (Exp 16) | Atomic split vs cloud-diversity track; smallest diversity lever on Exp 14 scaffold | [15-mpo-episode-seed-diversity.md](../experiments/pipeline/0-initialized/15-mpo-episode-seed-diversity.md) |

---

## How to append a row

```markdown
| D-00N | YYYY-MM-DD | accepted/rejected/deferred | Short topic | One-line decision | Why | paths, JSON, investigation note |
```

After append: if the decision closes an investigation thread, update the relevant `*-investigation.md` **Decisions** section and STATUS board if pipeline order changed.
