---
name: review-experiment-build
description: >
  Review a completed experiment Phase 1 build before running any training compute.
  Checks ML implementation correctness, common AI code-writing pitfalls, and
  experiment-specific control questions. Use after /close-experiment-step for
  the build phase and before starting the run phase in complex experiments
  (many new ML components or long compute runs where bugs are expensive to discover late).
disable-model-invocation: true
---

# Review Experiment Build

**Gate:** run this review after Phase 1 (build) is complete and smoke passes, **before** committing to a full screen or multi-env run. It is optional for simple experiments but mandatory for experiments with:
- New actor/critic architectures
- Custom action spaces or factored action heads
- Custom episode loops replacing a canonical runner
- Off-policy replay buffer wiring changes

## Checklist (run top-to-bottom, document each finding)

### 1. Replay buffer action format
- [ ] Stored action represents the **applied** (sampled) action, not the predicted distribution
- [ ] One-hot or discrete components store the **index that was executed**, not the softmax probs
- [ ] Continuous components store the **post-squashing** value (e.g., tanh output), not the pre-squash sample
- [ ] Warmup and train episodes store the same format (same width, same meaning per index)
- [ ] Decode functions (`decode_*`) recover the same value that was passed to the actuator

### 2. M-step gradient flow (MPO / off-policy actor-critic)
- [ ] **Reparameterization cancellation check**: if M-step samples are drawn via `rsample()` from the **same** distribution whose `log_prob()` is computed, the score-function and reparameterization gradients cancel to zero. Verify either:
  - Samples are drawn from the **target** (frozen) policy, OR
  - Samples are **detached** before log_prob: `log_prob(dist_online, actions.detach())`
- [ ] Q-values used to weight M-step samples are **detached** (no gradient into actor from Q)
- [ ] E-step samples factored correctly across all action heads (categorical + Gaussian)

### 3. Log-probability and Jacobian corrections
- [ ] Tanh-squashed Gaussian log-prob includes the Jacobian: `log π(a) = log π_z(z) − log(1 − a²)`
  - The correction **subtracts** `log(1−a²)` (i.e., adds a positive term, since `log(1−a²) < 0`)
  - Common wrong pattern: `+ log(1−a²)` instead of `− log(1−a²)`
- [ ] atanh reconstruction is numerically clamped before log_prob to avoid `-inf`/`+inf`
- [ ] Jacobian term has **no** actor-parameter gradient (safe to have wrong sign without breaking training, but values will be wrong for logging/entropy estimation)

### 4. KL constraints (MPO decoupled KL)
- [ ] `kl_mu` uses **online** variance in denominator (not reference): `(μ_ref − μ_online)² / σ_online²`
- [ ] `kl_sigma` formula is full KL(`N(μ_online, σ_online) || N(μ_ref, σ_ref)`) — verify against MPO paper
- [ ] Alpha multipliers are **detached** when computing pi_loss; alpha optimized separately
- [ ] Target KL thresholds `eps_mu`, `eps_sigma` are from experiment's frozen hparams (not default MPO values)

### 5. Entropy bonus (categorical head)
- [ ] Entropy bonus uses **exact** `Categorical.entropy()`, not a Monte Carlo estimate
- [ ] Sign: `pi_loss -= entropy_coef * H[target]` (negative because we minimise pi_loss)
- [ ] `entropy_coef` is the fork-local hyperparameter, not something pulled from MPOConfig that doesn't have it

### 6. Episode loop
- [ ] Warmup stores actions in the **same buffer format** as training (same width, same index meanings)
- [ ] `done` flag is correctly set at the terminal timestep (not left False at natural horizon end) — required for correct TD bootstrapping
- [ ] `cmd_steps` collected inside the loop match the steps passed to `compute_episode_mission_score`
- [ ] `ObcPointingResolver.reset_episode(theta_orbit_rad=...)` called at episode start
- [ ] `train()` is NOT called during warmup episodes

### 7. Action constants discipline
- [ ] No raw integer indices for action slicing anywhere outside `_action_constants.py`
- [ ] `MOVE_IDX` and `SHUTTER_IDX` are in the correct order (swap detection test exists)
- [ ] All `encode_*` / `decode_*` functions imported from `_action_constants`, never re-implemented

### 8. Env diversity and seeding
- [ ] Train envs use deterministic but distinct seeds via `derive_seed` namespace per env_index
- [ ] Eval seeds are **never** the same as train seeds (different namespace prefix)
- [ ] Screen fixed env uses a fixed seed (independent from train/eval ranges)

### 9. Screen runner metrics
- [ ] Eval actions / target indices **collected** during eval episodes (not just warmup/train)
- [ ] `train_metrics = agent.train()` called **before** `clear_buffer()`, not after
- [ ] Winner selection ties resolved by a meaningful metric (entropy, eval score — not all-zero)

### 10. Reward fork
- [ ] Reward mode is activated before any episode runs (not just before training)
- [ ] Fork patches `reward_mod.compute_reward` globally — verify no double-patch from multiple `activate_reward_fork()` calls
- [ ] `RewardConfig` returned by `exp14_reward_config()` is wired into the episode loop via `simulation_overrides`

### 11. Stage runner wiring (screen / full / eval)
- [ ] Every symbol called inside stage runners (`_screen_runner`, `_multienv_runner`, artifact export helpers) is **imported at module level** in that runner file — not assumed from a sibling edit
- [ ] `--verify` (or equivalent) includes a **runner binding check** when smoke only exercises the single-episode path (e.g. `export_screen_arm_artifacts` bound on `_screen_runner` if `run_screen_arm` calls it)
- [ ] **Export mode documented:** Phase 1.3 and README state whether `--screen`/`--full` default to trim or export; when `profile.json` enables `export_episode_reward_plots` / videos, Phase 2 commands must use **`--export-artifacts`** unless user opts **`--trim-artifacts`** (see learnings.md `phase2-export-artifacts-not-trim-default`)

### 12. Pipeline doc run instructions (mandatory before Phase 1 close)
- [ ] Pipeline MD has `### 1.3 Run instructions (How to execute)` with copy-paste `conda activate auto-sat` + `cd` + entrypoint commands
- [ ] **Step table** maps each command to stage (A screen / B full / eval) and artifact — not a flat undifferentiated list (see learnings.md `run-instructions-stage-table`)
- [ ] Mutex: document that `--screen`/`--full` acquire lock via `_run_guard`; optional `python run.py --check-mutex` — **no** fragile `python -c` with repo-relative paths from experiment cwd
- [ ] **Do not** close Phase 1 or hand off to run phase if 1.3 is missing (see learnings.md `phase1-run-instructions-required`)

---

## Common AI code-writing pitfalls to scan for

| Pitfall | Where to look |
|---------|---------------|
| `rsample` → `log_prob` on same dist → zero gradient | M-step of any actor-critic |
| Jacobian sign inverted (−log instead of +log correction) | Any squashed Gaussian log_prob |
| Wrong KL direction: `KL(ref \|\| online)` instead of `KL(online \|\| ref)` | Alpha / KL constraint |
| Buffer action format width mismatch between warmup and train | `store()` call sites |
| `done=False` at natural episode end → wrong bootstrapping | Episode loop termination |
| Metric list initialized but never populated (entropy, scores) | Screen/eval runners |
| Stage runner calls helper without module-level import | `_screen_runner`, artifact export modules |
| Smoke passes but multi-stage runner path untested | Verify gate must bind runner symbols |
| Soft-update applied to wrong pair (source/target swapped) | `_soft_update()` calls |
| Q-values NOT detached before being used as weights | E-step / M-step boundary |

---

## How to run

```text
1. Read the experiment plan file (.cursor/plans/<slug>.plan.md)
2. Read all implementation files in the experiment folder
3. Work through each checklist section top-to-bottom
4. Document findings as: [OK], [BUG: severity] description, or [WARN]
5. Fix all BUG items before proceeding to run phase
6. Verify pipeline doc has `### 1.3 Run instructions` — add if missing before Phase 1 close
7. Append a ## Review block to the pipeline doc Phase 1 section:
     findings: [list], fixes_applied: [list], verdict: pass|pass-with-fixes|fail
```

---

## Output format

Append to the pipeline Phase 1 section in `docs/experiments/pipeline/`:

```markdown
### Build Review (pre-run gate)

| Check | Result | Notes |
|-------|--------|-------|
| replay buffer format | OK | |
| M-step gradient flow | BUG-CRITICAL fixed | rsample cancellation, detach added |
| Jacobian sign | BUG-MEDIUM fixed | sign inverted |
| KL formulas | OK | |
| entropy bonus | OK | |
| episode loop | OK | |
| action constants discipline | OK | |
| env diversity / seeding | OK | |
| screen runner metrics | BUG-LOW fixed | eval_actions never appended |
| reward fork | OK | |

**Verdict:** pass-with-fixes (4 bugs found, all fixed before run)
```
