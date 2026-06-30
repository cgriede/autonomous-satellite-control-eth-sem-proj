---
experiment_id: 6
slug: ml_modular_encoder_r2
title: "Exp 6 — Modular encoder (r2)"
current_phase: 0
overall_verdict: deferred
blocked_by: null
code_path: backend/scripts/experiments/ml_modular_encoder_r2/
phases:
  "0": { status: cancelled, documented_utc: "2026-06-29T20:00:00Z", completed_utc: null, notes: "Deferred — archived; low priority vs Exp 7 reward/path work" }
  "1": { status: pending, documented_utc: null, completed_utc: null }
  "2": { status: pending, documented_utc: null, completed_utc: null }
  "3": { status: pending, documented_utc: null, completed_utc: null }
  "4": { status: pending, documented_utc: null, completed_utc: null }
run_lock_holder: null
decision_ids: [D-006, D-015]
predecessor: ml_modular_encoder
---

# Exp 6 — Modular encoder r2 (`ml_modular_encoder_r2`)

> **Status: deferred / archived** — not scheduled. Encoder A0 vs A1 retest deprioritized after Exp 5 width ruled out and Exp 4 vector+reward path showed more value ([D-021](../../research/DECISIONS.md), [D-015](../../research/DECISIONS.md)).

**Agent:** SAC · **dt:** 1.5 s / 1.5 s · **Train:** TBD (≥7; match learnable slice from Exp 3/5)  
**Plan:** [sac_vs_mpo_compare plan](../../../../.cursor/plans/sac_vs_mpo_compare_821ab4d5.plan.md) · **Predecessor:** [02-modular-encoder.md](../4-documentation/02-modular-encoder.md) (Exp 2 v1)  
**Investigation:** [model-size-investigation.md](../../research/model-size-investigation.md)  
**Blocked by:** ~~Exp 5~~ — **unblocked** after Exp 5 closeout (2026-06-30)  
**Priority:** [D-015](../../research/DECISIONS.md) — **high deferred interest** once `learning_mode` exists elsewhere in the stack

---

## Phase 0 — Initialized

### 0.1 Experiment scope (What)

**Core question:** Re-test **SAC flat vs vector-compress encoder** (same delta as Exp 2 v1) once the pipeline has a **learnable MPO reference** from width sizing — or a documented verdict that capacity is not the bottleneck.

**Hypothesis (H2r):**

> With reward / training protocol aligned to the best learnable regime from Exp 3 + Exp 5, **A1** (`CompressedControllerEncoder`, `vector_embed_dim=8`) beats **A0** (production flat `ControllerEncoder`) on `learning_mode` and eval return.

| Claim | Success criterion | Falsified if |
|-------|-------------------|--------------|
| **H2ra** | A1 `learning_mode` **true** while A0 false, or A1 eval return ↑ ≥ **10%** vs A0 | Both false / flat; A0 ≥ A1 |
| **H2rb** | A1 best train return **>** A0 | A0 best train ≥ A1 |
| **H2rc** | A1 improves vs A0 on `shutter_meaningful_fraction` or lower spam at equal return | No secondary KPI gap |

**Arms** (unchanged from Exp 2 v1):

| Arm | Encoder | Notes |
|-----|---------|-------|
| `sac_a0` | Flat / production `ControllerEncoder` | Baseline |
| `sac_a1` | `CompressedControllerEncoder` (`k=8`) | Single encoder delta |

**Frozen until Phase 1 build** (pick from Exp 3/5 closeout — do not guess now):

| Knob | v1 (Exp 2) | r2 default intent |
|------|------------|-----------------|
| Reward mode | sparse | **Match Exp 3 SAC arm** if `learning_mode`; else **dense** if Exp 5 M/L learns |
| `train_episodes` | 7 | **≥7**; extend only if Exp 5 uses longer slice with signal |
| dt | 1.5 / 1.5 | unchanged [D-002] |
| Warmup | 5 ep, rebuild per arm | unchanged |

**Stop rule:** Same as Exp 2 — no split-head / wider encoder arms without `learning_mode` on A1.

**Gates before Phase 2 run:**

- [x] Exp 2 v1 evaluation ([D-014](../../research/DECISIONS.md)) — [02-modular-encoder.md](../4-documentation/02-modular-encoder.md)
- [ ] Exp 3 closeout — SAC vs MPO verdict + reward mode for SAC path
- [ ] **Exp 5 closeout** — MPO S/M/L width ablation; record whether any arm achieves `learning_mode` or stable KL
- [ ] r2 reward mode + train length **frozen in DECISIONS** (or Phase 1.1)

**Out of scope:** MPO arms, encoder width sweep, shutter threshold (Exp 1 closed).

### 0.2 Thought process (Why)

| Prior fact (Exp 2 v1) | Implication for r2 |
|------------------------|-------------------|
| Both SAC arms `learning_mode=false`; returns **worsen** after ep 0; **q_loss** explodes | v1 sparse slice may be **non-learnable** for SAC — not a clean encoder test |
| A1 **worse** eval than A0 (−86.5 vs −78.9) despite **fewer** eval shutters | Compress encoder did not help; rerun only meaningful in a learnable regime |
| `shutter_meaningful_fraction=0` on all arms | Encoder test needs a protocol where capture credit is observable |
| SAC **~40%** shutter rate vs MPO **~100%** | SAC behavior differs; encoder question is separate from spam |

**Deferred high interest ([D-015](../../research/DECISIONS.md)):** v1 verdict is `not_supported`, but **if the stack ever reaches `learning_mode=true`**, group compressors on bearing/mask are **highly interesting** — structured 105-D obs, literature support, and A1’s lower eval shutter rate are worth retesting once reward/credit/algorithm are fixed. Exp 6 is chartered for that gate, not because v1 showed a win.

**Why after Exp 5 (MPO sizing):**

- [D-006](../../research/DECISIONS.md): encoder before width — **v1 satisfied**; width ablation (Exp 5) answers “is MLP capacity the bottleneck?”
- If Exp 5 **M/L learns** on dense (or chosen reward), r2 reruns encoder comparison under that **known-good** SAC-compatible protocol.
- If Exp 5 **all widths collapse** (H5d), r2 still runs SAC encoder A0 vs A1 with Exp 3 reward choice — tests structure when capacity is ruled out.

**Reject / defer:**

| Path | Status | Why |
|------|--------|-----|
| Encoder r2 before Exp 5 | **blocked** | User charter — wait for MPO sizing |
| Split-head encoder | deferred | Exp 2 stop rule |
| Re-run v1 sparse 7-ep only | rejected | Already inconclusive; r2 must change protocol per gates |

#### 0.2.1 Shoulders of giants

- Exp 2 v1 record: [02-modular-encoder.md](../4-documentation/02-modular-encoder.md) · `results/modular_encoder_summary.json`
- [model-size-investigation.md](../../research/model-size-investigation.md) — encoder vs width ordering
- Same literature as Exp 2 §0.2.1 (entity-based RL, Gorishniy embeddings, MERL fusion)
- Exp 5 width refs: MPO 2018 appendix; [05-mpo-model-size.md](05-mpo-model-size.md)

### 0.3 Preliminary implementation remarks (How)

**Scaffold:** Copy **`ml_modular_encoder/`** → `ml_modular_encoder_r2/` (or subcommand on same runner with `--protocol r2` — pick one in Phase 1; prefer **separate folder** for JSON contract clarity).

**Single delta vs v1:** reward fork mode + train episode count from Exp 3/5 gate table; encoder arms unchanged.

| Component | Planned path |
|-----------|--------------|
| Runner | `run_modular_encoder_r2.py` (or extend v1 with `--profile r2`) |
| Encoders / agents | Reuse `encoders/`, `encoder_agents/` from v1 |
| Results | `results/modular_encoder_r2_summary.json`, `modular_encoder_r2_analysis.md` |

**Smoke:** `--smoke` on `sac_a1` with **r2 reward profile** applied; one `train()` step.

**Risks:** Exp 5 inconclusive → r2 still runnable but may repeat v1 null result; document as H2r inconclusive not encoder falsified.

**Follow-up if inconclusive:** Close encoder line; promote Exp 4 agent-reference or production SAC sparse with documented non-learnability.

*(Skills)* [`hypothesis-experiment-cycle`](../../../.cursor/skills/hypothesis-experiment-cycle/SKILL.md) § ponytail rule; [`experiment-knowledge-pipeline`](../../../.cursor/skills/experiment-knowledge-pipeline/SKILL.md) Phase 1 build.

---

## Pipeline next step

1. Finish **Exp 2** Phases 2–4 (document run → verdict → closeout).  
2. Run **Exp 3** → freeze SAC reward mode for r2.  
3. Run **Exp 5** → MPO sizing closeout (**unblocks r2**).  
4. `/close-experiment-step` Phase 0 here when 0.1–0.3 approved → Phase 1 build (`ml_modular_encoder_r2/`).
