# Review research report

Read and follow **`~/.cursor/skills/dev-skills/review-research-report/SKILL.md`** end to end.

Check `docs/report/semester-project/` (PDF + LaTeX) against the writing guidelines and anti-patterns from generate/update research-report skills, **and** PDF layout (render pages → vision; checklist **I** / `report-layout-visual-pdf-review`). Prefer `docs/report/compile_report.ps1` — it recompiles and **fails** if any `Overfull \hbox` is ≥ 20 pt (LaTeX already logs these; the script surfaces them). Layout-only reviews still require visual PDF inspection, not LaTeX alone. Report findings; do not edit unless asked. Do not commit unless asked.

If Critical / Should-fix / Nits remain, **suggest** a sequential `update-research-report` Task-subagent queue (one item per agent; parent verifies `compile_report.ps1` + acceptance criteria before the next). Do not start that queue until the user asks.
