# Report direction log

Living record of report-scoping discussions. Use this when revising Abstract, Introduction, or framing Results — not as submission text.

**Last updated:** 2026-06-27

---

## People & placement

| Role | Name | Notes |
|------|------|--------|
| ETH examiner / chair | Prof. Dr. Marco Hutter (RSL) | Primary academic audience |
| Industry supervisor | Alejandro Torrents Rufas (Beyond Gravity, MPP group) | Semester project host |
| Industry contact | Mathias Burkhalter | Acknowledgements |
| Author | Cédric Grieder | |

Title page in `main.tex` reflects this. **Acknowledgements section not yet written.**

---

## Narrative spine (agreed direction)

1. **Use case:** Climate / environmental monitoring — **rainforest imaging** where clouds are prevalent.
2. **Problem:** Deterministic baseline (fixed nadir + scheduled shuttering) **images every target vector blindly**; wastes onboard memory/downlink on cloud-occluded frames; scientists lose usable observations.
3. **Hypothesis:** A **learned policy** using **simulated vision** can outperform that deterministic strategy by timing captures and pointing for quality — “smart autopilot” under safety constraints.
4. **Comparison:** **Notebook 07 baseline overflight** vs **MPO eval** on **matched environment setups** (same altitude, clouds, target layout per episode).
5. **Evidence (current):** **Qualitative** multi-seed behavior; **quantitative headline numbers deferred** to Results until final runs frozen.
6. **Tone:** **Hypothesis-driven**, **problem-heavy** abstract; simplifications high-level in abstract, **full simplification list** in Introduction / Methods.
7. **Non-goals:** Flight hardware, multi-satellite, SOTA RL benchmark chasing; 3D / richer terrain = logical extensions, not deliverables.

**Terminology preference:** “Observation yield” / successful captures weighted by quality; emphasize **baseline vs learned**, **rainforest + clouds**, **vision-driven autopilot**, **safety constraints for ML**.

---

## Session 1 — LaTeX boilerplate (2026-06-24)

- Created `docs/report/semester-project/` — shorter than bachelor thesis reference.
- Structure: Abstract → Intro (Motivation, Objective, Contributions) → Methods → Results → Discussion → Conclusion → Appendix.
- Companion to `docs/presentation/` slides (constants live there; report carries protocol + evidence).
- Build: `.\compile_win.ps1` (MiKTeX). Fixed `microtype` expansion + removed `cleveref` for stable builds.

---

## Session 2 — Scope questionnaire (50 questions)

Answers collected via structured multiple-choice (+ “Other” where noted). Grouped below by theme.

### A. Problem & motivation (Q1–10)

| Q | Topic | Answer |
|---|--------|--------|
| 1 | EO use case | **Climate** monitoring (rainforest framing in later answers) |
| 2 | Why autonomous | **A + B:** ground loop too slow; clouds change faster than replan cycles |
| 3 | Cloud failure mode | **Wasted shutter** / downlink on useless frames |
| 4 | Who benefits | **Scientists** (end users of imagery) |
| 5 | Cost of miss | **All:** science value, downlink/memory, actuator wear — worth mentioning |
| 6 | Why polar / stripe | **Not orbit-specific.** Any circular orbit at one overflight instant is equivalent. Polar was a convention; RL polar cost irrelevant to scope. Stripe = simplified coordinate-defined targets. |
| 7 | Core pain point | **Both** timing (when to shoot) and pointing (how to orient) |
| 8 | Operator baseline mental model | **Fixed nadir + pre-planned shutter times** |
| 9 | Mech Eng angle | **ML as tool** — mechanics secondary in narrative (still model dynamics, safety, ray tracing) |
| 10 | Elevator sentence | **Learn when/how to point** so cloud-occluded passes still maximize useful imagery |

### B. Mission scenario & constraints (Q11–18)

| Q | Topic | Answer |
|---|--------|--------|
| 11 | Successful overflight | **Combination:** capture count + quality; at **zero reward** ≈ maxed capability, **memory-limited**; avoided clouds + pointed for max image quality |
| 12 | ~50 targets / stripe | **Simplified choice** for rainforest multi-area sampling; real use case unclear on area definition; coordinates work as proxy |
| 13 | Random altitude | **Orbit uncertainty + GSD/geometry generalization**; **must compare matched scenarios** (baseline vs MPO eval same env setup) |
| 14 | Safety highlight | **Balanced:** wheel saturation, off-nadir envelopes, rates/stillness |
| 15 | Clouds in motivation | **Defining challenge** — cloud-aware EO is the hook |
| 16 | Secondary camera | **In scope** for narrative (dual-camera / vision) |
| 17 | Shutter budget | **Mention briefly** (OBC-like constraint, not headline) |
| 18 | Primary limitation to flag | **2D simplification** (detail full list in intro) |

### C. Learning approach (Q19–26)

| Q | Topic | Answer |
|---|--------|--------|
| 19 | Why RL | **Sequential decisions under uncertainty** |
| 20 | Why MPO | **Don’t stress in abstract**; practically copied from prior uni project (CartPole, probabilistic ML) |
| 21 | Direct torque framing | **Standard low-level RL** — brief mention, not architecture essay |
| 22 | Observation value | **Successful captures weighted by quality & coverage** |
| 23 | Essential reward terms | **Capture quality**, **cloud fraction**, **area/target novelty** |
| 24 | Primary baseline | **Notebook 07 baseline overflight** |
| 25 | Success threshold | **Beat baseline** (conceptual) |
| 26 | Main claim | **Higher yield under cloud occlusion** |

### D. Objectives & non-goals (Q27–34)

| Q | Topic | Answer |
|---|--------|--------|
| 27 | Primary objective | **Demonstrate cloud-aware learned control in simulation** |
| 28 | Secondary objectives | **Artifacts**, **documented baselines**, **reward design** (not render-split as research focus) |
| 29 | Charter invariants | **Not research focus** — technical sidenote at most; user questioned relevance to scope |
| 30 | Sim/render pipeline as objective | **Means to RL experiments**, not equal headline |
| 31 | Scientific question | **Can RL exploit gaps/timing under clouds?** |
| 32 | Supervisor “done” | **Working demo** (video) + documented pipeline |
| 33 | Non-goals | **All listed:** no flight, no 3D/real terrain as deliverable, no multi-sat, no SOTA chasing; 3D and stronger RL = extensions |
| 34 | Bachelor thesis link | **LaTeX structure reference only** — not narrative continuity |

### E. Results & abstract claims (Q35–42)

| Q | Topic | Answer |
|---|--------|--------|
| 35 | Headline number | **Qualitative only** for now |
| 36 | vs baseline | **nb07** |
| 37 | Evidence strength | **Multi-seed** — wording can reflect that, but no hard numbers in abstract yet |
| 38 | Qualitative success | **Prioritizes high-value / novel targets** under budget |
| 39 | Baseline failure | **Naively images all target vectors**; cannot distinguish what sensors see |
| 40 | Not in abstract | **All quantitative claims** held back for now |
| 41 | Trade-offs | **None prominent yet** |
| 42 | Hero artifacts | **Suggest as reader:** baseline vs MPO comparison, learning curves, model complexity vs reward, screenshots, links to baseline + train/eval videos (placeholders OK) |

### F. Audience, rigor & wording (Q43–50)

| Q | Topic | Answer |
|---|--------|--------|
| 43 | Audience | **ETH examiner (Hutter)** + industry context above |
| 44 | Rigor style | **Hypothesis-driven** |
| 45 | Novelty vs PDF | **Unclear / deferred** — user asked “what is the question?”; treat as: implemented cloud-aware pipeline beyond original PDF, but don’t over-claim without explicit decision |
| 46 | Abstract limitation | **High-level simplifications only**; exhaustive list in Introduction |
| 47 | Hierarchical planner vision | **Short paragraph** — current work as step toward mission planner over OBC |
| 48 | Terminology | Rainforest imaging; **learned vs deterministic**; vision for smart autopilot; **safety constraints for ML approaches** |
| 49 | Operational realism | **Very simplified** — only close problem domain (attitude, safety, control, ray tracing, basic orbit; single pass) |
| 50 | Abstract structure | **Problem-heavy** (strong opening sentences) |

---

## Decisions applied to LaTeX (2026-06-24)

Files updated from questionnaire:

- `sections/abstract.tex` — rainforest/cloud waste problem; hypothesis; MPO + matched nb07 eval; qualitative multi-seed claim; 2D single-pass limit.
- `sections/introduction.tex` — expanded Motivation, Objective (primary/secondary/hypothesis/scope/long-term), Contributions.
- `main.tex` — title, supervisors, Beyond Gravity institute line.

**Explicitly not emphasized (per user):** charter invariants as research contributions; MPO algorithm novelty; polar-orbit special case.

---

## Session 3 — Platform narrative in report (2026-06-27)

User reflection: most semester effort went into infrastructure (simulation kernel, timesteps, UI wiring, parallelization trade-offs) rather than mature ML benchmarks; thesis still justified if cloud-aware learning insight is demonstrated.

**Applied to LaTeX:**

- `sections/introduction.tex` — Contributions split into Platform / Mission / Evaluation / Evidence; sentence on effort allocation.
- `sections/methods.tex` — new **Software architecture** subsection (canonical sim, timesteps, seeded randomness, notebook cycle, parallelization).
- `sections/discussion.tex` — Interpretation ties platform to credible comparison; Limitations adds **Effort allocation** bullet.
- `sections/conclusion.tex` — platform as primary deliverable; Outlook lists 3D/propagator/real imagery/multi-orbit extensions.

Personal/process notes (50% time, 3 months) stay in this log only — not submission text.

---

## Open items / follow-ups

- [ ] Write **Acknowledgements** (Hutter, Torrents Rufas, Burkhalter, Beyond Gravity).
- [ ] Add **quantitative sentence** to abstract once final MPO vs nb07 metrics frozen.
- [ ] Introduction: **enumerated simplification table** (modeled vs not modeled) — user requested full list in intro/problem description.
- [ ] Results: hero artifacts per Q42 (comparison table, learning curves, complexity–reward, video links).
- [ ] Decide whether to add one sentence on **novelty vs semester PDF** (Q45 unresolved).
- [ ] Optional: sentence on **safety constraints for ML** as contribution (Q48) — currently light in draft.

---

## Raw notes (verbatim snippets worth preserving)

> “We don't care if it is polar or equatorial — at one overflight instant any circular orbit is the same. Polar was convention; RL polar cost doesn't matter for scope.”

> “If we get 0 reward we maxed out capability and are memory limited — successfully avoided clouds and pointed for maximal image quality.”

> “Baseline naively images all target vectors and cannot distinguish what the sensors are seeing.”

> “Compare equal scenarios — baseline and MPO eval must have the same environment setup.”

> “Bachelor thesis folder is only for LaTeX structure / ETH report components reference.”

---

## How to use this log

1. Before editing Abstract/Intro, skim **Narrative spine** and **Open items**.
2. When new scoping answers arrive, append a dated **Session N** section — don’t delete old decisions; strike through if superseded.
3. When a decision lands in LaTeX, note the file under **Decisions applied**.
