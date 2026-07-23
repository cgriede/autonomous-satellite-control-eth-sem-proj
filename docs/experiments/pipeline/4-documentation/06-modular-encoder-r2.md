---
experiment_id: 6
slug: ml_modular_encoder_r2
title: "Exp 6 — Modular encoder (r2)"
current_phase: 4
overall_verdict: supported
blocked_by: null
code_path: backend/scripts/experiments/ml_modular_encoder_r2/
phases:
  "0": { status: done, documented_utc: "2026-06-29T20:00:00Z", completed_utc: "2026-06-30T03:30:00Z", notes: "Charter frozen; overnight ran despite interim D-021 defer vs Exp 7 priority" }
  "1": { status: done, documented_utc: "2026-07-23T01:40:00Z", completed_utc: "2026-06-29T22:50:53Z", notes: "Fork + smoke already on disk; Phase 1 documented retrospectively" }
  "2": { status: done, documented_utc: "2026-07-23T01:40:00Z", completed_utc: "2026-06-30T03:30:00Z", arms: [sac_a0, sac_a1], notes: "Overnight pipeline step exp6; Phase 2 documented retrospectively" }
  "3": { status: done, documented_utc: "2026-07-23T01:40:00Z", completed_utc: "2026-07-23T01:40:00Z" }
  "4": { status: done, documented_utc: "2026-07-23T01:40:00Z", completed_utc: "2026-07-23T01:40:00Z" }
run_lock_holder: null
decision_ids: [D-006, D-015, D-021, D-027]
predecessor: ml_modular_encoder
---

# Exp 6 — Modular encoder r2 (`ml_modular_encoder_r2`)

**Agent:** SAC · **dt:** 1.5 s / 1.5 s · **Train:** 50 episodes · **Seed:** 7  
**Predecessor:** [02-modular-encoder.md](02-modular-encoder.md) (Exp 2 v1)  
**Investigation:** [modular-encoder-r2-investigation.md](../../research/modular-encoder-r2-investigation.md)  
**Closeout:** 2026-07-23 (retrospective — overnight run 2026-06-30; charter had been archived under [D-021](../../research/DECISIONS.md))

**Plain question:** Does structured encoding of the **per-target bearing and capture-mask arrays** (not camera images) beat flat concatenation once SAC can learn?

---

## Phase 0 — Initialized

### 0.1 Experiment scope (What)

**Core question:** Re-test **SAC flat vs structured target-array encoding** (same delta as Exp 2 v1) once a learnable protocol exists.

**Hypothesis (H2r):**

> With reward / training protocol aligned to a learnable SAC sparse regime, **A1** (`CompressedControllerEncoder`, `vector_embed_dim=8` on each length-50 target array) beats **A0** (production flat `ControllerEncoder`) on `learning_mode` and eval return.

| Claim | Success criterion | Falsified if |
|-------|-------------------|--------------|
| **H2ra** | A1 `learning_mode` **true** while A0 false, or A1 eval return ↑ ≥ **10%** vs A0 | Both false / flat; A0 ≥ A1 |
| **H2rb** | A1 best train return **>** A0 | A0 best train ≥ A1 |
| **H2rc** | A1 improves vs A0 on `shutter_meaningful_fraction` or lower spam at equal return | No secondary KPI gap |

**Arms** (unchanged from Exp 2 v1):

| Arm | Encoder | Notes |
|-----|---------|-------|
| `sac_a0` | Flat / production `ControllerEncoder` | Baseline |
| `sac_a1` | `CompressedControllerEncoder` (`k=8`) | Embed each 50-D target array → 8-D; **not** image compression |

**Frozen protocol (as run):**

| Knob | Value |
|------|-------|
| Reward mode | sparse |
| `train_episodes` | 50 |
| dt | 1.5 / 1.5 |
| Warmup / eval | 5 / 2 |
| Action interface | torque (pre–vector default path) |

**Out of scope:** MPO arms, encoder width sweep, image/vision CNN changes, reward redesign.

### 0.2 Thought process (Why)

| Prior fact (Exp 2 v1) | Implication for r2 |
|------------------------|-------------------|
| Both SAC arms `learning_mode=false`; returns worsen; **q_loss** explodes | v1 sparse 7-ep slice may be **non-learnable** — not a clean encoder test |
| A1 worse eval than A0 | Compress did not help under that protocol |
| `shutter_meaningful_fraction=0` | Encoder test needs observable capture credit |

**Deferred high interest ([D-015](../../research/DECISIONS.md)):** Retest once `learning_mode` exists elsewhere. Exp 3 SAC sparse provided that gate; overnight pipeline then executed Exp 6 after Exp 5.

**Interim defer ([D-021](../../research/DECISIONS.md)):** Same day as the overnight completion, priority moved to Exp 7 (budget penalty). Charter was archived; compute had already finished. This closeout restores the science record.

#### 0.2.1 Shoulders of giants

- Same literature as Exp 2: entity-/set-structured observations; Gorishniy-style group embeddings on tabular groups; MERL-style multimodal fusion.
- Project: [model-size-investigation.md](../../research/model-size-investigation.md); Exp 2 closeout [02-modular-encoder.md](02-modular-encoder.md).

### 0.3 Preliminary implementation remarks (How)

**Scaffold:** `ml_modular_encoder/` → `ml_modular_encoder_r2/` (separate folder).  
**Single delta vs v1:** longer train (50 ep) + raised LRs from hparam grid; encoder arms unchanged.  
**Smoke:** `--smoke` on `sac_a1` — passed 2026-06-29 (`results/smoke.json`).

---

## Phase 1 — Built

### 1.1 Build plan (What)

**Single delta:** same as Exp 2 — `Linear(50 → 8)` on bearing and capture-mask arrays; passthrough globals + vision CNN unchanged. Protocol knobs only differ from v1.

| Component | Path |
|-----------|------|
| A1 encoder | `encoders/compressed_controller_encoder.py` |
| Scalar split | `encoders/scalar_split.py` |
| SAC modular agent | `encoder_agents/sac_modular_agent.py` |
| Runner | `run_modular_encoder_r2.py`, `_encoder_runner.py` |
| Hypothesis | `H2r-modular-encoder.md`, `SUBAGENT_CHARTER.md` |
| JSON / analysis | `results/modular_encoder_r2_summary.json`, `modular_encoder_r2_analysis.md` |

### 1.2 Build implementation (How we forked)

- Global mutex via `pipeline_run_guard` (`_run_guard.py`).
- A0: overnight `SACAgent` + production flat encoder.
- A1: `SACModularAgent` + structured target-array embeddings (`k=8`).
- **Smoke passed** (`results/smoke.json`, 2026-06-29T22:50:53Z): `passed: true`, warmup return **72.7**, buffer 516, `encoder_mode: compress`.

### 1.3 Run instructions (How to execute)

| Step | Command | Output |
|------|---------|--------|
| Smoke | `python .\run_modular_encoder_r2.py --smoke --allow-cpu --arms sac_a1` | `results/smoke.json` |
| Full | `python .\run_modular_encoder_r2.py --show-progress --arms sac_a0,sac_a1` | `results/modular_encoder_r2_summary.json` |

```powershell
conda activate auto-sat
cd backend/scripts/experiments/ml_modular_encoder_r2
python .\run_modular_encoder_r2.py --show-progress --arms sac_a0,sac_a1
```

**Mutex:** [D-012](../../research/DECISIONS.md) — one pipeline job per host.

---

## Phase 2 — Run

### 2.1 Run scope (What)

| Item | Value |
|------|-------|
| Orchestrator | `ml_pipeline_overnight` step `exp6` |
| Arms | `sac_a0` (flat), `sac_a1` (structured target encode, k=8) |
| dt | 1.5 s / 1.5 s |
| Reward | sparse |
| Warmup / train / eval | 5 / 50 / 2 |
| Seed | 7 |
| Completed UTC | 2026-06-30T03:30:00Z |

### 2.2 Run monitoring (Why)

- Sequential after Exp 5 close in overnight resume; child `run_modular_encoder_r2.py`.
- Agent discussion log: `sac_a0` done then `sac_a1`; pipeline completed 03:30 UTC.
- No abort; summary written.

### 2.3 Run log & artifacts (How)

**Summary:** `backend/scripts/experiments/ml_modular_encoder_r2/results/modular_encoder_r2_summary.json`  
**Analysis:** `backend/scripts/experiments/ml_modular_encoder_r2/modular_encoder_r2_analysis.md`

| Arm | Run dir | Warmup mean | Best train | Eval mean | `learning_mode` | Eval shutter cmds | Meaningful frac (eval) | Wall |
|-----|---------|-------------|------------|-----------|-----------------|-------------------|------------------------|------|
| **sac_a0** | `backend/autonomous_control/runs/9998217212521862_ml_encoder_r2_sac_a0_02-44-37/` | +393.2 | +11.2 | −3.9 | true | 358 | 0.011 | ~1287 s |
| **sac_a1** | `backend/autonomous_control/runs/9998217211235184_ml_encoder_r2_sac_a1_03-06-04/` | +393.2 | +137.2 | +80.9 | true | 298 | 0.034 | ~1436 s |

**Plots (both arms):** `plots/returns_by_episode.png`, `plots/learning_curves.png`, `plots/eval_episode_diagnostics.png`.

**Videos:** No MP4s retained under these run dirs (artifact gap — profile requested videos; overnight likely trimmed or encode failed). Phase 3 verdict is **KPI / learning-curve based**, not video-based. Platform note [D-013](../../research/DECISIONS.md).

---

## Phase 3 — Evaluation

### 3.1 Claims & success criteria (What)

| ID | Claim | Success bar |
|----|-------|-------------|
| **H2ra** | A1 learns better / higher eval than A0 | `learning_mode` or eval ↑ ≥ 10% vs A0 |
| **H2rb** | A1 best train > A0 | Best train A1 > A0 |
| **H2rc** | Secondary shutter KPIs | Meaningful frac ↑ or spam ↓ at equal return |

### 3.2 Evidence summary (Why)

- **Both arms learn** (`learning_mode=true`) under 50-ep SAC sparse torque — Exp 2’s null result was protocol-limited.
- **A1 clearly beats A0 on return:** eval +80.9 vs −3.9 (~21× relative lift vs A0’s negative eval); best train +137.2 vs +11.2.
- **Not a mission win:** both remain far below matched baseline +393.2; eval shutter spam remains high (hundreds of cmds/ep); meaningful shutter fractions stay low (1–3%).
- **Secondary KPIs:** A1 has fewer eval shutter cmds (298 vs 358) and higher meaningful fraction (0.034 vs 0.011) — weak but consistent with H2rc.
- **A1 critic:** `q_loss` mean ~852 on last train ep (elevated) — note instability risk; does not overturn the return gap.
- **Scope clarity:** delta is **target-array encoding** (bearing + mask), not fisheye/primary image compression.

### 3.3 Verdict table (How we decided)

| # | Claim | Criterion | sac_a0 | sac_a1 | **Verdict** |
|---|-------|-----------|--------|--------|-------------|
| H2ra | Learning / eval lift | `learning_mode` or eval ↑ | true, −3.9 | true, +80.9 | **Supported** |
| H2rb | Train return | A1 > A0 best train | +11.2 | +137.2 | **Supported** |
| H2rc | Secondary KPIs | Meaningful ↑ or spam ↓ | meaningful 0.011; 358 cmds | meaningful 0.034; 298 cmds | **Supported** (weak) |

**Overall verdict: `supported`** — structured encoding of per-target bearing/mask arrays beats flat concat on return under learnable SAC sparse torque.  
**Caveat:** does **not** imply baseline outperformance or selective budget-aware shuttering; those remain Exp 7/9 territory.

**Per-arm auto JSON verdict:** both `supported` (learning_mode gate) — science conclusion is **H2r supported for A1 vs A0**.

---

## Phase 4 — Documentation

### 4.1 Promotion & integration (What)

**No production promote** ([D-003](../../research/DECISIONS.md)):

| Component | Disposition |
|-----------|-------------|
| `CompressedControllerEncoder` / `encoder_agents/` | Stay in `ml_modular_encoder_r2/` (and Exp 2 fork) |
| Production `ControllerEncoder` | Unchanged unless a later promote decision |
| Target-array embedding pattern | Reusable; promote only if a production SAC stack needs it |

**Decision IDs:** [D-015](../../research/DECISIONS.md) (deferred interest resolved), [D-021](../../research/DECISIONS.md) (superseded), [D-027](../../research/DECISIONS.md) (this closeout).

### 4.2 Closeout rationale (Why)

**Verdict stands:** In a learnable 50-ep SAC sparse slice, embedding the length-50 bearing and capture-mask arrays (\(50\to 8\)) improves train/eval return vs flat concat. Exp 2’s `not_supported` was the wrong protocol for this question, not proof the idea is dead.

**Why D-021 deferred felt right at the time:** Exp 7 (budget penalty) was the higher-leverage path for selective shuttering; encoder structure helps sample efficiency, not the scheduling objective by itself.

**Do not** claim: image compression, baseline victory, or production-ready selective shuttering from Exp 6 alone.

### 4.3 Knowledge persistence (How)

| Layer | Path |
|-------|------|
| Pipeline closeout | This file (`4-documentation/06-modular-encoder-r2.md`) |
| Investigation | [modular-encoder-r2-investigation.md](../../research/modular-encoder-r2-investigation.md) |
| Analysis card | `backend/scripts/experiments/ml_modular_encoder_r2/modular_encoder_r2_analysis.md` |
| Summary JSON | `backend/scripts/experiments/ml_modular_encoder_r2/results/modular_encoder_r2_summary.json` |
| DECISIONS | [D-027](../../research/DECISIONS.md) |
| STATUS | [STATUS_2026-06.md](../../ml/experiments/STATUS_2026-06.md) |
| Run dirs | `…_ml_encoder_r2_sac_a0_02-44-37/`, `…_ml_encoder_r2_sac_a1_03-06-04/` |
| Report | Semester report Exp~6 in `sections/04_experiments.tex` + experiment comparison table |

**Artifact gap:** no eval/train MP4s in run dirs — do not use video claims for this closeout.
