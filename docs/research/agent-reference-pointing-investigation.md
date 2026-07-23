# Agent-reference pointing — investigation note

**Pipeline:** [Exp 4](../experiments/pipeline/4-documentation/04-agent-reference-pointing.md) (`ml_agent_reference_pointing`)  
**Closeout:** 2026-06-30 · **Overall verdict:** partial

---

## 1. Question

Does SAC sparse learn better mission behavior when dim0 commands a **nadir-relative orientation reference** (vector / OBC PD) vs direct **torque**?

## 2. Evidence (canonical run 2026-06-30)

| Arm | Eval | Best train | Video anchor |
|-----|------|------------|--------------|
| Ref0 torque | −11.13 | +8.37 | `.../9998217183842846_ml_ref_ref0_torque_10-42-36/videos/eval_best.mp4` |
| Ref1 vector | −24.08 | +95.77 | `.../9998217182442815_ml_ref_ref1_vector_11-05-57/videos/train_ep_11_rank1.mp4` |

JSON: `backend/scripts/experiments/ml_agent_reference_pointing/results/agent_reference.json`

## 3. User video findings (Ref1 train ep 11)

Operator-reviewed `train_ep_11_rank1.mp4` (return **+95.8**):

1. **Pointing works** — vector mode shows deliberate off-nadir scheduling mid-episode; behavior is qualitatively promising.
2. **Sparse shutters mid-episode** — SAC fires shutter commands relatively sparingly when geometry aligns; resembles **learning to schedule**, not constant spam.
3. **End-of-episode spam** — policy still commands shutters after capture budget is exhausted; does not respect the **fixed budget** as a hard constraint.
4. **Peak then collapse** — large train reward at ep 11 vs weaker later eps and eval (−24); hypotheses: learning rate, reward mis-shaping, local optimum, eval cloud draw.

## 4. Decisions

| ID | Status | Decision |
|----|--------|----------|
| [D-016](DECISIONS.md) | accepted | Vector OBC v1 promoted to production |
| [D-019](DECISIONS.md) | accepted | Exp 4 **partial** — vector valid; H4a eval win not shown |
| [D-020](DECISIONS.md) | accepted | Charter **Exp 7** — budget-exhausted shutter penalty |
| [D-022](DECISIONS.md) | accepted | Exp 7 **supported** — promote budget-exhausted penalty to production |

## 5. Rejected / deferred

| Path | Why |
|------|-----|
| Abandon vector mode on eval KPI alone | Video shows learnable pointing + scheduling signal |
| Ref2 MPO vector | Not run; separate charter |
| Torque-passthrough warmup runs | Invalid science — excluded |

## 6. Exp 7 results (budget-exhausted shutter penalty)

**Closeout:** 2026-06-30 · **Overall verdict:** supported · [07-sac-vector-budget-penalty.md](../experiments/pipeline/4-documentation/07-sac-vector-budget-penalty.md)

| Arm | Eval | Best train | Train shutter cmds | Meaningful frac |
|-----|------|------------|--------------------|-----------------|
| penalty_on | **+10.58** | **+124.57** (ep 42) | **478** | **0.220** |
| Ref1 baseline | −24.08 | +95.77 (ep 11) | 7071 | 0.015 |

Run: `backend/autonomous_control/runs/9998217172220712_ml_sac_vector_budget_13-56-17`  
Video: `...\videos\eval_best.mp4`, `...\videos\train_ep_42_rank1.mp4`  
JSON: `backend/scripts/experiments/ml_sac_vector_budget_penalty/results/sac_vector_budget.json`

**Finding:** Penalty removes end-of-episode shutter spam (video pre-check) while improving eval and meaningful capture rate vs Ref1. **Next:** promote fork to production `reward.py` / `stepper.py` ([D-022](DECISIONS.md)).

## 7. Next experiments (ASC)

- **Promote** budget-exhausted shutter penalty (post Exp 7 closeout)
- Diagnose eval–train gap (LR, replay, eval cloud draw) after promote
- Optional Ref2: MPO + vector + dense
- Exp 6 encoder r2 — **supported** ([D-027](DECISIONS.md); [06-modular-encoder-r2.md](../experiments/pipeline/4-documentation/06-modular-encoder-r2.md))

## 8. Artifacts index

- Exp 4 pipeline: `docs/experiments/pipeline/4-documentation/04-agent-reference-pointing.md`
- Exp 7 pipeline: `docs/experiments/pipeline/4-documentation/07-sac-vector-budget-penalty.md`
- Manifests: per-arm `artifacts_manifest.json` under run dirs above
