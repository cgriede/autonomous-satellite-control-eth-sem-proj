# Semester project report (LaTeX)

Final written report for the ETH MSc Mechanical Engineering semester project.
Companion slides live in `docs/presentation/`.

## Build (Windows / MiKTeX)

From this directory:

```powershell
.\compile_win.ps1
```

Output: `main.pdf`

Manual sequence:

```powershell
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

## Layout

| File | Role |
|------|------|
| `main.tex` | Metadata, document structure |
| `eth-semester-report.cls` | ETH-style title page, packages |
| `sections/*.tex` | One file per major section |
| `references.bib` | Bibliography |
| `report-direction-log.md` | Scoping Q&A and narrative decisions (update after report discussions) |
| `figures/` | Add exported plots/frames here |
| `graphics/eth_logo.pdf` | ETH logo for title page |

## Writing notes

- Keep the abstract to one page; main body target is **shorter than the bachelor thesis** reference under `docs/report/bachelor-thesis-reference/`.
- Numeric values must match code; use `docs/presentation/` as the parameter record and cite repository paths.
- Replace `\reportSupervisor` and `\reportInstitute` in `main.tex` before submission.
