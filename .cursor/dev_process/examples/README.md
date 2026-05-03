# Dev Process Examples

This folder is a **walkthrough-ready** companion to [.cursor/dev_process/README.md](../README.md). Follow the numbered path when starting new work.

## Workflow (four steps applied in order)

| Step | What you do | Example file |
|---|---|---|
| 1 | Establish shared intent before code (questions, acceptance criteria, non-goals). | [grill-me-prompt-template.md](grill-me-prompt-template.md) |
| 2 | Anchor vocabulary so prompts/tests/code agree. | [ubiquitous-language-seed.md](ubiquitous-language-seed.md) |
| 3 | Ship one smallest verifiable slice with strict TDD. | [tdd-vertical-slice-template.md](tdd-vertical-slice-template.md) |
| 4 | Place the slice in clear module boundaries aligned with repo invariants. | [architecture-slice-pattern.md](architecture-slice-pattern.md) |

## Included Example Files

- `grill-me-prompt-template.md` — copy-paste prompts and follow-ups for clarification-first work.
- `ubiquitous-language-seed.md` — starter glossary aligned with charter and simulation/render boundaries.
- `tdd-vertical-slice-template.md` — blank checklist plus one **filled** illustrative slice for this repo.
- `architecture-slice-pattern.md` — how slices map onto `backend/simulation`, `backend/render`, `backend/autonomous_control`, etc.

## Related Project References

- [Project README](../../../README.md)
- [docs/user-manual.md](../../../docs/user-manual.md)
- [docs/project-charter.md](../../../docs/project-charter.md) (architecture invariants)
- [docs/render-api.md](../../../docs/render-api.md)
