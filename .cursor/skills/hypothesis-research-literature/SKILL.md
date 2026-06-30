---
name: hypothesis-research-literature
description: >-
  Finds and cites prior work before hypothesis experiments: search docs/research/,
  download PDFs, scrape lecture/LMS materials into research/, write literature basis
  for hypothesis docs and analysis cards. Use when starting hypothesis-experiment-cycle,
  justifying an encoder/architecture fork, writing Related Work, when the user mentions
  taking or teaching a lecture/course, or when the user asks for research before an experiment.
disable-model-invocation: true
---

# Hypothesis Research Literature

Run **before** designing or forking under [`hypothesis-experiment-cycle`](../hypothesis-experiment-cycle/SKILL.md). For numbered ML pipeline experiments, also update `docs/experiments/pipeline/{bin}/{NN}-{slug}.md` **`## Literature`** via [`experiment-knowledge-pipeline`](../experiment-knowledge-pipeline/SKILL.md).

After a broad literature review, persist synthesis with [`document-research`](../document-research/SKILL.md) (investigation note + [DECISIONS.md](../../../docs/research/DECISIONS.md)).

## Read first (avoid duplicate / scope creep)

Before any new literature search or fork proposal:

1. [`docs/research/PROJECT_KNOWLEDGE.md`](../../../docs/research/PROJECT_KNOWLEDGE.md)
2. [`docs/research/DECISIONS.md`](../../../docs/research/DECISIONS.md) — do not re-open `rejected` without user reversal
3. [`docs/ml/experiments/STATUS_*.md`](../../../docs/ml/experiments/) + existing `results/*.json`

If the topic is already `rejected` or an arm already has a verdict, stop and point to the stored row.

## When to use

- New experiment slug under `backend/scripts/experiments/<slug>/`
- New hypothesis branch (`<hypothesis>.md`, analysis card §1)
- Report / semester-project Related Work for an architectural change
- User asks to "look up papers", "justify experiment", or "research first"
- User mentions **taking, teaching, or referencing a lecture/course** (ETH Moodle, edX, course URL, course number)

## Two local libraries

| Library | Path | Contents |
|---------|------|----------|
| **Published papers** | [`docs/research/`](../../../docs/research/) | arXiv / venue PDFs, `LITERATURE_HIGHLIGHTS.md` |
| **Lecture / course materials** | [`research/<slug>/`](../../../research/) | Slides, problem sets, ZIPs, code scraped from LMS (e.g. `research/mpc_lecture/`) |

Search **both** before web search. Lecture folders are supporting knowledge for control-theory, ML, or domain context—not substitutes for peer-reviewed citations unless the hypothesis is course-shaped (e.g. MPC baseline design).

## Workflow (papers)

```text
1. Scope question  →  2. Search local library  →  3. Gap? web search  →  4. Download PDF
        →  5. Add highlights  →  6. Write literature basis in hypothesis doc
```

### Step 1 — Scope the research question

One sentence: *what structural change and what outcome do we expect?*

Example: "Compressing per-target bearing vectors before fusion should improve sample efficiency vs flat 105-D scalar MLP."

### Step 2 — Search local library first

| Resource | Path |
|----------|------|
| Paper PDFs | [`docs/research/`](../../../docs/research/) |
| Section highlights | [`docs/research/LITERATURE_HIGHLIGHTS.md`](../../../docs/research/LITERATURE_HIGHLIGHTS.md) |
| Paper index | [`docs/research/README.md`](../../../docs/research/README.md) |
| Lecture / course materials | [`research/`](../../../research/) — each course has its own `README.md` |

Grep highlights, paper README, and `research/*/README.md` before web search.

### Step 3 — Acquire missing papers

- Download to `docs/research/{arxiv_or_year}_{short_slug}.pdf`
- arXiv: `https://arxiv.org/pdf/<id>`
- Update `docs/research/README.md` index row
- Add **§ highlights** to `LITERATURE_HIGHLIGHTS.md` (section table + project mapping)

Ask user before `pip install` for PDF tooling; prefer direct PDF URLs.

### Step 4 — Open for human review (Windows)

```powershell
Start-Process "d:\code\sem-proj-asc\docs\research\<file>.pdf"
```

### Step 5 — Literature basis in experiment artifacts

**Required before first fork run:**

1. **`<slug>/<hypothesis>.md`** — section **Literature basis** (3–6 bullets):
   - Citation (author, year, arXiv/venue)
   - **Section / figure** read (from highlights doc)
   - **Claim** from paper
   - **Mapping** to this fork (one line)

2. **`results/<id>_analysis.md`** — section **1 Motivation / literature** must echo the same citations (analysis card template).

3. **Optional:** `docs/ml/experiments/<slug>_YYYY-MM.md` for report reuse (long-form).

4. **Broad synthesis:** [`document-research`](../document-research/SKILL.md) → investigation note + DECISIONS rows when the review spans multiple experiments or records reject/defer choices.

### Step 6 — Tie to experiment cycle

Then follow [`hypothesis-experiment-cycle`](../hypothesis-experiment-cycle/SKILL.md): frozen baseline, fork, JSON contract, verdict.

**Stop rule:** If no literature supports the fork and no strong internal baseline (e.g. overnight JSON), narrow the hypothesis or run a **diagnostic-only** arm first.

## Workflow (lecture materials — user-centric scrape)

**Trigger:** User says they are enrolled in / taking / following a course, or names a lecture without giving a link.

**Ask before scraping** (do not guess URLs or log in silently). Collect:

| Ask | Why |
|-----|-----|
| **Course website URL** | Direct link to Moodle/course home (e.g. `…/course/view.php?id=…`) |
| **Course id / title / semester** | Slug + README (e.g. `151-0660-00L`, FS2026) |
| **Login method** | Shibboleth org, guest OK?, password course?, other SSO |
| **Your login in Cursor browser** | Gated LMS: user signs in in the browser panel; agent does **not** take passwords in chat |
| **What to download** (if ambiguous) | See scope below; confirm before large pulls |

**Download scope** — ask when the user says "materials", "everything", or does not specify:

| Scope | Includes | Skip unless asked |
|-------|----------|-------------------|
| **Default** | PDF, PPTX, ZIP, code (`.m`, `.mlx`, `.py`, `.ipynb`, `.mat`, …) | — |
| **Slides only** | Lecture/recitation PDFs, PPTX | Problem sets, code, exams |
| **Code / project only** | ZIP archives, scripts, live notebooks | Slide PDFs |
| **Exams only** | Past exams, supplementary sheets | Rest |
| **Full mirror** | Default + videos, forum exports, recordings | Warn about size/time first |

If the user does not answer, use **default** (PDF + ZIP + code). State the chosen scope in the proposal and in `research/<slug>/README.md`.

**Propose** once URL is known or after user confirms they will provide it:

> "I can download *[scope, e.g. slides, problem sets, ZIPs, and code]* from *[course]* into `research/<slug>/`. Please share the **course URL** and **how you log in** (e.g. ETH Moodle → Shibboleth → ETH Zürich). When the browser opens, sign in there and reply **logged in**—I won't ask for your password in chat."

If the user only names a course (no URL), search the institution catalogue (e.g. [IDSC lectures](https://idsc.ethz.ch/education/lectures/)) for the Moodle link, then confirm with the user before scraping.

Then:

```text
0. Intake (URL + login + download scope)  →  1. Resolve course  →  2. Create research/<slug>/
        →  3. Open URL in browser; user authenticates  →  4. Crawl resources (filter by scope)
        →  5. Download + organize  →  6. README inventory  →  7. Link from hypothesis doc
```

### Lecture scrape — step by step

0. **Intake** — Get **course URL**, **login path**, and **download scope** (default: PDF + ZIP + code). Never store passwords, cookies, or `sesskey` in the repo. If login fails (guest denied, wrong org), report what you saw and ask user to retry in the browser.

1. **Resolve course** — course number, title, semester. Check [`research/`](../../../research/) for an existing folder; skip re-download if fresh unless user asks.

2. **Slug** — `research/{topic}_lecture/` or `research/{course_number_sanitized}/` (lowercase, underscores). Example: `research/mpc_lecture/`.

3. **Open & authenticate** — Navigate to the URL in the **Cursor browser**. Unlock for the user; they complete Shibboleth / SSO / password in the UI. Continue only after user confirms **logged in** or the course page loads with their account (e.g. username in header, not "Gast").

4. **Discover files** — On the course page, collect resource links from the sidebar index. **Filter by agreed scope** (e.g. skip `mod/url` video links and forums unless full mirror). For each included `mod/resource`, resolve the `pluginfile.php/…/mod_resource/content/…` download URL from the resource HTML (authenticated `fetch` in browser context).

5. **Download** — Only files matching scope. Use the authenticated browser session (CDP `fetch` → base64 batches, or equivalent). Do **not** export cookies or credentials to disk. Shell `curl` without session will fail (303 to login).

6. **Organize** — Default layout under `research/<slug>/`:

   | Subfolder | Put here |
   |-----------|------------|
   | `lectures/` | Slide PDFs |
   | `recitations/` | Recitation PDFs / PPTX |
   | `problem_sets/` | Weekly sets + solutions |
   | `exams/` | Past exams, supplementary sheets |
   | `code/` | `.m`, `.mlx`, loose scripts |
   | `project/` | ZIP handouts; **extract** archives into named subfolders |

7. **README** — Course title, LMS URL, download date, **scope used**, file counts, section list. No secrets.

8. **Hypothesis tie-in** — If the course topic matches an active experiment, add bullets to **Literature basis** citing lecture material:

   ```markdown
   - **Zeilinger, ETH 151-0660-00L (FS2026)**, Lecture 6 — tube MPC feasibility/stability; **maps to** robust constraint handling in satellite pointing fork.
   ```

   State mismatch when the course plant differs from the repo sim (e.g. truck MPC vs reaction-wheel sat).

### Lecture scrape — platforms

| Platform | Notes |
|----------|--------|
| ETH Moodle (`moodle-app2.let.ethz.ch`) | Ask URL + **Shibboleth org** (usually ETH Zürich); guest often denied; course index in left panel |
| Public course pages | IDSC / course catalogue may link to Moodle only; scrape LMS after login |
| arXiv / open PDFs | Use paper workflow into `docs/research/`, not `research/` |

### Lecture scrape — anti-patterns

- Scraping without **course URL**, confirmed **login path**, or agreed **download scope**
- Downloading videos / forum dumps when user only wanted slides (or when scope was never clarified—use default instead)
- Asking the user to paste **passwords** in chat (browser login only)
- Scraping without user login on gated courses
- Storing session cookies, passwords, or `sesskey` in the repo
- Dumping everything flat in one folder (hard for the next agent to skim)
- Treating lecture slides as peer-reviewed citations without labeling them as course notes
- Re-downloading 50+ MB when `research/<slug>/README.md` already documents a recent pull

## Terminology (this repo)

| Phrase | Use for |
|--------|---------|
| State representation learning (SRL) | Encoder / embedding experiments |
| Entity-based / set-structured observations | Per-target bearing + mask vectors |
| Multimodal fusion | Vision CNN + non-vision streams |
| Group bottleneck | `Linear(n_targets → embed_dim)` |
| Robotic priors | Physics-shaped SRL losses (future) |

Full mapping: [reference.md](reference.md)

## Starter library (observation / RL)

| PDF in `docs/research/` | Use when |
|-------------------------|----------|
| `2506.17518_srl_survey_drl.pdf` | Taxonomy, Related Work framing |
| `bruin2018_integrating_srl_into_rl.pdf` | Shared trunk + joint SRL/RL training |
| `gorishniy2022_numerical_feature_embeddings.pdf` | Scalar / vector embedding before MLP |
| `2206.02855_efficient_entity_based_rl.pdf` | Per-entity structure vs flatten |
| `jonschkowski2015_..._robotic_priors.pdf` | Physics priors for representations |
| `2410.17551_multimodal_information_bottleneck_rl.pdf` | Multimodal compression |

## Starter library (lecture / course — `research/`)

| Folder | Use when |
|--------|----------|
| [`research/mpc_lecture/`](../../../research/mpc_lecture/) | MPC theory, tube/robust MPC, ETH 151-0660-00L slides & MATLAB project |

Add a row here when a new course is scraped.

## Literature basis template

```markdown
## Literature basis

- **Gorishniy et al. 2022** (NeurIPS), §3–4 — embedding numeric features before backbone mixing improves tabular/MLP models; **maps to** `Linear(50→k)` on bearing/mask groups in `ml_modular_encoder` A1.
- **Jankovics et al. 2022** (arXiv:2206.02855), Intro + method — flattening entity features into one MLP is sample-inefficient; **maps to** avoiding `scalar_dim≈105` single MLP.
- **SRL survey 2025** (arXiv:2506.17518), §3 multimodal — modality-specific encoders then fusion; **maps to** CNN vision + compressed vectors + passthrough globals.
```

## Anti-patterns

- Starting a fork with only "we think X might help" and no citation or prior run JSON
- Re-opening a path marked `rejected` in DECISIONS without a new decision row
- Downloading papers without adding highlights (next agent cannot skim)
- Citing papers that address a **different plant** (e.g. rendezvous thrust MPC) without stating the mismatch
- Ignoring a relevant local lecture folder when the user is actively taking that course
- Committing LMS scrape helper scripts or browser cookie dumps into the repo (one-off automation is fine; do not leave credential plumbing)

## Additional resources

- Detailed per-paper sections: [reference.md](reference.md)
- Project experiment plans: `.cursor/plans/` and `backend/scripts/experiments/*/README.md`
