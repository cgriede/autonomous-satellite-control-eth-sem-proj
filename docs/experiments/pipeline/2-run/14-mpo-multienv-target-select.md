---
experiment_id: 14
slug: ml_mpo_multienv_target_select
title: "Exp 14 — Multi-env MPO target selection + mission score"
current_phase: 2
overall_verdict: pending
blocked_by: null
code_path: backend/scripts/experiments/ml_mpo_multienv_target_select/
predecessor: ml_mpo_decoupled_dual_torque
phases:
  "0": { status: done, documented_utc: "2026-07-02T12:00:00Z", completed_utc: "2026-07-02T16:40:07Z" }
  "1": { status: done, documented_utc: "2026-07-02T19:34:00Z", completed_utc: "2026-07-02T19:34:00Z", notes: "4 bugs fixed by review-experiment-build gate before advancing to Phase 2" }
  "2": { status: done, documented_utc: null, completed_utc: "2026-07-02T19:36:03Z"
  "3": { status: pending, documented_utc: null, completed_utc: null }
  "4": { status: pending, documented_utc: null, completed_utc: null }
run_lock_holder: null
decision_ids: []---
# Exp 14 — Multi-env MPO target selection + mission score (`ml_mpo_multienv_target_select`)

**Agent:** MPO (decoupled-KL dual, Exp 8 protocol) · **Action:** factored target (50) + move + shutter · **Low-level:** PD OBC (move-gated) · **dt:** 1.5 s / 1.5 s (frozen)  
**Predecessor:** [Exp 8](../4-documentation/08-mpo-decoupled-dual-fix.md) (working MPO learner); [Exp 4](../4-documentation/04-agent-reference-pointing.md) (vector OBC / PD path)  
**Design conversation:** [2026-07-02-exp14-discrete-categorical-action-gpt55.md](../../research-conversations/2026-07-02-exp14-discrete-categorical-action-gpt55.md)  
**Operator feedback (bugs & miscommunications):** [14-mpo-multienv-target-select-user-feedback.md](./14-mpo-multienv-target-select-user-feedback.md)

---

## Phase 0 — Initialized

### 0.1 Experiment scope (What)

**Core question:** Can we beat baseline on **mission image performance** by training MPO as a **planning-oriented target selector** (not a torque pilot), with **multi-environment diversity** and a **reported mission score** decoupled from the training reward?

**Radical deltas vs pipeline so far (Exp 1–13):**

| Axis | Prior pipeline default | Exp 14 |
|------|------------------------|--------|
| Optimization target | Episode **return** (reward) | Primary KPI = **mission score** (reward is training signal only) |
| Action space | Continuous torque or scalar `u` vector | **Factorized:** `Categorical(50)` target + 2 bool dims (move, shutter) via shifted tanh |
| Low-level control | Learned pilot competes with safety | **PD OBC** toward latched target when `move=True`; coast when `move=False` |
| Environment | Fixed `build_setup(seed=7)` per arm | **Curriculum:** sample `N` distinct env setups via `build_baseline_overflight_setup` |
| Eval | Same seed family as train | **Unseen env seeds only** |

**Mission score (reported KPI, unitless):**

**Per episode** (one unseen env, one rollout):

```text
score_ep = Σ_over_applied_captures (image_quality × primary_target_pixel_coverage)
```

Equivalent to summing `quality × coverage` at shutter steps where the capture budget accepts a novel target (`simulation/capture_reward.py`, `SimulationStateSeries` per-step `primary_camera_image_quality` + observation-line codes).

**Aggregated cohort score** (baseline and treatment — **primary comparison metric**):

```text
score_mean = mean(score_ep over 5 eval envs)
score_std  = std(score_ep over 5 eval envs)   # report for luck / cloud-luck illustration
```

We **always** compare **means over the same 5 held-out env seeds**, not a single lucky or unlucky run. Cloud fields differ per seed; averaging across 5 unseen envs gives a fair baseline for EO performance under variable occlusion. Per-episode scores are still logged so we can show variance — how bad or lucky one run can be when strategy is effectively “hope for clear skies.”

Score is **not** the RL return; log **both** `mission_score_*` and `eval_return` in KPI JSON.

**Training reward (shaping only):**

```text
reward = α·score_gain + β·successful_capture_bonus − γ·missed_opportunity − δ·instability_penalty − ε·torque_penalty
```

Starting weights (fork defaults, tunable in Phase 1):

| Symbol | Value | Note |
|--------|-------|------|
| α | 1.0 | ties reward to score deltas |
| β | 0.5 | bonus on budget-eligible capture |
| γ | 0.2 | opportunity cost when good target visible but not selected |
| δ | 0.1 | attitude / safe-mode instability |
| ε | 0.01 | torque effort — **must stay small** so PD path is not re-learned |

**Action space (frozen contract — factorized, orthogonal dims):**

Same pattern as production MPO (`POLICY_RAW_DIM=2` torque+shutter): **one distribution per action dimension**, shared encoder trunk; **not** one softmax over all outputs. Target, move, and shutter are **mutually composable** each controller tick.

| Dim | Type | Policy output | Env / OBC semantics |
|-----|------|---------------|---------------------|
| **target** | `Categorical(n_targets)` | 50 logits → softmax **over targets only** | Latched navball index `i ∈ {0…49}`; updates selected ground target |
| **move** | bool (continuous head) | Gaussian → tanh → `[-1,1]` → threshold (`action_adapter` shutter pattern) | **`move=True`:** engage PD toward latched target `i`. **`move=False`:** **zero RW torque** — coast (not KSP-style hold) |
| **shutter** | bool (continuous head) | same shifted-tanh + threshold as today `dim 1` | Fire capture when above threshold; independent of move |

* `n_targets` = **50** (frozen; `BASELINE_N_TARGETS`).
* **Train:** sample target from `Categorical`; sample move/shutter from their Gaussians (or threshold logits); **eval:** `argmax` target, threshold move/shutter.
* **MPO log-prob:** `log π_target + log π_move + log π_shutter` (factorized; cross-correlation via shared trunk — same as current 2D Gaussian actor).
* **Forbidden:** single `Categorical(52)` or `n_targets+1` mutex head (target and shutter must not compete).

Operator model: set target on navball → pulse **move** to slew → release to coast → **shutter** when ready ([research conversation](../../research-conversations/2026-07-02-exp14-discrete-categorical-action-gpt55.md) — historical GPT note used single categorical; **superseded** by this contract).

**Multi-environment training protocol (full run — after hparam screen):**

| Parameter | Value |
|-----------|-------|
| Env count `N` | **10** (distinct env draws) |
| Per-env warmup | **5** episodes (rebuild cache) |
| Per-env train | **30** episodes |
| **Total train episodes** | **350** (`10 × (5 + 30)`) |

Applies only to the **winning hparam config** from the preliminary screen below — not during the 5×20 ep screen.

**Per-env setup entrypoint:** `s01_utils.baseline_overflight.build_baseline_overflight_setup(mission_seed, cloud_seed)` — 50-target grid + seeded `cloud_formation_generator` along the target corridor (not bare `build_setup`, which only randomizes altitude and uses static `S01_CLOUDS`).

**Held fixed every env:**

| Knob | Value | Rationale |
|------|-------|-----------|
| `sim_dt_s` / `controller_interval_s` | 1.5 s / 1.5 s | H0 winner; not part of this hypothesis |
| `n_targets` | **50** | Categorical action dim fixed; grid geometry unchanged |
| Target stripe layout | `BASELINE_*` meridian grid | Same mission structure; only scene/orbit vary |
| Lighting model | *(none)* | No lighting randomization in sim — do not claim it |

**Sampled per env** — prioritize knobs **already implemented** in `baseline_overflight.py` / `cloud_formation.py`:

| Draw | Mechanism | Exp 14 bounds | Baseline today |
|------|-----------|---------------|----------------|
| **Orbit altitude** | `sample_satellite_altitude(seed=mission_seed)` inside `build_setup` | unchanged altitude envelope | same |
| **Cloud count** | `cloud_number_bounds` → `cloud_formation_generator` | **`(20, 40)`** | `(15, 30)` (~25 typical) |
| **Cloud along-track placement** | integer start + extent along formation path (`cloud_range_bounds`, path fractions) | **`(1, 80) km`** extent | same |
| **Cloud vertical placement** | `cloud_base_altitude_bounds` + `cloud_thickness_bounds` | **base `(4, 12) km`**, thickness `(1, 16) km`, top cap 20 km | same |
| **Initial body attitude** | `OrbitConfig.sat_z_offset` → `sat_z_offset_deg` at resolve | sample per env (hook exists; fork wires range in Phase 1) | fixed 0° nadir |

**Seeds per env:** `mission_seed` (altitude) and `cloud_seed` (entire cloud field draw) — derive both from `env_index` via `derive_seed(base, "exp14_env", i)` so train/eval sets stay disjoint and reproducible.

**Explicitly not sampled (no built hook / out of scope):**

| Item | Note |
|------|------|
| Lighting / sun angle | Not modeled |
| Target count or grid spacing | Frozen at 50 × 15 km / 40 km spacing |
| Independent orbit φ window | `start_angle_deg` / `end_angle_deg` inferred from target placement + LOS margin at resolve — moves with fixed grid, not a separate RNG axis |
| Initial wheel spin | `body_initial_omega_rad_s` exists in low-level kinematic config but is **not** on `EnvironmentSetup` today — defer unless wired in Phase 1 |

**Operator rationale (orbit height):** sampling degraded orbits keeps the selector valid when altitude drifts over mission life ([`docs/raw_thoughts/simplify-drag`](../../raw_thoughts/simplify-drag)).

**Evaluation protocol (unseen envs only):**

| Cohort | Env seeds | Episodes | Agent |
|--------|-----------|----------|-------|
| Baseline | 5 fresh held-out seeds | 1 episode per seed | PD baseline overflight (no learned policy) |
| Treatment | **same** 5 seeds | 1 episode per seed | Trained MPO target selector |

**Scoring contract (mandatory):**

| Metric | Definition |
|--------|------------|
| `score_ep[i]` | Mission score for env seed `i` (formula above) |
| **`score_mean`** | **Arithmetic mean of `score_ep` over all 5 eval envs** — this is the baseline reference and the treatment comparator |
| `score_std` / `score_min` / `score_max` | Dispersion across the 5 envs — illustrate cloud luck vs robust strategy |
| `Δscore_mean` | `score_mean_treatment − score_mean_baseline` on the **identical** seed list |

Do **not** pick the best single env or best single episode for the verdict. Optional plots: per-seed bar chart (baseline vs treatment) + error bars from `score_std`.

Also report (secondary): mean reward, images captured, mean quality, mean coverage — aggregated the same way (mean over 5 envs). Checkpoint selection by **best eval `score_mean`**, not best eval return or best single run.

**Why mean over 5:** each eval seed draws a different cloud field; one run can be anomalously good or bad under occlusion. Averaging matches the operational question — does the selector beat the scripted baseline **on average** across diverse EO conditions, not on one lucky pass?

**Training phases (two-stage):**

| Stage | Purpose | Train ep budget | Env sampling |
|-------|---------|-----------------|--------------|
| **A — Hparam screen** | Integration smoke + “is it learning?” (non-random actions) | **5 configs × 20 train = 100** | **Single fixed train env** (`mission_seed=7`, `cloud_seed=7`) — isolate optimizer, not generalization |
| **B — Full run** | Mission hypothesis (H14a–b) | **350** (multi-env curriculum above) | **10 train envs** + **5 held-out eval envs** |

Pick **one winner** from Stage A, freeze its `MPOConfig` (+ `entropy_coef`), then launch Stage B only if the screen passes.

**Stage A — preliminary hparam screen (max 5 configs, 100 train ep)**

Inspired by [Exp 13 Track B](../2-run/13-mpo-learn-cadence-hparams.md) (MPO LR / batch / trust-region axes; staged screen not full factorial) and [`ml_sac_hparam_grid`](../../../backend/scripts/experiments/ml_sac_hparam_grid/README.md) (short train-per-arm, pick winner, then commit) — Exp 13 Track B has **not executed** yet; borrow the **axis list**, not its cadence arms.

| Arm | `learning_rate_pi` | `learning_rate_q` | `batch_size` | `entropy_coef` | Notes |
|-----|-------------------|-------------------|--------------|----------------|-------|
| **hp_default** | 1.5e-4 | 4.5e-4 | 256 | 0.01 | Exp 8 decoupled-KL baseline |
| **hp_conservative** | 5e-5 | 1.5e-4 | 256 | 0.01 | Low LR (Exp 13 B0 low end) |
| **hp_mid_batch** | 1.5e-4 | 4.5e-4 | 512 | 0.01 | Default LRs, larger batch |
| **hp_aggressive** | 4.5e-4 | 1e-3 | 512 | 0.02 | Raised LRs (SAC hparam grid pattern) |
| **hp_explore** | 1.5e-4 | 4.5e-4 | 256 | 0.05 | Higher entropy for categorical exploration |

**Screen protocol (all 5 arms):**

| Knob | Screen value |
|------|----------------|
| Warmup | **5** ep (rebuild per arm) |
| Train | **20** ep |
| Eval | **1** ep on **one** held-out seed (quick sanity — not the 5-seed verdict) |
| Env | Fixed `build_baseline_overflight_setup(mission_seed=7, cloud_seed=7)` |
| Videos | `--trim-artifacts` OK |
| Mutex | One arm at a time ([D-012](../../research/DECISIONS.md)) |

**Screen pass gates (must hit before Stage B):**

| Gate | Criterion |
|------|-----------|
| Plumbing | Run completes; discrete actor + OBC routing + `score_ep` logged |
| Learning signal | `learning_mode=true` **or** monotonic train-return improvement ep 5→20 |
| Non-random policy | Eval action entropy > 0.5 bits **or** ≥3 distinct argmax targets across eval; not collapsed to single action from ep 1 |

**Screen winner selection:** rank arms by **train return at ep 20**; tie-break with eval return then policy entropy. Document all 5 in Phase 2; **only the winner** gets Stage B budget.

**Stage B — full multi-env run:** winning hparam arm only; 350 train ep curriculum; full **5-seed** eval + `score_mean` verdict per scoring contract above.

**Claims**

| ID | Claim | Success criterion | Falsified if |
|----|-------|-------------------|--------------|
| **H14a** | Multi-env training generalizes | Treatment **`score_mean`** (mean over 5 unseen eval envs) beats baseline **`score_mean`** by ≥10% on best arm | All arms `score_mean` ≤ baseline with matched eval seeds |
| **H14b** | Target-selection beats torque MPO on mission KPI | Best arm `score_mean` > Exp 8 torque sparse `score_mean` on same 5-seed eval set (Phase 3 comparator) | `score_mean` gain only on train seeds (memorization) |
| **H14c** | Score–reward decoupling helps reporting | Training return and mission score rank arms differently ≤1 arm; primary verdict uses **score** only | N/A (process claim — document both metrics) |
| **H14d** | Factored policy learns | Screen pass gates met; Stage B shows `learning_mode=true` + non-trivial target / move / shutter use in eval videos | KL collapse or frozen target+never-move from ep 1 |
| **H14e** | Hparam screen yields a viable config | ≥1 of 5 screen arms passes all Stage A gates | All 5 arms fail gates → fix fork before Stage B |

**Frozen protocol (unless noted in arm table):**

| Knob | Value |
|------|-------|
| `sim_dt_s` / `controller_interval_s` | 1.5 s / 1.5 s |
| `n_targets` | **50** (frozen) |
| MPO dual | decoupled KL (Exp 8) |
| Reward credit mode | sparse shutter applied + shaping terms above |
| Attitude path | OBC PD toward latched target when `move=True`; coast when `move=False` |
| Warmup | 5 ep per env segment (full run); 5 ep per screen arm |
| Videos | Full run: 3 train + 2 eval per arm; screen: `--trim-artifacts` OK ([experiment-visual-evidence](../../../.cursor/rules/experiment-visual-evidence.mdc)) |

**Out of scope:** SAC arms; production promotion before Phase 4; re-tuning `sim_dt_s`; learning low-level torque (explicitly deferred — PD + safety model already exist).

**Gate:** `pipeline_run_guard.check_pipeline_run_clear(slug="ml_mpo_multienv_target_select")` before Phase 2. Soft preference: after Exp 10–13 mutex clears ([D-012](../../research/DECISIONS.md)).

### 0.2 Thought process (Why)

**Why now:** Exp 8–13 optimized MPO as a **torque pilot** against reward return. Returns improved learning stability but mission capture KPIs remain poor ([D-024](../../research/DECISIONS.md)). Exp 4 showed vector OBC is valid infrastructure ([D-016](../../research/DECISIONS.md), [D-019](../../research/DECISIONS.md)) but still asked the policy to steer continuously. Architecturally, the OBC holds authority in flight; the interesting decision is **which target to service and when to shutter**, not RW torque micro-management (PD + safety already modeled).

**Why separate score from reward:** Early pipeline conflated them; production reward now mixes capture credit, penalties, and safe-mode shaping (`autonomous_control/reward.py`). Mission success for the semester is **quality × coverage integrals**, not TD return. Training may still use shaped reward; **verdict table uses score only**.

**Why multi-env:** Single-seed `build_setup(seed=7)` invites overfitting to one cloud/orbit draw. Sampling altitude + cloud fields (and optional `sat_z_offset`) tests generalization across orbit degradation and occlusion patterns — essential before claiming autonomous cloud-aware targeting.

**What we reject or defer:**

| Item | Disposition | Link |
|------|-------------|------|
| Standalone MPC pointing | Rejected | [D-001](../../research/DECISIONS.md) |
| Torque-learning as primary hypothesis | Deferred | PD path sufficient for safety exercise |
| Production edits during cycle | Forbidden | [D-003](../../research/DECISIONS.md) |
| Parallel pipeline training | Forbidden | [D-012](../../research/DECISIONS.md) |

#### 0.2.1 Shoulders of giants

| Source | Relevance |
|--------|-----------|
| [Exp 4 vector OBC](../4-documentation/04-agent-reference-pointing.md) | PD pointing request path, hold-last safety, baseline→`u` warmup pattern |
| [Exp 8 MPO decoupled dual](../4-documentation/08-mpo-decoupled-dual-fix.md) | Trust-region learner that actually trains (`learning_mode=true`) |
| [2206.02855 entity-based RL](../../research/2206.02855_efficient_entity_based_rl.pdf) | Set-structured decisions over many targets — motivates categorical target index |
| `simulation/capture_reward.py` | Canonical quality × coverage from `SimulationStateSeries` |
| [Discrete policy conversation](../../research-conversations/2026-07-02-exp14-discrete-categorical-action-gpt55.md) | Categorical head + train/eval exploration contract |
| [Exp 13 Track B (planned)](../2-run/13-mpo-learn-cadence-hparams.md) | MPO LR / batch / entropy axes — screen borrows axes, not cadence protocol |
| [`ml_sac_hparam_grid`](../../../backend/scripts/experiments/ml_sac_hparam_grid/README.md) | Staged short-train grid → pick winner → full run pattern |

### 0.3 Preliminary implementation remarks (How)

**Feasibility:** High conceptual delta, medium integration risk. Core simulation already exposes capture quality, coverage, and budget (`take_picture.py`, `capture_target.py`). **Most env diversity is already built:** `build_baseline_overflight_setup` + `cloud_formation_generator` sample cloud count/placement/height; `build_setup(seed)` samples altitude; `OrbitConfig.sat_z_offset` is resolve-ready. Phase 1 fork work = wire per-env seeds, override cloud count bounds to `(20, 40)`, optional attitude offset sampler — not new physics.

**Sibling scaffolds to copy:**

| Sibling | Reuse |
|---------|-------|
| `ml_mpo_decoupled_dual_torque/` | MPO runner, `_run_guard`, decoupled KL config, smoke JSON contract |
| `ml_agent_reference_pointing/` | Vector OBC episode patches, baseline warmup, PD routing |
| `ml_sac_mpo_compare/_compare_runner.py` | `n_mission_targets` wiring, KPI JSON shape |
| `ml_sac_hparam_grid/` | Multi-arm screen runner + `arm_kpis/{arm}.json` + summary JSON pattern |

**Build slices (Phase 1 ponytail order):**

1. **Mission score metric** — per-episode aggregator from `SimulationStateSeries` / capture series; eval rollup: `score_mean`, `score_std`, per-seed `score_ep[]`; log alongside `eval_return` in `summary_metrics.json`.
2. **Factored MPO actor fork** — `Categorical(50)` target head + 2 Gaussian→tanh bool heads (move, shutter); summed `log_prob` in experiment fork only (mirror `controller_actor.py` factorization).
3. **Target + move-gated OBC** — latch target index → ground XY; apply PD torque only when `move=True`; coast on `move=False` (fork patch on episode runner / stepper).
4. **Multi-env trainer loop** — Stage B only: outer loop over `env_index` with winning hparam config; Stage A = single-env 20-ep arms.
5. **Hparam screen runner** — 5 arms × (5 warmup + 20 train + 1 eval); JSON per arm; winner picker → frozen config for Stage B.
6. **Unseen-env eval harness** — fixed 5-seed eval list; baseline + treatment on identical seeds; verdict on `score_mean`; checkpoint by best eval `score_mean`.

**Smoke strategy:** 1 env (`mission_seed=0`, `cloud_seed=0`), 1 warmup + 2 train ep, `n_targets=50`, `--trim-artifacts` OK for import/smoke only; full arms require videos per visual-evidence rule.

**Risks / open questions (pre-Phase 1):**

| Risk | Mitigation |
|------|------------|
| MPO assumes continuous Gaussian throughout codebase | Fork actor: categorical target + 2 bool Gaussians; MPO `log_prob` sum in experiment slug only |
| Uncertain target distribution causes junk slews | `move` gate — learn `move=False` when target logits flat |
| Env switch mid-training destabilizes replay | Clear or partition replay per env segment (design choice in Phase 1.1) |
| Score/reward misalignment | Log both; verdict on score only (H14c) |
| Phase 1 scope creep into prod `autonomous_control/` | [D-003](../../research/DECISIONS.md) — experiment fork until closeout |

*(Skills)* [`hypothesis-experiment-cycle`](../../../.cursor/skills/hypothesis-experiment-cycle/SKILL.md) § ponytail rule; [`isolated-notebook-hypotheses`](../../../.cursor/skills/isolated-notebook-hypotheses/SKILL.md) § Before launching branches.

**Follow-up experiment (if inconclusive):** Exp 14b — entity embedding encoder over targets (literature: entity-based RL); or widen Stage A to Exp 13-style OAT on `learning_rate_eta` / KL targets if all 5 screen arms fail narrowly.

---

## Phase 1 — Build

### 1.1 What was built

Full fork under `backend/scripts/experiments/ml_mpo_multienv_target_select/` per plan `exp_14_phase_1_build_9f96fa1f.plan.md`. All slices completed:

| File | Slice | Description |
|------|-------|-------------|
| `_action_constants.py` | 0 | Canonical 52-dim action layout; single source of truth for all index constants and encode/decode functions |
| `_mission_score.py` | 1 | `compute_episode_mission_score` from `SimulationStateSeries` + `cmd_steps`; `aggregate_eval_scores` rollup |
| `_env_setup_fork.py` | 2 | 10 train envs with derive_seed namespacing; cloud count override `(20,40)`; `sat_z_offset` ±5°; fixed screen env; 5 eval envs |
| `_factorized_actor.py` | 3 | `FactoredActor`: shared `ControllerEncoder` trunk + `Categorical(50)` target head + 2 squashed-Gaussian bool heads |
| `_factorized_mpo_agent.py` | 3 | MPO fork: action_size=52, factored E-step + M-step, decoupled KL on Gaussian dims, entropy bonus on Categorical |
| `_episode_loop_fork.py` | 4 | Custom warmup / train / eval loop; move-gated `ObcPointingResolver`; `selected_target_indices` tracking |
| `_exp14_reward_fork.py` | 5 | Sparse capture reward + torque effort; global `compute_reward` patch |
| `_profile_baseline.py` | 6 | 5 hparam arms; `ControllerFeatureConfig` with bearing errors + captured mask + budget |
| `_screen_runner.py` | 6 | Stage A 5-arm × (5+20+1) ep runner; winner by train_ep20 → eval_return → entropy |
| `_multienv_runner.py` | 6 | Stage B 10-env × (5+30) ep curriculum; best `score_mean` checkpoint |
| `_eval_harness.py` | 6 | 5-seed baseline + treatment comparison on held-out envs |
| `run.py` | scaffold | `--verify` / `--smoke` / `--screen` / `--full` / `--eval-baseline` / `--eval-comparison` |
| `_verify_conversions.py` | scaffold | 7 checks A–G: one-hot layout, decode round-trip, swap detection, OBC `u` bounds, warmup format, baseline score |

Smoke pass: `python run.py --verify` (all 7 checks pass) + `python run.py --smoke --allow-cpu` exit 0, `results/smoke.json` contains finite `score_ep`.

### 1.2 Build review (pre-run gate)

Reviewed by `review-experiment-build` skill. **4 bugs found, all fixed before advancing to Phase 2.**

| Check | Result | Fix |
|-------|--------|-----|
| Replay buffer format | OK | One-hot applied action; warmup = degenerate case |
| **M-step gradient flow** | **BUG-CRITICAL fixed** | `actions_squashed` not detached → rsample cancellation → zero gradient for move/shutter Gaussian heads; added `.detach()` before `log_prob` |
| **Jacobian sign** | **BUG-MEDIUM fixed** | `+ log(1−a²)` should be `− log(1−a²)`; sign negated in `_log_prob_flat` |
| KL formulas | OK | Decoupled KL correct; alpha updates detached |
| Entropy bonus | OK | Exact `Categorical.entropy()`; sign correct |
| Episode loop | OK | `done` flag, cmd_steps, resolver reset verified |
| Action constants discipline | OK | No raw index literals outside `_action_constants.py`; swap test in `--verify` |
| Env diversity / seeding | OK | Train / eval / screen seeds disjoint via `derive_seed` namespaces |
| **Screen runner metrics** | **BUG-LOW fixed ×2** | (a) `eval_actions` never appended → entropy always 0; added `selected_target_indices` to `Exp14EpisodeResult`, collected in screen arm; (b) `clear_buffer()` before `train_metrics` → always None; swapped order |
| Reward fork | OK | `activate_reward_fork` called before episodes; no double-patch risk |

**Verdict:** pass-with-fixes — ready for Phase 2 (hparam screen).

### 1.3 Run instructions (How to execute)

**Setup (every session):**

```powershell
conda activate auto-sat
cd D:\code\sem-proj-asc\backend\scripts\experiments\ml_mpo_multienv_target_select
```

| Step | Command | Stage | What it does |
|------|---------|-------|----------------|
| **1** | `python run.py --screen --show-progress` | **A — hparam sweep** | 5 arms × (5 warmup + 20 train + 1 eval) on **one fixed env**; writes `results/screen_summary.json` with `winner_arm_id` |
| **2** | `python run.py --full --show-progress` | **B — full training** | **Winner arm only**; 10 envs × (5 warmup + 30 train); writes `results/stage_b_summary.json` — **run after Step 1** |
| **3** | `python run.py --eval-baseline --show-progress` | Eval | Baseline policy on 5 held-out seeds |
| **4** | `python run.py --eval-comparison --show-progress` | Eval | Trained agent vs baseline on same seeds |

Optional: `python run.py --check-mutex` (preflight only; `--screen` / `--full` acquire the lock automatically).

Build-only (after actor/action changes): `python run.py --verify` then `python run.py --smoke --allow-cpu`.

**Watch:** long runs → [`long-run-watch`](../../../.cursor/skills/long-run-watch/SKILL.md); console with `--show-progress`; KPI JSON under `results/`.

---

## Phase 2 — Run

*To be filled by `/document-experiment-step` after screen + full run complete.*
