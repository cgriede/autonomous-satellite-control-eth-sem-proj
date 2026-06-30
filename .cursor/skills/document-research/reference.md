# Document research — reference

## Investigation note template

Required thought-process sections in **bold**. Remove optional blocks if N/A; never omit **Decisions** or **Experiments already conducted** when any experiment or scope discussion occurred.

```markdown
# {Title} — {short subtitle}

Purpose, audience, related experiments. Link [PROJECT_KNOWLEDGE.md](PROJECT_KNOWLEDGE.md).

**Related code:** `…`
**Decision IDs:** D-00x, … (from [DECISIONS.md](DECISIONS.md))

---

## Reasoning chain

1. **Question** — …
2. **Literature / prior art** — …
3. **Hypothesis** — …
4. **Evidence** — our runs vs papers
5. **Conclusion** — …

---

## 1. {External / literature baseline}

{Tables, local PDF links, external arXiv.}

---

## 2. {Project-specific analysis}

{Code stack, observation layout, config.}

---

## 3. {Diagnostics / methodology}

{How to interpret metrics; decision flow.}

---

## Decisions taken

| ID | Status | Decision | Link |
|----|--------|----------|------|
| D-00x | accepted/rejected/deferred | … | [DECISIONS.md](DECISIONS.md) |

---

## Rejected or deferred (do not re-run without user reversal)

| Path | Status | Why | Revisit when |
|------|--------|-----|--------------|
| … | rejected/deferred | … | … |

---

## Experiments already conducted

| Slug | Arm | Verdict | JSON / analysis | Notes |
|------|-----|---------|-----------------|-------|
| `ml_algo_overnight` | H1a mpo_sparse | inconclusive | `results/h1a_mpo_sparse.json` | … |

Do not re-propose identical frozen inputs.

---

## Open questions

- …

---

## Gaps in local library

| Topic | Status | Action |
|-------|--------|--------|

---

## References

### Local · External · Project code & runs
```

## DECISIONS.md row template

```markdown
| D-00N | YYYY-MM-DD | rejected | Topic | One-line decision | Rationale | link to investigation, JSON, plan |
```

Statuses: `accepted` | `rejected` | `deferred` | `superseded`

## README / PROJECT_KNOWLEDGE index rows

**README.md** (Investigation notes):

```markdown
| [topic-slug.md](topic-slug.md) | One-line description |
```

**PROJECT_KNOWLEDGE.md** (Investigation notes table): same row.

## LITERATURE_HIGHLIGHTS cheat-sheet row

```markdown
| question or experiment | [topic-slug.md](topic-slug.md); PDF slugs | one-line justification |
```

## STATUS closeout line

Append to `docs/ml/experiments/STATUS_*.md` § Closeout log:

```markdown
| UTC | Exp | Arm | Verdict | Notes |
| 2026-06-29T… | 1 | mpo_t05 | inconclusive | links to JSON |
```

## Slash command reply template

```markdown
## Document research complete

- **Note:** docs/research/{slug}.md
- **Decisions:** D-00x, … appended to DECISIONS.md
- **Indexed:** README, PROJECT_KNOWLEDGE, LITERATURE_HIGHLIGHTS (as applicable)
- **Experiments referenced:** {list — avoids duplicate re-run}
- **Rejected/deferred:** {one line}
- **Gaps:** {missing PDFs or unwritten layers}
- **Deliverable readiness:** {which layers still empty for generate-* skills}
```

## Quality bar

Good documentation enables another agent to:

1. Explain **why** we did not pursue path X (DECISIONS + investigation)
2. List **exactly** which arms ran and verdicts (table + JSON paths)
3. Propose **only new** work not blocked by rejected/deferred rows
4. Run `/generate-research-report` without inventing narrative

Weak: paper summaries, no DECISIONS rows, no experiment table, chat-only reasoning.
