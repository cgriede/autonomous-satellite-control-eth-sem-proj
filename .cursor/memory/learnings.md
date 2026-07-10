# Agent learnings log

Durable record of **breakthroughs** (do this) and **anti-patterns** (never do this).  
Invoke **`/learn-skill`** (see [`.cursor/commands/learn-skill.md`](../commands/learn-skill.md)) to sweep skills/rules after adding entries here.

## Entry format

```markdown
### YYYY-MM-DD — short-id

- **Type:** breakthrough | anti-pattern
- **Learning:** One imperative sentence.
- **Evidence:** What happened (session, bug, review) — optional but recommended.
- **Applied to:** comma-separated skill/rule names, or `pending`
- **Status:** pending | applied | superseded
```

---

### 2026-06-03 — backlog-xlsx-preflight

- **Type:** anti-pattern
- **Learning:** When backlog or sprint status is requested, preflight `backlog.xlsx` via `backlog_xlsx.py check`; if the workbook is missing, ask the user where it lives — never silently use `backlog.md` as the live board.
- **Evidence:** Session review updated only `backlog.md` until user pointed out missing xlsx workflow.
- **Applied to:** pm-briefing, pm-backlog-review, minimal-feature-cycle, learn-skill (POINTER), bulk-change-triage-commit (N/A), minimal-feature-review (POINTER), new-skill-integration (N/A), all other skills (N/A), all rules (N/A)
- **Status:** applied

---

### 2026-06-30 — agent-tools-in-cursor-not-backend

- **Type:** breakthrough
- **Learning:** Reusable agent CLIs (backlog xlsx, presentation pptx, frame extract) live under `.cursor/tools/` with a matching workflow skill — never add them to `backend/scripts/` as app logic; re-running ad-hoc Python per chat action is inefficient.
- **Evidence:** Presentation iteration + backlog pattern; user requested build-tool skill.
- **Applied to:** build-tool, create-update-presentation, pm-backlog-review, pm-briefing, minimal-feature-cycle
- **Status:** applied

---

- **Type:** anti-pattern
- **Learning:** Before creating a new skill or slash command, glob `.cursor/skills/**/SKILL.md` and `.cursor/commands/` — extend the existing artifact instead of duplicating.
- **Evidence:** User asked to add learn-skill; workflow already existed under `.cursor/skills/learn-skill/` and needed refinement only.
- **Applied to:** learn-skill, new-skill-integration
- **Status:** applied

---

### 2026-06-03 — human-confirm-before-review-ship

- **Type:** anti-pattern
- **Learning:** After a review fix, never commit or treat the slice as shipped until the user explicitly confirms human verification passed — passing pytest or agent-run notebook output is not sufficient.
- **Evidence:** Safe-mode movement-constraints review: agent attempted a production commit immediately after tests passed; user rejected because they had not re-verified notebook/MP4 behavior.
- **Applied to:** minimal-feature-review, minimal-feature-cycle (POINTER), bulk-change-triage-commit (POINTER), visual-output-verification (POINTER), learn-skill (POINTER), all other skills (N/A), all rules (N/A)
- **Status:** applied

---

### 2026-06-30 — long-run-watch-closeout-errors-fixes-audit

- **Type:** breakthrough
- **Learning:** When a `/long-run-watch` session ends (completed, failed, or handed back), always publish a structured **Errors encountered** and **Fixes applied** audit in chat and in the final message-queue block — not only KPI/run outcomes.
- **Evidence:** Pipeline overnight watch fixed exp4 crash and resumed, but the closeout emphasized step completion; user had to ask separately about the exp4 error, the torque-passthrough workaround, and whether other failures occurred.
- **Applied to:** long-run-watch, learn-skill (POINTER)
- **Status:** applied

---

### 2026-06-30 — experiment-light-fix-action-space-semantics

- **Type:** anti-pattern
- **Learning:** Never treat a long-run-watch or experiment-fork light fix as done if it only unblocks a crash but leaves warmup/train on different action semantics — flag the invalid run; do not resume downstream steps until the user approves the design fix.
- **Evidence:** exp4 ref1 warmup used torque passthrough while train used `u`; pipeline marked exp4 completed; user rejected implement-first baseline→`u` work.
- **Applied to:** long-run-watch, hypothesis-experiment-cycle (POINTER), experiment-knowledge-pipeline (POINTER)
- **Status:** applied

---

### 2026-06-30 — define-fix-before-implement-experiment

- **Type:** anti-pattern
- **Learning:** On `/start-experiment-step` or pipeline rebuild, define and agree the fix design before editing experiment fork code when the bug is semantic (action space, warmup contract), not import/env only.
- **Evidence:** User stopped baseline→`u` implementation mid-flight; analysis for succeeded exps on hold.
- **Applied to:** experiment-knowledge-pipeline, implementation-discipline (POINTER), learn-skill (POINTER)
- **Status:** applied

---

### 2026-06-30 — pipeline-discuss-runs-include-video-paths

- **Type:** breakthrough
- **Learning:** When discussing pipeline experiment run results in chat (review, Phase 2/3 prep, overnight recap), always list **full MP4 paths** per arm — lead with `eval_best.mp4` and eval episodes, then train highlights from `artifacts_manifest.json` — alongside KPIs; never KPI-only or “videos exist” without paths.
- **Evidence:** User asked to watch Exp 4 SAC eval videos and requested path links whenever pipeline run results are discussed (faster than hunting `run_dir/videos/`).
- **Applied to:** experiment-knowledge-pipeline, experiment-visual-evidence, visual-output-verification (POINTER), video-frame-inspect (POINTER), hypothesis-experiment-cycle (POINTER), document-research (POINTER), long-run-watch (POINTER), learn-skill (POINTER), all other skills (N/A), all other rules (N/A)
- **Status:** applied

---

### 2026-06-30 — pipeline-closeout-video-findings

- **Type:** breakthrough
- **Learning:** On pipeline Phase 3 closeout, record **operator video findings** (not only KPI/agent frame pre-check) in §3.2 — especially when KPI and video diverge (e.g. high train ep, weak eval).
- **Evidence:** Exp 4 ref1 train ep 11: user saw pointing + sparse shutters + end spam + budget ignore; eval KPI lost to ref0.
- **Applied to:** experiment-knowledge-pipeline (POINTER via Phase 3 template), agent-reference investigation note, learn-skill (POINTER)
- **Status:** applied

---

### 2026-06-30 — pipeline-closeout-before-promote

- **Type:** anti-pattern
- **Learning:** When a pipeline experiment run succeeds or the user asks to promote a fork, **never** edit production `autonomous_control/` / `simulation/` / `render/` until the pipeline MD is in `4-documentation/` with Phases 2–4 documented, `overall_verdict` set, README/DECISIONS updated — treat “promote” as a **separate task after** pipeline closeout, even if the user requests promote in the same breath as results review.
- **Evidence:** Exp 7: agent jumped to reward-kernel promotion after KPI review; user stopped — “lets not get ahead you forgot to move the experiment note through the pipeline.”
- **Applied to:** experiment-knowledge-pipeline, hypothesis-experiment-cycle, implementation-discipline, document-research (POINTER), learn-skill (POINTER), all other skills (N/A), all rules (N/A)
- **Status:** applied

---

### 2026-06-30 — powershell-pid-automatic-readonly

- **Type:** anti-pattern
- **Learning:** In PowerShell watch/launch scripts, never assign to `$pid` — it is an automatic read-only variable; use `$lockPid` or `$processId` for lock-file PIDs.
- **Evidence:** `watch_exp9_then_exp8.ps1` stale-lock cleanup failed every retry with `Cannot overwrite variable PID`; Exp 8 auto-launch retried ~15×.
- **Applied to:** long-run-watch, learn-skill (POINTER), build-tool (POINTER)
- **Status:** applied

---

### 2026-06-30 — long-run-watch-no-duplicate-auto-launch

- **Type:** anti-pattern
- **Learning:** Before auto-launching the next experiment, read the profile **completion JSON** — if it exists, treat the step as done and never spawn another full run; use a one-shot launch flag and non-interactive `Start-Process python` (not `powershell -NoExit`).
- **Evidence:** Watch script retried Exp 8 launch until summary appeared; a later window (`18-55-51` run dir) duplicated full 50-ep training while `mpo_torque.json` already held results from `16-05-19`.
- **Applied to:** long-run-watch, experiment-knowledge-pipeline (POINTER), learn-skill (POINTER)
- **Status:** applied

---

### 2026-06-30 — check-completion-json-before-live-terminal

- **Type:** breakthrough
- **Learning:** When the user asks whether a training run "already ran", read the profile completion JSON and `results/*.log` DONE line **before** interpreting live terminal scrollback — live output may be a duplicate spawn.
- **Evidence:** User saw MPO train ep 23 while `mpo_torque.json` (16:38 UTC) and run dir `9998217164480175_*_16-05-19` already existed; active terminal was duplicate `9998217154247371_*_18-55-51`.
- **Applied to:** long-run-watch, experiment-knowledge-pipeline (POINTER), learn-skill (POINTER)
- **Status:** applied

---

### 2026-06-30 — pipeline-doc-bin-sync-tool

- **Type:** breakthrough
- **Learning:** Never manually move pipeline experiment notes between bins — on `/close-experiment-step` run `python .cursor/tools/pipeline/pipeline_doc.py close-phase --slug <slug>`; on `/start-experiment-step` run `check` first.
- **Evidence:** Exp 8/9 docs stayed in wrong bins while `current_phase` advanced; user asked to automate bin moves.
- **Applied to:** experiment-knowledge-pipeline, build-tool, learn-skill (POINTER), close-experiment-step command, start-experiment-step command
- **Status:** applied

---

### 2026-06-30 — pipeline-implement-nike-vs-plan-gate

- **Type:** breakthrough
- **Learning:** On pipeline Phase 1 / implement, run the Nike-vs-plan gate yourself — **Nike mode** (build now) only when Phase 0.3 has hook + sibling + smoke, single delta, user approved build, no hook TBD, fork-only, no semantic-contract risk; **notify the user in chat with a brief justification before the first fork edit**; **plan mode** (stop and ask the user) when any plan signal fires or an upstream/production bug is suspected — never agent-only decide those cases.
- **Evidence:** Exp 10: Phase 0.3 + Exp 8 sibling made a separate build plan redundant; user asked when planning is worth it and that missing plan/upstream-bug calls must always go to the operator.
- **Applied to:** experiment-knowledge-pipeline, hypothesis-experiment-cycle, implementation-discipline (POINTER), start-experiment-step command, learn-skill (POINTER), architecture-planning (POINTER), all other skills (N/A), all rules (N/A)
- **Status:** applied

---

- **Type:** anti-pattern
- **Learning:** After a pipeline run completes and you deliver evaluation or operator verdict in chat, **proactively** append missing `## Phase 2` / `## Phase 3` blocks and run `pipeline_doc.py close-phase --slug <slug>` — do not wait for `/close-experiment-step` and do not leave docs in `2-run/` with stale `current_phase`.
- **Evidence:** Exp 8/9: runs evaluated and discussed in chat; pipeline MD stayed in `2-run/` at phase 2 until user asked again — same class of mistake as Exp 7 bin skip.
- **Applied to:** experiment-knowledge-pipeline, hypothesis-experiment-cycle, close-experiment-step command, learn-skill (POINTER), long-run-watch (POINTER), all other skills (N/A), all rules (N/A)
- **Status:** applied

---

### 2026-07-02 — atomic-one-hypothesis-per-pipeline-slug

- **Type:** anti-pattern
- **Learning:** When a charter names two independent experiment directions (e.g. cadence sweep + hyperparam screen), **stop Phase 0** and use **AskQuestion** to force the operator to split into **two pipeline slugs** (`/init-experiment` twice) — one atomic hypothesis per doc; do not mix both tracks in one spec unless the user explicitly accepts a single sequential slug **and** the overnight runner implements every charter step.
- **Evidence:** Exp 13 (`ml_mpo_learn_cadence_hparams`): Track B hparam arms were built but never run; `--overnight` only executed Track A0+A1; user lost reserved GPU night budget and flagged watcher/pipeline gap across stages.
- **Applied to:** experiment-knowledge-pipeline, init-experiment command, start-experiment-step command, hypothesis-experiment-cycle, architecture-planning (POINTER), learn-skill (POINTER), all other skills (N/A), all rules (N/A)
- **Status:** applied

---

### 2026-07-02 — mpo-mstep-rsample-detach

- **Type:** anti-pattern
- **Learning:** In MPO M-step, always `.detach()` sampled actions before calling `log_prob(dist_online, actions)` when actions were drawn from the same `dist_online` via `rsample()` — score-function and reparameterization gradients cancel exactly to zero for Gaussian heads, silently killing the Q-weighted policy update for those dims.
- **Evidence:** Exp 14 build review: `_factorized_mpo_agent.py` line 236 — move/shutter Gaussian heads received zero M-step gradient; only KL constraint updated them.
- **Applied to:** review-experiment-build (canonical §2), hypothesis-experiment-cycle (fork sizing checklist UPDATE), experiment-knowledge-pipeline (N/A — skill chain pointer only), all other skills (N/A), all rules (N/A)
- **Status:** applied

---

### 2026-07-02 — tanh-jacobian-sign

- **Type:** anti-pattern
- **Learning:** For tanh-squashed Gaussian log-prob, the Jacobian correction **subtracts** `log(1−a²)` (equivalently, adds a positive term): `log π(a) = log π_z(z) − log(1−a²)`; writing `+ log(1−a²)` is wrong and silently underestimates density near the tanh boundary.
- **Evidence:** Exp 14 build review: `_factorized_actor.py` `_log_prob_flat` had inverted sign; gradients unaffected (Jacobian is constant w.r.t. actor params) but log_prob values were numerically wrong.
- **Applied to:** review-experiment-build (canonical §3), hypothesis-experiment-cycle (POINTER via fork sizing checklist), all other skills (N/A), all rules (N/A)
- **Status:** applied

---

### 2026-07-02 — review-experiment-build-gate

- **Type:** breakthrough
- **Learning:** Insert a pre-run code review gate (`review-experiment-build` skill) for experiments with new ML components (custom actor heads, custom action spaces, custom episode loops) — this caught a critical zero-gradient bug and two medium bugs before any compute was spent.
- **Evidence:** Exp 14: 4 bugs found (1 critical, 1 medium, 2 low) all fixed before first screen run; the critical bug would have silently produced a non-learning experiment.
- **Applied to:** review-experiment-build (canonical home), experiment-knowledge-pipeline (Phase 1 skill chain UPDATE), hypothesis-experiment-cycle (fork sizing checklist UPDATE), all other skills (N/A — gate is fork-review domain only), all rules (N/A)
- **Status:** applied

---

### 2026-07-02 — run-instructions-stage-table

- **Type:** anti-pattern
- **Learning:** In experiment README and pipeline `### 1.3`, use a **numbered step table** (command → stage → purpose → artifact) — never a flat list of flags without saying which is hparam sweep vs full training vs eval; operators cannot infer `--screen` vs `--full` from flag names alone.
- **Evidence:** Exp 14 README listed `--screen`, `--full`, `--eval-baseline` under one comment block; user asked "which runs the hparam sweep which runs the full training on the found hparam."
- **Applied to:** experiment-knowledge-pipeline (reference.md 1.3 template UPDATE), review-experiment-build (§11 UPDATE), learn-skill (POINTER), all other skills (N/A), all rules (N/A)
- **Status:** applied

---

### 2026-07-02 — phase1-run-instructions-required

- **Type:** anti-pattern
- **Learning:** On Phase 1 close, always append `### 1.3 Run instructions (How to execute)` to the pipeline MD with copy-paste `conda activate auto-sat`, `cd`, smoke/screen/full/eval commands, mutex slug, and `results/*.json` paths — experiment `README.md` alone is not sufficient; builders repeatedly skip this and block the operator at run time. Commands must be **cwd-correct** (no `Path('backend/...')` from inside the experiment folder) — prefer `python run.py --check-mutex` over fragile `python -c` one-liners; label `--verify`/`--smoke` as Phase 1 one-time gates, not prerequisites before `--screen`.
- **Evidence:** Exp 14: Phase 1 omitted 1.3 until user flagged; then 1.3 mutex `python -c` used repo-relative path from experiment cwd → `ModuleNotFoundError`; user ran `--screen` directly (correct — mutex auto-acquired).
- **Applied to:** experiment-knowledge-pipeline (document + close workflow UPDATE, reference.md exit criteria), review-experiment-build (§11 checklist UPDATE), hypothesis-experiment-cycle (fork sizing checklist POINTER), learn-skill (POINTER), all other skills (N/A), all rules (N/A)
- **Status:** applied

---

### 2026-07-02 — overnight-charter-scope-audit

- **Type:** anti-pattern
- **Learning:** Before marking an overnight or `/long-run-watch` session **completed**, diff charter Phase 0.3 execution order + arm list against completion JSON and `results/` artifacts — if any charter step has zero artifacts, report **scope incomplete** in the closeout audit (not `status: completed` alone) and ask the user to resume, extend the runner, or split the experiment; never treat exit 0 + summary JSON as full Phase 2 success.
- **Evidence:** Exp 13: `pipeline_overnight_batch.json` and `learn_cadence_overnight.json` show `status: ok` but zero `hparam_*.json`; watcher closeout did not flag deferred Track B; Phase 2 doc never appended.
- **Applied to:** long-run-watch, experiment-knowledge-pipeline (POINTER), hypothesis-experiment-cycle (POINTER), ml-pipeline-overnight-batch-10-13 profile, learn-skill (POINTER), all other skills (N/A), all rules (N/A)
- **Status:** applied

---

### 2026-07-02 — screen-runner-smoke-wiring

- **Type:** anti-pattern
- **Learning:** When Phase 1 smoke is single-episode only, extend `--verify` with **stage-runner binding checks** (every symbol called in `_screen_runner` / artifact helpers must be imported at module level) — smoke does not exercise post-eval export paths; document whether plain `--screen` trims or exports (do not assume operators know the default).
- **Evidence:** Exp 14: `--screen` crashed after eval with `NameError: export_screen_arm_artifacts` (missing import); smoke passed because it never called `run_screen_arm` artifact export.
- **Applied to:** review-experiment-build, hypothesis-experiment-cycle, experiment-knowledge-pipeline, implementation-discipline (POINTER), learn-skill (POINTER), all other skills (N/A), all rules (N/A)
- **Status:** applied

---

### 2026-07-03 — phase2-export-artifacts-not-trim-default

- **Type:** anti-pattern
- **Learning:** For pipeline Phase 2 when behavior is in scope, never launch `--screen` / `--full` with default artifact trim when `profile.json` enables `export_episode_reward_plots` or `train_episode_videos` — use `--export-artifacts` in Phase 1.3, overnight auto-launch, and operator runbooks unless the user explicitly passes `--trim-artifacts`; if trimmed, closeout must report **artifact gap** (no PNG/MP4 paths), not KPI-only success.
- **Evidence:** Exp 14: `profile.json` has `export_episode_reward_plots: true`, `train_episode_videos: 3`; overnight `--screen` + `--full` ran with `trim_artifacts: true` → only `warmup_preview` PNG on disk; user expected same reward plots/MP4s as sibling experiments ("where do I see the plot?").
- **Applied to:** experiment-knowledge-pipeline, experiment-visual-evidence, long-run-watch, review-experiment-build, hypothesis-experiment-cycle (POINTER), visual-output-verification (POINTER), video-frame-inspect (POINTER), learn-skill (POINTER), all other skills (N/A), all other rules (N/A)
- **Status:** applied

---

### 2026-07-04 — ask-skill-location-before-create

- **Type:** anti-pattern
- **Learning:** Before creating a new skill, **AskQuestion where it should live** — user personal (`~/.cursor/skills/`, e.g. `dev-skills/{name}/`) vs project (`.cursor/skills/{name}/`) — unless the user already stated; never default to project without asking.
- **Evidence:** `log-answered-questions` was created under project `.cursor/skills/`; user corrected it should be a user skill and had to be moved to `~/.cursor/skills/dev-skills/`.
- **Applied to:** learn-skill, new-skill-integration, all other project skills (N/A), all rules (N/A)
- **Status:** applied

---

### 2026-07-07 — report-constants-verify-source

- **Type:** anti-pattern
- **Learning:** Before writing any constant value into a nomenclature or parameter table, verify it against the canonical source file — never copy from a benchmark run config or an earlier draft; implementation-detail constants (internal discretization params such as sensor ray sample counts and observation-line bin counts) must be omitted from the reader-facing parameter tables because they are invisible to the reader and change with performance tuning.
- **Evidence:** Nomenclature table listed `strip ray samples = 96` (benchmark value from `sensor_ray_batch` experiment, not the canonical default) and `observation-line bins = 100` (actual value is `DEFAULT_CAMERA_OBSERVATION_LINE_N_BINS = 101` in `SIMULATION.py`); both were removed as implementation details after user correction.
- **Applied to:** generate-research-report (anti-patterns section), update-research-report (verify-before-editing + what-belongs-in-tables), all other skills (N/A), all rules (N/A)
- **Status:** applied

---

### 2026-07-07 — report-reader-frame-no-lla

- **Type:** anti-pattern
- **Learning:** Never expose LLA-specific geodetic details (longitude, latitude band, meridian labels) in reader-facing prose — the reader cares about orbit geometry (altitude, pass arc, target count), not internal coordinate bookkeeping; state instead that the specific ground track is arbitrary and results transfer to any equivalent pass.
- **Evidence:** "meridian ground stripe (longitude 0°, latitude 89.65°–90°N)" was confusing to the user; replaced with "ground corridor directly below the orbit plane" and a note that geographic location is irrelevant since the agent only sees orbit-plane angles.
- **Applied to:** generate-research-report (anti-patterns), update-research-report (new reader-frame section + anti-patterns), all other skills (N/A — orbit/LLA specifics out of scope), all rules (N/A)
- **Status:** applied

---

### 2026-07-07 — report-no-internal-code-refs-in-prose

- **Type:** anti-pattern
- **Learning:** Never reference internal notebook names, script paths, or code artefacts (e.g. "notebook~07 overflight") in reader-facing prose — the reader does not have the repo open; replace with a plain description of the behaviour or system, and use `\missingfigure{}` from the `todonotes` package as a visible placeholder when a figure is the right substitute.
- **Evidence:** "notebook~07 overflight" appeared twice in the introduction as the name for the deterministic baseline; user flagged this as opaque; replaced with "deterministic pre-scheduled baseline" and added `\missingfigure` for the overflight phases diagram.
- **Applied to:** generate-research-report (anti-patterns), update-research-report (anti-patterns), all other skills (N/A), all rules (N/A)
- **Status:** applied

---

### 2026-07-07 — report-define-project-terms-at-first-use

- **Type:** anti-pattern
- **Learning:** Define every project-specific abstraction at its first use in the text — never assume the reader knows terms like "shutter budget", "arm", "warmup/eval episodes", or any internal variable name (`learning_mode`, `shutter_gym`, etc.); replace code-internal variable names with plain English descriptions throughout reader-facing prose.
- **Evidence:** "shutter budget of ten captures per pass" appeared in §1.2 before any definition; `learning_mode`, `shutter_gym`, `shutter_meaningful_fraction` appeared raw in experiment descriptions; "arm" and "warmup/eval episodes" were used in the master table without prior explanation.
- **Applied to:** generate-research-report (anti-patterns), update-research-report (anti-patterns), all other skills (N/A), all rules (N/A)
- **Status:** applied

---

### 2026-07-10 — report-figure-curate-not-dump

- **Type:** anti-pattern
- **Learning:** Never commit the full experiment dump as report evidence — light-clean, then copy only selected plots/frames into `docs/report/semester-project/figures/` (optional `figures/candidates/` for real alternates), tag section/status in `FIGURES_TODO.md` (or a figure manifest), leave KPI/provenance under experiment `results/`; backups are real alternate artifacts marked `backup`, not synthetic invented data.
- **Evidence:** Report closeout discussion: user asked select+sort into docs vs commit all data vs clean-then-commit; agreed curated report tree + placement tags; `*.mp4` already gitignored; `FIGURES_TODO.md` already maps figures → sections.
- **Applied to:** generate-research-report (canonical figure freeze), document-research, bulk-change-triage-commit, visual-output-verification, experiment-knowledge-pipeline/skill-chain (Phase 4.3), create-update-presentation (POINTER), experiment-visual-evidence (Forbidden), learn-skill/reference (table), video-frame-inspect (POINTER), all other skills (N/A), units/simulation-sso/render-view-only/math-physics/python-runtime (N/A)
- **Status:** applied
