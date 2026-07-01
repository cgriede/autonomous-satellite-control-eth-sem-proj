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
