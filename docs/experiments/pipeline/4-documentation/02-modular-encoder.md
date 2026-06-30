---
experiment_id: 2
slug: ml_modular_encoder
title: "Exp 2 — Modular encoder"
current_phase: 4
overall_verdict: not_supported
blocked_by: null
code_path: backend/scripts/experiments/ml_modular_encoder/
phases:
  "0": { status: done, documented_utc: "2026-06-29T18:00:00Z", completed_utc: "2026-06-29T18:00:00Z" }
  "1": { status: done, documented_utc: "2026-06-29T18:00:00Z", completed_utc: "2026-06-29T17:05:00Z" }
  "2": { status: done, documented_utc: "2026-06-29T20:30:00Z", completed_utc: "2026-06-29T17:07:35Z", arms: [sac_a0, sac_a1] }
  "3": { status: done, documented_utc: "2026-06-29T20:30:00Z", completed_utc: "2026-06-29T21:00:00Z" }
  "4": { status: done, documented_utc: "2026-06-29T21:15:00Z", completed_utc: "2026-06-29T21:30:00Z" }
run_lock_holder: null
run_started_utc: "2026-06-29T16:34:58Z"
decision_ids: [D-006, D-013, D-014, D-015]
---

# Exp 2 — Modular encoder (`ml_modular_encoder`)

**Agent:** SAC sparse · **dt:** 1.5 s / 1.5 s · **Train:** 7 episodes  
**Evaluated:** 2026-06-29 · **Closed:** 2026-06-29 · **Decision IDs:** [D-006](../../research/DECISIONS.md), [D-014](../../research/DECISIONS.md), [D-015](../../research/DECISIONS.md)  
**Plan:** [sac_vs_mpo_compare plan](../../../../.cursor/plans/sac_vs_mpo_compare_821ab4d5.plan.md) · **Investigation:** [model-size-investigation.md](../../research/model-size-investigation.md)

---



## Phase 0 — Initialized



### 0.1 Experiment scope (What)



**Hypothesis (H1):** SAC sparse with **vector compressors** on per-target bearing/mask (arm **A1**) outperforms production flat `ControllerEncoder` (arm **A0**) on `learning_mode` and returns.



| Claim | Success criterion |

|-------|-------------------|

| **H1a** | A1 `learning_mode` **true** while A0 false, or A1 sustained eval return improvement |

| **H1b** | A1 best train return **>** A0 |

| **H1c** | A1 improves secondary KPIs vs A0 (`positive_reward_steps`, shutter meaningful fraction) |



**Arms:** `sac_a0` (flat / production encoder) vs `sac_a1` (compress, `vector_embed_dim=8`).



**Frozen protocol:** SAC sparse · dt **1.5 s / 1.5 s** · 7 train · 5 warmup (rebuild cache per arm) · 2 eval ([D-002](../../research/DECISIONS.md)).



**Stop rule:** No KPI gap after 7 eps → **do not** add split-head arms; report “flat MLP / concat not the bottleneck.”



**Gates:** [D-006](../../research/DECISIONS.md) — encoder before MPO width ablation; Exp 1 shutter threshold **not supported** (pipeline proceeds here).



### 0.2 Thought process (Why)



- Overnight MPO runs showed warmup OK then collapse; width ablation deferred ([D-005](../../research/DECISIONS.md)) — **structure before capacity**.

- Exp 1 rejected threshold + capture-window alone ([D-009](../../research/DECISIONS.md), [D-010](../../research/DECISIONS.md)); spam/latent reward may be **encoder + credit**, not shutter knob.

- Scalar observation is **105-D** with **50+50** ordered target bearing/mask fields — flattening may be sample-inefficient vs group compressors.

- SAC chosen as sole learner for this arm (MPO compare deferred to Exp 3).



#### 0.2.1 Shoulders of giants



- **Entity- / set-structured observations** — per-target fields; ordered slots (not full Deep Sets sum-pool): [compositional policy architectures](https://openreview.net/pdf/ceead8c5d2c73b2e871b5d6bddf870a3c404f75a.pdf), [entity-based RL survey](https://arxiv.org/html/2410.17647v3).

- **Multimodal fusion** — CNN vision + scalar streams → trunk MLP: [MERL](https://openreview.net/pdf/6c53a204af9367febb3d6fdad8ca87528ae40d9f.pdf).

- **Group bottleneck** — `Linear(50 → k)` on bearing/mask vs flat concat (lightweight; preserves slot order).

- Project synthesis: [model-size-investigation.md](../../research/model-size-investigation.md) · plan § Exp 2 literature.

- Fork doc: `backend/scripts/experiments/ml_modular_encoder/H1-modular-encoder.md`



### 0.3 Preliminary implementation remarks (How)



- **Hook:** swap agent after `build_training_workflow_setup` — encoder-only delta; training loop unchanged.

- **Scaffold:** copy overnight patterns (`_reward_fork`, `_sim_constants_fork`, `_runner_common` KPIs, `pipeline_run_guard`).

- **Smoke:** `run_modular_encoder.py --smoke` — 1 warmup ep, A1 `SACModularAgent`, buffer + one `train()` step.

- **Risks:** `agents` package name collision with overnight (resolved → `encoder_agents/`); SAC lr names must match `sac_agent_fork`.

- **Follow-up if inconclusive:** proceed to Exp 3 SAC vs MPO dense; do **not** widen encoder (split heads) without `learning_mode` on A1. **Deferred rerun:** [Exp 6](../0-initialized/06-modular-encoder-r2.md) after Exp 5 MPO sizing.



---



## Phase 1 — Built



### 1.1 Build plan (What)



**Single delta:** replace flat concat of bearing + mask vectors with **`Linear(n, k)`** compressors (`k=8`); passthrough globals + vision CNN unchanged.



| Component | Path |

|-----------|------|

| Scalar partition | `encoders/scalar_split.py` |

| A1 encoder | `encoders/compressed_controller_encoder.py` |

| SAC + modular actor/critic | `encoder_agents/sac_modular_agent.py`, `modular_actor.py`, `modular_critic.py` |

| A0 baseline | Overnight `sac_agent_fork.SACAgent` (production `ControllerEncoder`) |

| Runner | `run_modular_encoder.py`, `_encoder_runner.py` |

| dt / reward / baseline | `_encoder_sim.py`, `_frozen_baseline.py`, overnight forks |

| Charter / hypothesis | `SUBAGENT_CHARTER.md`, `H1-modular-encoder.md` |



**JSON contract:** `results/modular_encoder_summary.json` · **Analysis card:** `modular_encoder_analysis.md`



### 1.2 Build implementation (How we forked)



- Global mutex via `pipeline_run_guard` (`_run_guard.py`).

- A0: `importlib` load `ml_algo_overnight/agents/sac_agent_fork.py`.

- A1: `SACModularAgent` + `CompressedControllerEncoder` (passthrough + bearing/mask compress + vision fusion).

- **Smoke passed** (`results/smoke.json`): `passed: true`, warmup return **72.7**, 516 steps, buffer 516, `encoder_mode: compress`, `vector_embed_dim: 8`.

- **Deviations:** local package renamed `agents/` → `encoder_agents/`; `sys.path` order `reversed(_PATH_ROOTS)`; `SACModularAgent` uses `learning_rate_pi` / `learning_rate_q`.



### 1.3 Run instructions (How to execute)



**Mutex:** one pipeline job per host ([D-012](../../research/DECISIONS.md)) — `backend/scripts/experiments/.pipeline_run.lock`.



```powershell

conda activate auto-sat

cd D:\code\sem-proj-asc\backend\scripts\experiments\ml_modular_encoder

python .\run_modular_encoder.py --show-progress --arms sac_a0,sac_a1

```



| Flag | Purpose |

|------|---------|

| `--smoke --allow-cpu` | Quick A1 warmup + train step |

| `--vector-embed-dim 8` | A1 bottleneck (default) |

| `--train-episodes 7` | Fast slice (default) |



**Expected artifacts per arm:**



- `backend/autonomous_control/runs/ml_encoder_<arm>_<stamp>/` (train/eval, optional videos per training workflow)

- `results/modular_encoder_summary.json`, `modular_encoder_analysis.md`, `results/modular_encoder.log`

- After run: optional `video-frame-inspect` on eval MP4 → cite manifest in Phase **2.3**

- **Platform note ([D-013](../../research/DECISIONS.md)):** training-run video export is slow — default run uses trimmed eval video; full MP4 set needs `--full-artifacts` and may finish after KPIs. Frontend agent owns improvement.



---



## Phase 2 — Run



### 2.1 Run scope (What)



| Item | Value |

|------|-------|

| Command | `run_modular_encoder.py --show-progress --arms sac_a0,sac_a1` |

| Arms | `sac_a0` (flat), `sac_a1` (compress k=8) |

| dt | **1.5 s / 1.5 s** (`dt_profile.json`) |

| Reward | **sparse** |

| Warmup / train / eval | 5 / 7 / 2 |

| Completed UTC | 2026-06-29T17:07:35Z (`modular_encoder_summary.json`) |

| Exit code | 0 |



### 2.2 Run monitoring (Why)



- Sequential arms in one process (mutex [D-012](../../research/DECISIONS.md)); **sac_a0** then **sac_a1**.

- Wall time ~**987 s** (A0) + ~**970 s** (A1); videos encoded sync after each arm (~6 MP4s/arm).

- No run abort; dt guard lines logged per arm.



### 2.3 Run log & artifacts (How)



**Summary:** `results/modular_encoder_summary.json` · **Log:** `results/modular_encoder.log` · **Analysis:** `modular_encoder_analysis.md`



| Arm | Run dir | Eval mean | `learning_mode` | Train shutter cmds/ep (approx) | Eval shutter cmds/ep |

|-----|---------|-----------|-----------------|-------------------------------|----------------------|

| **sac_a0** | `autonomous_control/runs/9998217249101092_ml_encoder_sac_a0_16-34-58/` | −78.9 | false | ~236 | ~223 |

| **sac_a1** | `autonomous_control/runs/9998217248114377_ml_encoder_sac_a1_16-51-25/` | −86.5 | false | ~210 | ~98 |



**Plots:** `plots/returns_by_episode.png`, `plots/learning_curves.png` per run dir.



**Videos (eval):** `videos/eval_best.mp4`, `videos/eval_ep_0_rank1.mp4` (both arms).



**Learning signals (train ep 7):** A0 `q_loss≈1420`, `pi_loss≈−98`; A1 `q_loss≈3190`, `pi_loss≈−109` — critic divergence, returns worsen after ep 0.



**Shared diagnostics:** `shutter_meaningful_fraction=0` both arms (no applied capture credit above ε).



---



## Phase 3 — Evaluation



### 3.1 Claims & success criteria (What)



| ID | Claim | Success bar |

|----|-------|-------------|

| **H1a** | A1 learns better than A0 | A1 `learning_mode=true` or eval return ↑ vs A0 |

| **H1b** | A1 best train return > A0 | Best train −75.1 (A1) vs −72.4 (A0) |

| **H1c** | A1 secondary KPIs better | Meaningful shutter fraction or spam↓ at equal return |



### 3.2 Evidence summary (Why)



- **Neither arm learned** (`learning_mode=false`): train returns **degrade** from ep 0; SAC **q_loss explodes** (especially A1).

- **A1 worse than A0** on eval (−86.5 vs −78.9) despite **fewer** eval shutters (~98 vs ~223/ep) — selectivity without value.

- vs **MPO Exp 1** (~516 shutters/ep, return −101.6): SAC spams less and avoids collapse floor, but **encoder delta did not improve** SAC outcomes.

- **Zero meaningful captures** on both arms (same as Exp 1) — sparse 7-ep slice is a **weak test** of encoder benefit; stop rule still applies: no encoder widening.

- **Warmup identical** (+393 mean) — post-warmup failure is policy/credit, not mission seed.



### 3.3 Verdict table (How we decided)



| # | Claim | Criterion | sac_a0 | sac_a1 | **Verdict** |

|---|-------|-----------|--------|--------|-------------|

| H1a | Learning / eval lift | `learning_mode` or eval ↑ | false, −78.9 | false, −86.5 | **Rejected** |

| H1b | Train return | A1 > A0 best train | −72.4 best | −75.1 best | **Rejected** |

| H1c | Secondary KPIs | Meaningful shutter or spam↓ @ equal return | meaningful=0 | meaningful=0; fewer shutters but worse return | **Rejected** |



**Overall verdict: `not_supported`** — vector compress encoder (**A1**) shows **no meaningful benefit** vs flat (**A0**); flat concat / group bottleneck is **not** the limiting lever in this SAC sparse slice.



**Per-arm JSON verdict:** `inconclusive` (pipeline KPI gate) — science conclusion is **H1 not supported**.



**Follow-up:** [Exp 3](../../1-built/03-sac-mpo-compare.md) (algorithm/reward); [Exp 6](../0-initialized/06-modular-encoder-r2.md) (encoder rerun after Exp 5 learnable protocol). **Do not** add split-head encoder arms.

**Deferred interest ([D-015](../../research/DECISIONS.md)):** If the stack ever reaches **`learning_mode=true`**, group compressors on bearing/mask remain **highly interesting** — v1 cannot test that fairly today.

---

## Phase 4 — Documentation

### 4.1 Promotion & integration (What)

**No production promote** ([D-003](../../research/DECISIONS.md)):

| Component | Disposition |
|-----------|-------------|
| `CompressedControllerEncoder` / `encoder_agents/` | Stays in `ml_modular_encoder/` fork only |
| Production `ControllerEncoder` | Unchanged — flat concat remains baseline |
| `encoders/scalar_split.py` | Reusable pattern; not merged until learnable rerun |

**Reusable for later experiments:** fork runner, encoder swap hook, JSON + analysis card contract.

**Decision IDs:** [D-006](../../research/DECISIONS.md) (encoder-before-width gate satisfied), [D-014](../../research/DECISIONS.md) (H1 not supported v1), [D-015](../../research/DECISIONS.md) (deferred high interest).

### 4.2 Closeout rationale (Why)

**Verdict stands:** H1 **not supported** in the SAC sparse 7-ep slice — A1 did not beat A0; neither arm learned; `shutter_meaningful_fraction=0`.

**Deferred high interest:** Once **reward / credit assignment / algorithm** produce a learnable policy (`learning_mode=true`, stable critic, meaningful captures), **vector compressors on ordered target slots** could be **very helpful**:

- Observation is **105-D** with **50+50** structured bearing/mask fields — flattening may be sample-inefficient at scale.
- A1 already showed **lower eval shutter rate** than A0 (~98 vs ~223 cmds/ep) in v1 — a hint of different action structure worth retesting **only when learning is real**, not under q_loss blow-up.
- Literature + [model-size-investigation.md](../../research/model-size-investigation.md) motivation unchanged; v1 failure is **protocol-limited**, not proof the idea is dead.

**Do not** interpret v1 as “never use compressors” — interpret as **“not the current bottleneck.”**

**Follow-up:** [Exp 3](../../1-built/03-sac-mpo-compare.md) → [Exp 5](05-mpo-model-size.md) → [Exp 6](../0-initialized/06-modular-encoder-r2.md) (encoder r2 in learnable regime).

### 4.3 Knowledge persistence (How)

| Layer | Path |
|-------|------|
| Pipeline closeout | This file (`4-documentation/02-modular-encoder.md`) |
| Analysis card | `backend/scripts/experiments/ml_modular_encoder/modular_encoder_analysis.md` |
| Summary JSON | `backend/scripts/experiments/ml_modular_encoder/results/modular_encoder_summary.json` |
| DECISIONS | [D-014](../../research/DECISIONS.md), [D-015](../../research/DECISIONS.md) |
| STATUS | [STATUS_2026-06.md](../../ml/experiments/STATUS_2026-06.md) |
| Deferred rerun charter | [06-modular-encoder-r2.md](../0-initialized/06-modular-encoder-r2.md) |
| Run dirs | `…_ml_encoder_sac_a0_16-34-58/`, `…_ml_encoder_sac_a1_16-51-25/` |

**Pipeline next:** **Exp 3** SAC vs MPO (mutex free).
