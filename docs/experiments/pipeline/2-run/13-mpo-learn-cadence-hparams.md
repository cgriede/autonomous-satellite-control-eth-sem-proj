---
experiment_id: 13
slug: ml_mpo_learn_cadence_hparams
title: "Exp 13 — MPO learn cadence + untouched hyperparams"
current_phase: 2
overall_verdict: pending
blocked_by: null
code_path: backend/scripts/experiments/ml_mpo_learn_cadence_hparams/
predecessor: ml_mpo_decoupled_dual_torque
phases:
  "0": { status: done, documented_utc: "2026-06-30T22:00:00Z", completed_utc: "2026-06-30T21:41:09Z" }
  "1": { status: done, documented_utc: "2026-06-30T21:45:00Z", completed_utc: "2026-06-30T21:43:15Z" }
  "2": { status: in_progress, documented_utc: null, completed_utc: null }
  "3": { status: pending, documented_utc: null, completed_utc: null }
  "4": { status: pending, documented_utc: null, completed_utc: null }
run_lock_holder: null
decision_ids: []
---

# Exp 13 — MPO learn cadence + untouched hyperparams (`ml_mpo_learn_cadence_hparams`)

**Agent:** MPO (decoupled-KL dual, Exp 8 protocol) · **Action:** torque · **Reward:** sparse · **dt:** 1.5 s / 1.5 s (frozen)  
**Predecessor:** [Exp 8](../4-documentation/08-mpo-decoupled-dual-fix.md) (working MPO baseline); [Exp 5](../4-documentation/05-mpo-model-size.md) (width closed — not primary axis here)  
**Infra reuse:** `backend/scripts/experiments/train_timing/` (single-episode timing + duty-cycle sweep)

---

## Phase 0 — Initialized

### 0.1 Experiment scope (What)

**Core question (two tracks, one experiment):**

1. **Track A — Learn cadence:** Can we batch MPO `train()` calls relative to controller stores (and optionally controller interval) to cut wall time **without** changing learning outcomes?
2. **Track B — Untouched hyperparams:** Which **non-architecture** MPO knobs (LRs, KL/temperature, batch, samples) move eval/train KPIs on the **cadence winner** from Track A?

**Operator ratio notation** — **sim : collect : learn** (three relative frequencies):

| Slot | Meaning | Code knob |
|------|---------|-----------|
| **sim (1×)** | Physics integration step | `sim_dt_s` = **1.5 s** (frozen, H0 winner) |
| **collect (ap)** | Agent issues a new command **and** `store()` runs | `controller_interval_s` = ratio × 1.5 s |
| **learn (tr)** | Every **tr** collect events, open the learn gate and run **tr** `train()` calls (each samples `batch_size` transitions from replay — not a new stacked-obs architecture) | `train_every_n_steps` = **tr**, `updates_per_step` = **tr** |

**Agent vs low-level (this repo):** In train/eval the **learned agent is the pilot** — `get_action` + `store` only when `stepper.should_update_controller()` is true (`episode_runner.py`). **Simulation still steps every `sim_dt_s`**; between pilot ticks the last command is **held** (zero-order hold on torque / pointing). Attitude safety may override torque any step. There is no separate OBC loop issuing different commands every sim step in torque mode; vector mode resolves pointing→torque every sim step from the **last** pilot pointing command.

**Cadence arms** (canonical mapping — operator-confirmed 2026-06-30):

| Label | Ratio | `sim_dt_s` | `controller_interval_s` | `train_every_n_steps` | `updates_per_step` | Stores/ep† | Train updates/ep‡ |
|-------|-------|------------|-------------------------|----------------------|-------------------|------------|-------------------|
| **baseline_1_1_1** | 1:1:1 | 1.5 | 1.5 | 1 | 1 | ~516 | ~516 |
| **cadence_1_1_10** | 1:1:10 | 1.5 | 1.5 | 10 | 10 | ~516 | ~516 |
| **cadence_1_1_50** | 1:1:50 | 1.5 | 1.5 | 50 | 50 | ~516 | ~516 |
| **cadence_1_2_4** | 1:2:4 | 1.5 | **3.0** | 4 | 4 | ~258 | ~256 |

†Controller stores = sim steps ÷ `controller_interval_steps` (rounded integer multiple via `scheduler.resolve_controller_interval_steps`).  
‡`floor(stores / train_every_n_steps) × updates_per_step`.

**Interpretation:** `1:1:10` = collect every 1.5 s, learn every **10×1.5 s = 15 s** with **10** gradient bursts at that gate (same total updates as baseline, different scheduling). `1:2:4` = collect every **3 s**, learn every **4×3 s = 12 s** with **4** bursts — **also halves store count** (slower pilot), so total updates ≈ **half** baseline; treat as a distinct MDP + throughput arm, not matched-duty to `1:1:1`.

**Matched-duty controls** (same total gradient steps as baseline at **1.5 s** controller — isolates scheduling only):

| Label | Ratio | `train_every_n_steps` | `updates_per_step` | Total updates ≈ |
|-------|-------|----------------------|-------------------|-----------------|
| **duty_10x10** | 1:1:10 sched | 10 | 10 | ~516 |
| **duty_100x100** | 1:1:100 sched | 100 | 100 | ~516 |

**Track A claims**

| ID | Claim | Success criterion | Falsified if |
|----|-------|-------------------|--------------|
| **H13a** | Faster cadence, same learning | Among parity-passing arms, pick **lowest wall_s** for 50-train run | All fast arms collapse (KL→0, flat returns) while baseline learns |
| **H13b** | Batched learn preserves KPI | `1:1:10` / `1:1:50` match baseline eval within ≤5% at equal train ep **and** lower wall | Speedup only from fewer updates (`train_every`≫`updates`) with large return gap |
| **H13c** | Matched duty ≈ baseline | `10×10` / `100×100` within noise of `1:1:1` on eval | Matched duty diverges >10% eval return with same update count |

**Track B — hyperparam axes (untouched or single-point in pipeline so far)**

| Axis | Default (`MPOConfig`) | Proposed sweep (coarse) | Rationale |
|------|----------------------|-------------------------|-----------|
| **learning_rate_pi** | 1.5e-4 | {5e-5, 1.5e-4, 4.5e-4} | Exp 5 raised LRs ad hoc; no grid |
| **learning_rate_q** | 4.5e-4 | {1.5e-4, 4.5e-4, 1e-3} | Critic often 3× actor in literature |
| **learning_rate_eta** | 1e-3 | {3e-4, 1e-3, 3e-3} | Dual temperature step size |
| **target_kl_mu / target_kl_sigma** | 0.1 / 0.01 | {0.05, 0.1, 0.2} × {0.005, 0.01, 0.02} | MPO “temperature” / trust region — fixed in Exp 8 |
| **batch_size** | 256 | {128, 256, 512} | Affects train wall time + gradient noise |
| **num_samples_q / num_samples_pi** | 80 / 40 | {40/20, 80/40, 120/60} | MPO-specific compute vs variance |
| ~~buffer_size~~ | 50_000 | **frozen** | ~516 stores/ep × 50 ep ≪ capacity; unlikely lever |
| ~~gamma / tau~~ | 0.99 / 0.005 | **frozen** | Credit-horizon semantics — defer |
| ~~width (actor/critic units)~~ | 90 / 140 | **frozen** | Exp 5 closed; optional **cross-check** on winning LR only if Track B shows sensitivity |

**Track B design:** **staged fractional sweep** on cadence winner — not full Cartesian product.

- **Stage B0 (screen):** one-at-a-time ±1 step from default on each axis above (7 arms + default = 8 configs), 10 train ep, eval 2.
- **Stage B1 (refine):** 2×2 on the 1–2 axes that moved eval most in B0; 50 train ep.

**Track B claims**

| ID | Claim | Success criterion |
|----|-------|-------------------|
| **H13d** | Some untouched hparam moves KPI | ≥1 B0 arm beats default eval return by ≥5% **or** same return with ≥10% lower wall |
| **H13e** | Width not required | Best B1 config does not require width change vs Exp 5 null result |

**Frozen protocol** (all arms unless noted):

| Knob | Value |
|------|-------|
| dt | 1.5 s / 1.5 s |
| seed | 7 |
| warmup | 5 (rebuild per arm) |
| train | 50 (Track A parity screen may use 10 ep first) |
| eval | 2 |
| reward | sparse (Exp 8) |
| action | torque |
| MPO dual | decoupled KL (Exp 8) |
| videos | 3 train + 2 eval (trim only with `--trim-artifacts` on screen arms) |

**Primary metrics:** `summary_metrics.json` eval/train best return, `learning_mode`, KL stats, **`wall_s` / `steps_per_s`**, `n_train_updates`, timing breakdown (`episode_timing` categories).

**Gate:** `pipeline_run_guard.check_pipeline_run_clear(slug="ml_mpo_learn_cadence_hparams")` before Phase 2. Soft preference: after Exp 10–12 runs complete (mutex + stable MPO comparator).

**Out of scope:** SAC arms; dense reward; vector mode; changing `sim_dt_s` (H0 closed at 1.5 s); production promotion until Phase 4.

### 0.2 Thought process (Why)

| Prior | Implication |
|-------|-------------|
| [Exp 5](../4-documentation/05-mpo-model-size.md) | Width not the bottleneck — sweep **optimization / trust-region** knobs instead |
| [Exp 8](../4-documentation/08-mpo-decoupled-dual-fix.md) | Decoupled dual is the working MPO baseline — freeze architecture, vary cadence + hparams |
| `train_timing/` duty probes | `duty_100x1`: ~71 steps/s vs baseline ~13 steps/s but **5** train updates — pure stride wins speed, loses learning; burst variants untested end-to-end |
| [D-012](../../research/DECISIONS.md) | Sequential arms only — cadence screen (~8 arms × 1 ep) then short train, then B0/B1 |
| [machine-learning.md](../../presentation/machine-learning.md) § Training loop | Documents `train_every_n_steps` / `updates_per_step`; cadence does not change mission physics |
| Exp 10 charter | Explicitly deferred “hparam grid” to this experiment |

**Defer / reject**

- **buffer_size:** replay rarely fills; changing it adds cache invalidation noise without expected signal.
- **Full grid on width × LR:** Exp 5 + operator note — cross-correlation possible but **second-order**; only B1 spot-check if LR axis wins.
- **Controller interval change (`1:2:4`):** halves pilot decisions — different MDP; compare on its own merits (throughput + learning), not as matched-duty to `1:1:1`.

#### 0.2.1 Shoulders of giants

- **Abdolmaleki et al. 2018 (MPO)** — robustness to hyperparameters when dual/KL constraints are correct; motivates KL + LR axes over width.
- **SAC/MPO replay cadence** — common practice: multiple gradient steps per env step; our `updates_per_step` is the direct knob ([`environment-hyperparameters.md`](../../presentation/environment-hyperparameters.md)).
- **Prior art in repo:** `train_timing/run_duty_cycle_compare.py` — micro-benchmark; this experiment adds **full-episode learning parity** and hparam sweep on the winner.

### 0.3 Preliminary implementation remarks (How)

**Feasibility:** High — fork from Exp 8 runner + `train_timing/_fixtures.py` pattern; no production edits required ([D-003](../../research/DECISIONS.md)).

**Hook points**

| Component | Path |
|-----------|------|
| Cadence knobs | `TrainingWorkflowConfig.train_every_n_steps`, `updates_per_step` |
| Controller interval arm | `ml_algo_overnight/_sim_constants_fork.py` `apply_dt_profile` (only for `cadence_1_2_4`) |
| MPO hparams | `MPOConfig` replace in experiment `_frozen.py` |
| Timing | `episode_timing.EpisodeTimingCollector` via `train_timing/_profile_runner.py` |
| Mutex | `_run_guard.py` → `acquire_pipeline_run_lock` |

**Execution order (Phase 2)**

1. **A0 — Micro timing:** extend `train_timing` variants with `cadence_1_1_10`, `cadence_1_1_50`, `cadence_1_2_4` (+ matched duties); 1 train ep each; record JSON.
2. **A1 — Learning parity:** top 3–4 by steps/s → 10 train ep + eval; drop arms with KL freeze or >10% eval gap vs baseline.
3. **A2 — Confirm winner:** 50 train ep on cadence winner + baseline (2 arms).
4. **B0 — Hparam OAT screen:** 8 configs on winner cadence.
5. **B1 — Refine:** 2–4 arms, 50 train ep.

**Smoke:** 1 warmup + 1 train ep on `baseline_1_1_1` and `cadence_1_1_10`; assert `n_train_updates` matches table and run completes.

**Risks**

| Risk | Mitigation |
|------|------------|
| `1:1:50` OOM / runaway wall time | Cap burst at 50 only in A0; drop arm if single-ep wall >3× baseline |
| Hparam combinatorial explosion | Staged B0/B1 only; no full factorial |
| `1:2:4` halves stores + updates | Document in Phase 2; do not expect eval parity with `1:1:1` — success = acceptable KPI at lower wall |
| False speed win (stride-only) | H13c matched-duty controls + learning KPI gate; reject arms where `updates_per_step` ≪ `train_every_n_steps` |

---

## Phase 1 — Built

### 1.1 Build plan (What)

**Single logical delta:** vary **learn cadence** (`TrainingWorkflowConfig.train_every_n_steps`, `updates_per_step`) and **pilot interval** (`controller_interval_s` for `1:2:4` only); optional **MPOConfig** replace for Track B — no reward, architecture, or production edits.

| Artifact | Path |
|----------|------|
| Entry | `backend/scripts/experiments/ml_mpo_learn_cadence_hparams/run_exp13.py` |
| Cadence arms | `_cadence_profiles.py` |
| Hparam arms (Track B) | `_hparam_profiles.py` |
| Runner | `_runner.py` |
| Frozen knobs | `profile.json`, `_profile_baseline.py` |
| dt fork | `_sim_constants_fork.py` (+ `DT_15_AP2` for ap=3 s) |
| Mutex | `_run_guard.py` → `pipeline_run_guard` |
| Charter / hypothesis | `SUBAGENT_CHARTER.md`, `H13-learn-cadence-hparams.md` |
| Summary JSON | `results/learn_cadence_hparams_summary.json` |
| Smoke JSON | `results/smoke.json` |
| Timing A0 | `results/timing_a0.json`, `results/timing_a0.md` |
| Analysis card (Phase 3) | `results/learn_cadence_hparams_analysis.md` *(scaffold at closeout)* |

**Scaffold source:** Exp 8 `ml_mpo_decoupled_dual_torque` (MPO decoupled-KL sparse torque @ dt 1.5 s).

### 1.2 Build implementation (How we forked)

**Built 2026-06-30** — Nike mode; fork-only under `ml_mpo_learn_cadence_hparams/`.

| Component | Implementation |
|-----------|----------------|
| Cadence hook | `frozen_training_config(..., train_every_n_steps=, updates_per_step=)` + `run_serial(..., train_updates_per_step=, train_every_n_steps=)` via `tw.run_training_workflow` |
| `1:2:4` dt | `DT_15_AP2` (`sim_dt_s=1.5`, `controller_interval_s=3.0`) via `_sim_constants_fork.apply_dt_profile` |
| MPO hparams | `dataclasses.replace(setup.mpo_config, **overrides)`; `--hparam-arm` selects `_hparam_profiles.HPARAM_SCREEN_ARMS` |
| Timing A0 | `run_timing_episode()` + `EpisodeTimingCollector` (same pattern as `train_timing/_profile_runner.py`) |
| Smoke | 1 warmup + 1 train ep per arm; asserts `n_train_updates > 0` |

**Smoke result** (`results/smoke.json`, 2026-06-30 ~21:40 UTC):

| Arm | `n_train_updates` | `steps/s` | Episode wall (s) | Run dir |
|-----|-------------------|-----------|------------------|---------|
| `baseline_1_1_1` | 516 | 13.0 | 39.7 | `d:\code\sem-proj-asc\backend\autonomous_control\runs\9998217144429519_ml_mpo_learn_cadence_smoke_21-39-29` |
| `cadence_1_1_10` | 510 | 13.5 | 38.1 | `d:\code\sem-proj-asc\backend\autonomous_control\runs\9998217144386260_ml_mpo_learn_cadence_smoke_21-40-13` |

Both arms: `passed: true`; update counts match charter table (510 ≈ floor(516/10)×10).

**Deviations from 1.1:** none. `duty_10x10` not a separate arm (identical knobs to `cadence_1_1_10`). Track B hparam arms defined but not smoke-tested (cadence winner unknown until Phase 2 A0/A1).

### 1.3 Run instructions (How to execute)

**Env:** `conda activate auto-sat` · repo root or experiment folder.

**Mutex (Phase 2 full trains):** one pipeline job per host — `pipeline_run_guard.check_pipeline_run_clear(slug="ml_mpo_learn_cadence_hparams")` before multi-ep arms. `--smoke` and `--timing-a0` are single-episode probes (still avoid overlapping with another pipeline lock holder).

```powershell
# Smoke (done)
python backend/scripts/experiments/ml_mpo_learn_cadence_hparams/run_exp13.py --smoke

# Track A0 — one timed train ep per cadence arm
python backend/scripts/experiments/ml_mpo_learn_cadence_hparams/run_exp13.py --timing-a0

# Single arm — full train (50 ep default)
python backend/scripts/experiments/ml_mpo_learn_cadence_hparams/run_exp13.py --arm baseline_1_1_1 --show-progress

# Parity screen — 10 ep, trim video
python backend/scripts/experiments/ml_mpo_learn_cadence_hparams/run_exp13.py --arm cadence_1_1_10 --train-episodes 10 --trim-artifacts --show-progress

# All cadence arms sequentially
python backend/scripts/experiments/ml_mpo_learn_cadence_hparams/run_exp13.py --show-progress

# Track B on baseline cadence (after A2 winner frozen in Phase 2 doc)
python backend/scripts/experiments/ml_mpo_learn_cadence_hparams/run_exp13.py --arm baseline_1_1_1 --hparam-arm hparam_lr_pi_high --train-episodes 10 --trim-artifacts
```

**Cadence arms (Track A):** `baseline_1_1_1`, `cadence_1_1_10`, `cadence_1_1_50`, `cadence_1_2_4`, `duty_100x100`.

**Expected artifacts per arm:** `results/<arm_id>.json`, `run_dir/config.json` (`experiment.arm_id`, cadence fields), `summary_metrics.json`, `plots/`, `videos/` (unless `--trim-artifacts`).

*(Phase blocks 2–4 appended by `/document-experiment-step`.)*
