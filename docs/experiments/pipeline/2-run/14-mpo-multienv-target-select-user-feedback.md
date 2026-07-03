# Exp 14 — User feedback: bugs & miscommunications

**Experiment:** `ml_mpo_multienv_target_select` (Exp 14)  
**Period:** Phase 1 build → first Stage A screen runs → operator Q&A on artifacts (2026-07-02)  
**Audience:** Future builders, reviewers, pipeline doc authors  
**Status:** Living feedback from operator + build review session (not a Phase 4 verdict)  
**Companion:** [Phase 1 build feedback](../../research-conversations/2026-07-02-exp14-phase1-user-feedback.md) (action-space / import-collision detail)

---

## Executive summary

Phase 1 produced a runnable fork, but **operator-visible behavior lagged implied spec** (progress UX, run docs, checkpointing) while **silent ML bugs** would have made the experiment look like it was training when Gaussian heads received zero M-step gradient. Several explanations during the first runs were **wrong or imprecise** (CPU-sim bound, steps/s baselines, return vs score). The core architecture reuse (`training_workflow`, production MPO vectorized sampling) was **assumed, not enforced**, in the plan → build handoff.

A separate **architecture miscommunication** surfaced late: repo rules and `SimulationStateSeries` docs describe it as the mandatory episode artifact, but **training runs do not persist raw series to disk** — only derived KPIs, plots, and top-N MP4s. Exp 14 follows the same pattern; operators cannot post-hoc inspect full trajectories without re-running episodes or exporting videos.

---

## Bugs found and fixed (code)

| ID | Severity | Symptom | Root cause | File(s) | Fixed? |
|----|----------|---------|------------|---------|--------|
| B1 | **Critical** | Move/shutter heads never learn from Q-weighted M-step; only KL moves them | `rsample()` then `log_prob()` on same `dist_online` without `.detach()` → reparameterization + score-function gradients cancel to zero | `_factorized_mpo_agent.py` | Yes (pre–Phase 2 review) |
| B2 | Medium | Wrong `log_prob` magnitudes near tanh bounds (gradients OK) | Jacobian term used `+ log(1−a²)` instead of subtracting | `_factorized_actor.py` `_log_prob_flat` | Yes |
| B3 | Low | Screen winner entropy tie-break always 0 | `eval_actions` / `selected_target_indices` not collected in eval loop | `_screen_runner.py` | Yes |
| B4 | Low | `train_metrics` always `None` in arm KPIs | `clear_buffer()` called before reading `train_metrics` | `_screen_runner.py` | Yes |
| B5 | Low | `compute_episode_mission_score` NameError risk | Missing import in custom episode loop | `_episode_loop_fork.py` | Yes |
| B6 | Operator | Console silent during long runs except `Using device: cuda` | `--show-progress` plumbed through runners but **never wired** to `TrainingProgressDisplay` | `_episode_loop_fork.py`, runners | Yes |
| B7 | Perf | ~7 steps/s train; unnecessary Python overhead in learner | MPO Q/π sampling used `for _ in range(num_samples)` instead of `sample((S,))` / `sample_stored_actions` batch API (production `controller_agent.py` is vectorized) | `_factorized_mpo_agent.py`, `_factorized_actor.py` | Yes (mid–Phase 2) |
| B8 | Ops | Separate `results/exp14.log` duplicated or missed console output | File log treated as primary operator channel | `_exp14_runner_common.py` | Yes → console-only `append_log` |

---

## Bugs / gaps still open (or accepted debt)

| ID | Severity | Symptom | Notes |
|----|----------|---------|-------|
| G1 | **Ops** | Stopping mid-arm loses all KPIs for that arm | `arm_kpis/{arm}.json` written only at **end** of warmup+train+eval; no per-episode checkpoint |
| G2 | Ops | Running screen arms one-by-one does not produce `screen_summary.json` | Summary + winner pick only inside single `run_screen()` over all passed arms |
| G3 | Ops | No policy / replay persistence | Cannot resume Stage A arm or Stage B curriculum after kill |
| G4 | ML? | `learning_mode: false` even on completed `hp_default` screen arm | Eval score ~0.17, train return still strongly negative; screen compares arms but absolute “learning” gate fails |
| G5 | Design | Markov feedforward encoder vs sequential warmup demos | Warmup buffer has rich temporal expert trajectories; actor/critic see **i.i.d.** `(s,a,r,s')` — no LSTM, no frame stack |
| G6 | Design | 52-dim one-hot actions in replay + Q critic | Factorized policy internally; critic pays full 52-dim cost — performance + credit-assignment debt |
| G7 | Data? | `stored_action` may be all-zeros on non–controller-update substeps | Only refreshed inside `should_update_controller()`; harmless at dt=1.5s/1.5s but fragile if dt profile changes |
| G8 | UX | `--smoke` ignores `--show-progress` | Smoke path still uses raw episode loop without progress helpers |
| G9 | UX | `--eval-baseline` / `--eval-comparison` progress partial | First eval seed only for tqdm in some paths |
| G10 | Doc | Phase 0 reward formula (α,β,γ,δ,ε composite) vs code | `_exp14_reward_fork.py` implements **sparse capture + torque effort + budget penalty** via `RewardConfig`; named constants α–ε are **not** wired into a custom composite — pipeline prose oversells implemented shaping |
| G11 | **UX** | `--screen --show-progress` crashes on Windows | `OSError: [Errno 22] Invalid argument` in tqdm flush during nested phase+step bars (`results/run_error.json` 2026-07-02T21:42:37Z) | Workaround: run without `--show-progress` |
| G12 | CLI | `--trim-artifacts` flag has no effect | `run.py` defines the flag but screen passes `trim_artifacts=not args.export_artifacts` only — `args.trim_artifacts` is never read | Use `--export-artifacts` to enable export; flag is misleading |
| G13 | **Data** | No `SimulationStateSeries` on disk after training | Every episode produces `result.simulation_series` in memory; disk gets CSV/JSON + optional top-N MP4/PNG only — no `.pkl.gz` series per episode | See § Miscommunication: series persistence below |
| G14 | Ops | `export_screen_arm_artifacts` NameError on first screen attempt | Import missing in `_screen_runner.py` before fix; caught by verify check H after patch | Fixed (`results/verify.json` check H passes) |

---

## Miscommunications (plan ↔ build ↔ operator)

### `SimulationStateSeries`: mandatory artifact vs disk persistence

| What docs/rules say | What training actually does | Operator expectation gap |
|---------------------|----------------------------|--------------------------|
| `simulation-single-source-of-truth.mdc`: episode runs must produce/consume `SimulationStateSeries` | **Yes in memory** — `Exp14EpisodeResult.simulation_series` on every rollout | Correct at runtime |
| `experiment-visual-evidence.mdc`: behavioral claims need video + frame inspect | Screen **defaults to no export** unless `--export-artifacts`; no series files even when exporting | Operator may assume “artifact” means persisted series |
| `user-manual.md`: `series = result.simulation_series` | Series lives on `EpisodeResult` until process exit; `plan_standard_training_artifacts()` consumes it for top-N MP4/PNG then discards | “Where is my series file?” after a 20 min arm |
| Mission score computed from series (`_mission_score.py`) | Score scalar written to `arm_kpis/*.json`; full series not saved | Cannot re-audit score without re-sim |

**Size context (not the main blocker):** baked fixtures show ~38 KB gzip per typical ~8 min episode (`training_sparse`, 346 steps) vs ~1.2 MB for dense cloud scenes. Saving all 26 episodes/arm × 5 arms is manageable (~2–6 MB) but was never implemented.

**What Exp 14 does save (when `--export-artifacts`):**

| Saved | Path | Source |
|-------|------|--------|
| Scalar KPIs | `results/arm_kpis/{arm}.json` | Returns, mission score rollup, learning signal |
| Reward plot (warmup) | `results/artifacts/screen/{arm}/episodes/*_latent_applied.png` | Series → matplotlib |
| Top-N MP4/PNG (train/eval) | `results/artifacts/screen/{arm}/videos/`, `episodes/` | Series → render export |
| **Not saved** | — | Raw `SimulationStateSeries` pickle/npz per episode |

**Exceptions elsewhere in repo:** warmup bundle cache (`episodes.pkl.gz`), video_export fixtures, parallel video workers pickle series in-memory only.

**Recommendation:** Document in README that series is ephemeral unless operator adds `--export-artifacts` (derivatives only) or a future `--save-series` flag; do not imply checkpoint/resume includes trajectories.

### Implied but not delivered without explicit ask

| Topic | What was assumed | What shipped initially | Impact |
|-------|------------------|------------------------|--------|
| Progress UX | Same kernel as `training_workflow` → same banners, phase tqdm, step tqdm, episode summaries | `--show-progress` flag existed; almost no stdout feedback | Operator blind for ~20 min/arm; trust in fork dropped |
| Architecture reuse | “Slightly adapt info panels” from existing stack | Custom episode loop fork without `TrainingProgressDisplay` wiring | Felt like a greenfield script, not extension of s01 workflow |
| Plan → build handoff | Single mental model across planning and implementation | Plan written with one model/session, build with another; “implied” wiring skipped | Dead params, missing 1.3 run instructions, mutex one-liner wrong cwd |
| Logging | Console is enough for long runs | `exp14.log` file log set up as parallel channel | Operator had to tail wrong artifact |
| Run instructions | README enough | Pipeline `### 1.3` missing until flagged; flat flag list didn’t distinguish Stage A vs B | “Which command is hparam sweep?” |

### Wrong or imprecise explanations (corrected in discussion)

| Statement (wrong) | Correction |
|-------------------|------------|
| “CPU-sim bound at ~7 steps/s” | **Learner-bound:** `train()` ~88% of wall time; sim ~8%. Low GPU % is **serial pipeline + idle gaps**, not orbit integration dominating |
| “~25 steps/s is normal for this MPO on CUDA” | Comparable **train-every-step** runs are ~13–17 steps/s; ~25–31 often **warmup/eval** or **train_every_n_steps ≫ 1** (Exp 13 cadence) |
| “Bigger model explains slow train” | Same `MPOConfig` depth; slowness is **52-dim critic actions**, **80/40 MPO samples**, **train every step**, and (before fix) **Python sample loops** |
| “score=0 during train means broken” | **Mission score** = successful captures only; **return** can worsen while score stays 0 on early train eps — especially `hp_conservative` (3× lower LR) |
| “`SimulationStateSeries` is saved as the episode artifact” | It is the **in-memory** contract (train = eval = render). **Disk** persistence is derived artifacts only (CSV, plots, top-N videos). Re-run from checkpoint or export MP4 to recover behavior |
| “`--trim-artifacts` skips MP4 during screen” | Flag is **not wired**; screen trims by default because `--export-artifacts` is absent. Only `--export-artifacts` enables export |
| “Default screen run produces videos for Phase 2 evidence” | Default `trim_artifacts=True` (no `--export-artifacts`) → **no MP4s** unless operator opts in — conflicts with visual-evidence rule for behavioral claims |

### Naming / stage confusion

| Confusion | Clarification |
|-----------|---------------|
| “One full training run” | Operator meant **one complete screen arm** (`hp_default`: 5 warmup + 20 train + 1 eval), not Stage B `--full` |
| Stage A vs B | **Stage A** = `--screen` (5 hparam arms × 26 ep). **Stage B** = `--full` (winner × 10 envs × 35 ep) |
| 5 configurations | **5 screen arms** total; after `hp_default` done, **4 remain** (or 3 after `hp_conservative` if that run completes) |

### Mutex / preflight

| Issue | Detail |
|-------|--------|
| `python -c` mutex check from experiment cwd | Repo-relative import path → `ModuleNotFoundError`; replaced with `python run.py --check-mutex` |
| Stale lock after kill | `run_error.json` showed pid still holding lock; operator must wait or clear stale lock |

---

## Operator observations (first runs)

### `hp_default` (saved — `results/arm_kpis/hp_default.json`)

- Wall ~20 min/arm at ~7 steps/s train (pre-vectorize).
- Train return improved noisy: ep20 ≈ **−741** (from ~−1260).
- Eval **mission_score** ≈ **0.17**; eval return ≈ **+17**.
- `learning_mode: false` in KPI JSON despite upward train return trend.

### `hp_conservative` (interrupted / in progress)

- Live console: return **worse and worse**, **score = 0** on train episodes.
- Expected for **very low LR** in only 20 train episodes — not necessarily regression from vectorize patch.
- Warmup still good (preview: mission_score ≈ 3.8, 10 shutters, 6 rewarded captures).

### Warmup quality (reference)

- Ep 0 capture target indices: `0,5,10,15,20,25,30,35,40,45` (strided over 50 targets).
- Buffer actions: 52-dim one-hot target + move (+1 engage / −1 nadir) + shutter (+1/−1).
- Warmup **stores** expert transitions; **does not** call `train()` until train phase.

---

## Design feedback (not bugs — follow-up experiments)

1. **Temporal policy:** Feedforward encoder cannot learn orbit-phase / engage-then-shutter sequencing; warmup teaches it in data but not in architecture. Simplest next step: **frame stack**; proper step: **LSTM + sequence replay**.
2. **Compact action/obs:** Store `(target_idx, move, shutter)` in replay; embed for critic; reduce mission scalar fan-out (50+50 bearings/mask) if hypothesis allows.
3. **Async learner / GPU feeder:** Serial sim → train loop underutilizes GPU; pipeline sketch (sim workers → replay lake → learner thread) is valid but **out of scope** for Phase 1 fork.
4. **Learn cadence:** Exp 13 showed `train_every_n_steps` dominates steps/s; Exp 14 frozen at 1/1 — screen may need cadence arm or longer train episode count for slow LR arms.
5. **Checkpointing:** Per-arm incremental JSON (returns so far) + optional policy snapshot would prevent losing 20 min on Ctrl+C.

---

## Recommendations for next build / review gate

**For `review-experiment-build` / Phase 1 closeout:**

- [ ] Assert `--show-progress` actually drives `TrainingProgressDisplay` (grep for dead `show_progress` params).
- [ ] Assert MPO sampling matches production vectorized pattern (no per-sample Python loops).
- [ ] Require `### 1.3 Run instructions` with stage table + cwd-correct commands.
- [ ] Document checkpoint behavior (what is lost on kill).
- [ ] Align pipeline reward prose with `_exp14_reward_fork.py` actual `RewardConfig` flags.
- [ ] Note Markov encoder vs sequential mission explicitly in Phase 0/1.
- [ ] README: clarify `SimulationStateSeries` is in-memory; list what is (and is not) written under `results/`.
- [ ] Wire or remove dead `--trim-artifacts` CLI flag.
- [ ] Fix Windows tqdm crash before recommending `--show-progress` on win32.

**For operator runbook (remaining Stage A):**

```powershell
# Skip hp_default (done). Run remaining arms individually.
# On Windows: omit --show-progress until tqdm fix (G11); add --export-artifacts for MP4 evidence.
python run.py --screen --arms hp_conservative --export-artifacts
python run.py --screen --arms hp_mid_batch --export-artifacts
python run.py --screen --arms hp_aggressive --export-artifacts
python run.py --screen --arms hp_explore --export-artifacts
# Then pick winner from results/arm_kpis/*.json (or merge screen_summary manually)
python run.py --full --arm <winner> --show-progress
python run.py --eval-baseline --show-progress
python run.py --eval-comparison --show-progress
```

---

## Related artifacts

| Path | Role |
|------|------|
| `docs/experiments/pipeline/2-run/14-mpo-multienv-target-select.md` | Pipeline record |
| `backend/scripts/experiments/ml_mpo_multienv_target_select/README.md` | Operator commands |
| `.cursor/skills/review-experiment-build/SKILL.md` | Build review gate (initialized from this exp) |
| `.cursor/memory/learnings.md` | Durable learnings (`mpo-mstep-rsample-detach`, `phase1-run-instructions-required`, etc.) |
| `results/arm_kpis/hp_default.json` | First complete screen arm |
| `results/warmup_preview.json` | Warmup baseline quality gate |

---

*Updated 2026-07-02 with operator Q&A on `SimulationStateSeries` persistence, Windows tqdm failure, and dead `--trim-artifacts` flag. Update when new arms complete or Phase 2/3 closeout adds evidence.*
