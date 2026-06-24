---
name: read-handwritten-notes
description: >-
  Transcribes handwritten or annotated notes from PDFs (lab notebooks, bug
  reports, sketches) into JSON and optional markdown. Renders pages with global
  scripts, reads handwriting with vision. Use when the user asks to read notes,
  transcribe a PDF with handwriting, extract annotations from docs/notes, or
  OCR handwritten project notes (not exam answer sheets).
---

# Read Handwritten Notes

For **exam answer sheets**, use global [`extract-handwritten-exam-notes`](file:///C:/Users/cedri/.cursor/skills/extract-handwritten-exam-notes/SKILL.md) or exam-review-buddy instead.

## Runtime

```powershell
conda activate mini-proj
```

Scripts: `~/.cursor/skills/extract-handwritten-exam-notes/scripts/` (shared render/crop tooling).

```powershell
pip install pymupdf pillow
```

## Workflow

### 1. Render pages (default: full page, no exam crops)

```powershell
conda activate mini-proj
python ~/.cursor/skills/extract-handwritten-exam-notes/scripts/render_pages.py "docs/notes/your-notes.pdf" --zoom 3.0
```

Output: `{pdf_parent}/_tmp_pages/{pdf_stem}/page_XX.png`

Use `prepare_for_transcription.py` only when the layout matches exam sheets (right-half answer columns). For bug reports and annotated screenshots, **prefer full pages**.

Optional region crops:

```powershell
python ~/.cursor/skills/extract-handwritten-exam-notes/scripts/crop_regions.py docs/notes/_tmp_pages/<stem>/page_01.png --split-pages
```

### 2. Vision transcription

1. Read each `page_XX.png` with the Read tool.
2. Separate **typed/printed text**, **handwritten ink**, and **figure descriptions** (arrows, circles, UI labels).
3. Note ambiguity or illegible spans explicitly.

### 3. Write output

**JSON** (source of truth) under `docs/notes/hand_transcriptions/`:

`{run:02d}__{pdf_stem}.json`

```json
{
  "source_pdf": "Target Pointing Baseline model, bugs.pdf",
  "title": "Target Pointing: Baseline model, bugs",
  "transcribed_at": "2026-06-24",
  "pages": [
    {
      "page": 1,
      "typed_captions": ["..."],
      "handwriting": ["..."],
      "figure_annotations": ["..."]
    }
  ],
  "summary": "One-paragraph synthesis for agents."
}
```

**Markdown** (optional, human-readable) alongside the PDF:

`{pdf_stem}.transcription.md`

## Checklist

```
- [ ] render_pages.py (full pages unless exam layout)
- [ ] Read PNGs with vision
- [ ] Split typed vs handwritten vs figure markup
- [ ] Write hand_transcriptions JSON
- [ ] Optional: write .transcription.md
```

## Paths (this repo)

| Artifact | Location |
|----------|----------|
| Source PDFs | `docs/notes/*.pdf` |
| Rendered pages | `docs/notes/_tmp_pages/{stem}/` |
| Transcriptions | `docs/notes/hand_transcriptions/` |
| Markdown export | `docs/notes/{stem}.transcription.md` |
