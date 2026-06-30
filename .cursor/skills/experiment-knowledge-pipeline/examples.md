# Example — Exp 1 shutter threshold (legacy layout)

Canonical closed record: [`4-documentation/01-shutter-threshold.md`](../../../docs/experiments/pipeline/4-documentation/01-shutter-threshold.md)

> **Note:** Exp 1 was documented before the Phase 0–4 append model. New experiments follow [`reference.md`](reference.md) — one `## Phase N` block per `/document-experiment-step`.

## Phase mapping (if migrating Exp 1)

| Phase | Would contain |
|-------|----------------|
| 0 | H1 charter, D-009 context, literature / shoulders of giants |
| 1 | `ml_shutter_threshold/` fork, smoke, run command |
| 2 | t05/t09 run dirs, KPI JSON |
| 3 | Verdict table (H1a–H1d) |
| 4 | D-009–D-011, investigation note, no promotion |

## Append workflow (new experiments)

```text
/init-experiment          → title + frontmatter only in 0-initialized/
/start-experiment-step    → work Phase 0
/document-experiment-step → append ## Phase 0 — Initialized (0.1–0.3)
/close-experiment-step    → current_phase: 1, stay in or move to 1-built/
… repeat for Phases 1–4 …
```
