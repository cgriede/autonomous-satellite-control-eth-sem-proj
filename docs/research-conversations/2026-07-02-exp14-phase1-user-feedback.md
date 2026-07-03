# Exp 14 Phase 1 — User feedback (bugs & miscommunications)

**Date:** 2026-07-02  
**Experiment:** `ml_mpo_multienv_target_select` (Exp 14)  
**Scope:** Phase 0 design Q&A → Phase 1 build → first `--screen` attempts  
**Author:** Operator feedback synthesized from chat + `results/*.json`  
**Canonical living doc:** [14-mpo-multienv-target-select-user-feedback.md](../experiments/pipeline/2-run/14-mpo-multienv-target-select-user-feedback.md) (ops + runtime bugs; updated with series-persistence Q&A)

Related docs:
- [Discrete action design](./2026-07-02-exp14-discrete-categorical-action-gpt55.md)
- [Phase 1 build rationale](./2026-07-02-exp14-phase1-build-action-space.md)
- Build plan: `.cursor/plans/exp_14_phase_1_build_9f96fa1f.plan.md` (not edited)

---

## Executive summary

Phase 1 scaffolding **does run** (`--verify`, `--smoke` pass; warmup baseline quality gate passes). Several **design assumptions were not aligned early** between operator intent and what agents documented or initially modeled. The first **`--screen` run failed on Windows** due to tqdm/progress-display I/O, not ML logic. Import-path collisions with `ml_algo_overnight` caused a painful first-build debug loop.

---

## 1. Miscommunications (design & documentation)

### 1.1 Action space shape: 50+1+1 vs 51 vs 52

| Who said what | Issue |
|---------------|-------|
| Operator (early): three **orthogonal** outputs — target (50) + move (1) + shutter (1) | Clear from operator perspective |
| Phase 0 doc (transient): “action dim stays **51**” | Wrong for fork: replay buffer is **52** (one-hot 50 + move_gym + shutter_gym) |
| Agent summaries sometimes wrote “Categorical(50) + 2 bool” without stating buffer width | Operator had to re-assert that target/move/shutter are **not** one combined softmax |

**Resolution (locked in plan):** factorized actor; **52-dim applied action** in replay; `_action_constants.py` as single source of truth.

**Lesson:** Always state **three numbers** in docs: `(policy heads: 50+1+1) → (buffer dims: 52) → (critic input: 52)`.

---

### 1.2 “Probability distribution over targets” vs “store softmax in replay”

| Operator intent | Agent/doc drift |
|-----------------|-----------------|
| Policy **outputs** a distribution; environment **executes** a sampled index | Easy to conflate “distribution in network” with “vector stored in buffer” |

**Resolution:** buffer stores **one-hot of sampled index**, not softmax probs. Warmup stores Dirac one-hot at `active_target_index`.

**Lesson:** Explicit diagram in Phase 0: `softmax → sample → one-hot → OBC` with “NOT stored” on the probs line.

---

### 1.3 Single `Categorical(52)` vs factorized heads

Early Phase 0 text mentioned “categorical target+shutter” in one line; operator clarified **50 + 1 + 1** with separate meaning (KSP navball + engage key + shutter).

Agent once framed the alternative as “52-way softmax where target 7 competes with move” — operator rejected that framing as obvious non-goal.

**Resolution:** `Categorical(50)` + independent `Normal→tanh` for move and shutter; KL only on continuous pair; entropy bonus on target only.

---

### 1.4 Move semantics: PD engage vs “hold last target”

Plan lock: `move=False` → **zero RW torque (coast)**, not “keep pointing at last target.”

This was stated in the build plan but easy to miss when reading “move-gated OBC” alone.

**Lesson:** One-line actuator table in README: `move=False ⇒ τ=0`, not hold.

---

### 1.5 Score vs reward

| Metric | Purpose |
|--------|---------|
| `score_ep` / `score_mean` | Verdict KPI (quality × coverage, k=1) |
| `episode_return` | Training signal (sparse capture + torque effort) |

**Miscommunication:** Early Phase 0 mixed “mission score” with “reward shaping α…ε” without always saying **verdict uses score only**.

Screen winner criteria in plan: rank by **train return @ ep 20**, tie-break eval return — **not** score_mean. Operator may expect score-based screen winner; doc should flag that explicitly.

---

### 1.6 Production `EpisodeRunner` vs custom loop

Plan pre-condition was correct: production hardcodes `POLICY_RAW_DIM=2`.  

**Miscommunication risk:** Agents initially implied “fork MPO only”; operator had to understand **episode loop is mandatory**, not optional.

---

### 1.7 Env setup API naming

Plan referenced `build_baseline_overflight_setup`; implementation uses `build_setup` + local `build_exp14_clouds` because cloud bounds override lives in a fork, not in production baseline helper.

Not a logic bug, but **doc/code name mismatch** caused confusion during build.

---

### 1.8 `num_samples_q=80` / `num_samples_pi=40`

Operator asked whether these come from the MPO paper. Answer: **project default**, not paper-fixed; Acme uses one knob `N=20`.

**Miscommunication:** Treating 80/40 as “research-backed” without labeling them as inherited Exp 8 defaults.

---

### 1.9 Conda env name

User global rule says `LRF`; repo rule says **`auto-sat`**. Build sessions mixed references until workspace rule won.

### 1.10 `SimulationStateSeries` persistence vs “mandatory episode artifact”

Repo rules (`simulation-single-source-of-truth.mdc`, `user-manual.md`) state that `SimulationStateSeries` is the required episode-level artifact. Exp 14 **does produce it on every rollout** (`Exp14EpisodeResult.simulation_series`).

**Miscommunication:** “Mandatory artifact” was read as **saved to disk**. Training (including Exp 14) only persists **derived** outputs:

- `arm_kpis/*.json`, `episodes.csv`-style scalars
- Top-N reward PNGs + MP4s when `--export-artifacts` is set
- **Not** gzip-pickled series per episode

Series size is moderate (~38 KB/episode gzip for typical runs) — the design choice is curated export + re-run from checkpoint, not storage cost alone.

**Operator impact:** After a long screen arm, there is no `series.pkl` to inspect pointing/shutters without re-sim or exporting video. Warmup preview PNG uses series in-memory only.

---

### 1.11 `--trim-artifacts` CLI flag unused

`run.py` documents `--trim-artifacts` but screen uses `trim_artifacts=not args.export_artifacts` — the flag is never read. Default screen = no artifact export unless `--export-artifacts`.

---

## 2. Bugs found during Phase 1 implementation

### 2.1 Module name collisions with `ml_algo_overnight`

**Symptom:** `ImportError: cannot import name 'EXPERIMENT_ID' from '_runner_common'` (resolved to overnight module).

**Cause:** `_profile_baseline.py` inserted `ml_algo_overnight` at front of `sys.path`; generic names (`_runner_common`, `_reward_fork`, `_sim_constants_fork`) shadowed experiment-local files.

**Fix applied:** Rename to `_exp14_runner_common`, `_exp14_reward_fork`, `_exp14_sim_constants`; stop prepending overnight to `sys.path` in profile loader.

**Severity:** High (blocked all imports until fixed).

---

### 2.2 `RewardConfig` wired to wrong setup field

**Symptom:** `TypeError: SimulationConfig.__init__() got an unexpected keyword argument 'reward_config'`.

**Cause:** Episode loop tried `replace(sim_config, reward_config=…)`; reward lives on `EnvironmentSetup.simulation_overrides.reward_config`.

**Fix:** `replace(setup, simulation_overrides=replace(overrides, reward_config=…))`.

**Severity:** High (smoke crash).

---

### 2.3 Warmup `active_target_index=50` sentinel

**Symptom:** `ValueError: target_idx=50 out of [0, 50)`.

**Cause:** Baseline policy uses `n_targets` (50) as “past last target” sentinel when capture list exhausted; encode path assumed valid index always.

**Fix:** Clamp to `[0, N_TARGETS-1]` for warmup one-hot encoding.

**Severity:** Medium (warmup-only edge case; masks “no active target” semantics).

**Open question:** Should sentinel steps store a special “no target” action or skip store?

---

### 2.4 M-step `log_prob` batch shape mismatch

**Symptom:** `ValueError: Value is not broadcastable … torch.Size([10240]) vs torch.Size([256])`.

**Cause:** E-step stacks `(num_samples_pi, batch, 52)` actions but `Categorical.log_prob` expected batch 256.

**Fix:** `_expand_dists_for_batch()` + `_log_prob_flat()` in `_factorized_actor.py`.

**Severity:** High (first `train()` crash in smoke).

---

### 2.5 Missing `sys.modules` registration for importlib loads

**Symptom:** `AttributeError: 'NoneType' object has no attribute '__dict__'` when loading overnight `_runner_common` via importlib.

**Fix:** `sys.modules[spec.name] = mod` before `exec_module`.

**Severity:** Medium.

---

### 2.6 Accidental deletion of `build_stepper` call

During reward-config fix, one edit pass removed `stepper = build_stepper(...)` and left `ctrl0 = stepper.current_timestep_state()` — caught immediately.

**Severity:** Low (would have been obvious NameError).

---

## 3. Bugs found at runtime (after smoke)

### 3.1 `--screen --show-progress` tqdm crash on Windows

**Artifact:** `results/run_error.json` (2026-07-02T21:42:37Z)

**Symptom:** `OSError: [Errno 22] Invalid argument` inside `tqdm` flush/write during `TrainingProgressDisplay.on_step` / `end_episode`.

**Context:** Nested progress bars (phase + step) writing to stdout in Cursor/agent terminal on Windows.

**Impact:** Screen run aborts mid-train even if simulation logic is fine.

**Workarounds tried by operator:** run without `--show-progress`, or redirect output.

**Fix still needed:** Disable nested tqdm on non-TTY, single progress bar, or `file=sys.stderr` + `dynamic_ncols=False` guard in `_exp14_progress.py` / episode loop.

**Severity:** High for operator UX on Windows.

---

### 3.2 `export_screen_arm_artifacts` NameError (first screen attempt)

**Artifact:** Earlier `results/run_error.json` (`NameError: name 'export_screen_arm_artifacts' is not defined`).

**Fix:** Import wired in `_screen_runner.py`; verify check H (`_verify_conversions.py`) now asserts binding.

**Severity:** High (blocked screen until fixed); **status: fixed**.

---

## 4. Smoke / early-train anomalies (watch list)

Not necessarily bugs; flag for Phase 2 interpretation.

| Observation | `smoke.json` | Notes |
|-------------|--------------|-------|
| Warmup mission score healthy | ~3.19 | Baseline path OK |
| Train mission score zero | 0.0 both eps | Random untrained agent likely fires shutter without successful captures |
| Train return strongly negative | ~−1140 | Torque effort + failed captures with sparse credit |
| Eval score_ep small but >0 | ~0.29 | Pipeline wired; not behavioral success |
| `kl` negative | ~−0.15 | Gaussian KL formula can go negative numerically; monitor |

Warmup preview gate (`warmup_preview.json`) **passed**: mission score ~3.8, 10 shutters, peak efficiency 1.0 — contradicts “baseline broken” hypothesis.

---

## 5. Plan vs delivered gaps

| Plan item | Status | Notes |
|-----------|--------|-------|
| Slice 0–6 + scaffolding | Done | Under `ml_mpo_multienv_target_select/` |
| `--verify` A–G | Pass | `results/verify.json` |
| `--smoke` | Pass | `results/smoke.json` |
| Human review gate before screen | Process | Operator review requested; screen was attempted anyway |
| Full α/β/γ/δ/ε reward shaping | Deferred | Fork uses sparse + `k_torque_effort=ε` only |
| Copy `_sim_constants_fork.py` name | Renamed | `_exp14_sim_constants.py` to avoid collision |
| `_reward_fork.py` name | Renamed | `_exp14_reward_fork.py` |
| Progress / artifacts | Added post-plan | `_exp14_progress.py`, `_exp14_artifacts.py`, warmup preview — not in original plan file |

---

## 6. Process & communication gaps

1. **Human review gate skipped in practice:** Plan said STOP after smoke for review of four core modules; screen run started before explicit “looks good.”
2. **Action-space doc lag:** Phase 0 doc briefly said 51 dims; operator correction came late in thread.
3. **Agent assumed combined action space** until operator said “50+1+1 orthogonal” — should have been restated after first categorical discussion.
4. **Build agent did not run `--screen`** in first pass; operator hit Windows tqdm bug separately.
5. **No video/frame evidence yet** for learned train behavior (only warmup PNG preview) — pipeline rule expects MP4/frame inspect before behavioral claims in Phase 2+.

---

## 7. Recommendations

### For docs / Phase 1 closeout

- [ ] Fix Phase 0/1 pipeline doc: **52 buffer dims**, factorized heads, score vs return, screen winner = train return not score.
- [ ] Add actuator truth table: move/shutter threshold at 0; move=False ⇒ zero torque.
- [ ] Document that `SimulationStateSeries` is in-memory only; disk gets derived artifacts.
- [ ] Wire or remove dead `--trim-artifacts` flag.

### For code

- [ ] Harden progress display for Windows (`--show-progress` must not crash screen).
- [ ] Keep **`exp14_`-prefixed** helper modules; never generic `_runner_common` in experiment folder.
- [ ] Consider `--screen` default `show_progress=False` on win32 until tqdm fix lands.

### For next operator session

- [ ] Confirm `sat_z_offset` ±5° range before Stage B.
- [ ] Run `--eval-baseline` once and record `score_mean` before treatment comparison.
- [ ] After first train ep with video export, run `video-frame-inspect` before claiming pointing/shutter behavior.

---

## 8. What went well

- Factorized action contract (`_action_constants.py`) and verify checks A–G caught index swap and one-hot layout early.
- Custom episode loop correctly separates warmup (baseline torque) from train/eval (move-gated vector OBC).
- Mission score hook reuses `applied_capture_reward_series(k_capture=1.0)` — aligned with Phase 0 KPI definition.
- Warmup quality gate + latent/applied reward plot give fast baseline sanity check without full MP4 wait.

---

*This file is operator feedback for improving Exp 14 docs, build discipline, and Windows run UX — not a verdict on H14a–H14d.*
