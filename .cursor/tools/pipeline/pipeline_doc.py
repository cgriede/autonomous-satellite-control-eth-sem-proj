"""Pipeline experiment doc bin sync — move docs to match current_phase.

Canonical: .cursor/tools/pipeline/ — see .cursor/skills/build-tool/SKILL.md
Used by /close-experiment-step and experiment-knowledge-pipeline.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_PIPELINE_ROOT = _REPO_ROOT / "docs" / "experiments" / "pipeline"
_README = _PIPELINE_ROOT / "README.md"

PHASE_TO_BIN: dict[int, str] = {
    0: "0-initialized",
    1: "1-built",
    2: "2-run",
    3: "3-evaluation",
    4: "4-documentation",
}

_BIN_TO_PHASE: dict[str, int] = {v: k for k, v in PHASE_TO_BIN.items()}

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_PHASE_HEADING_RE = re.compile(r"^## Phase (\d+) —", re.MULTILINE)
_SLUG_RE = re.compile(r"^slug:\s*(\S+)\s*$", re.MULTILINE)
_CURRENT_PHASE_RE = re.compile(r"^current_phase:\s*(\d+)\s*$", re.MULTILINE)
_EXPERIMENT_ID_RE = re.compile(r"^experiment_id:\s*(\d+)\s*$", re.MULTILINE)


@dataclass
class PipelineDoc:
    path: Path
    slug: str
    experiment_id: int
    current_phase: int
    body: str
    frontmatter: str

    @property
    def filename(self) -> str:
        return self.path.name

    @property
    def expected_bin(self) -> str:
        return PHASE_TO_BIN[self.current_phase]

    @property
    def expected_dir(self) -> Path:
        return _PIPELINE_ROOT / self.expected_bin

    def expected_path(self) -> Path:
        return self.expected_dir / self.filename


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _parse_doc(path: Path) -> PipelineDoc:
    text = _read_text(path)
    m = _FRONTMATTER_RE.match(text)
    if not m:
        raise ValueError(f"No YAML frontmatter: {path}")
    fm = m.group(1)
    body = text[m.end() :]
    slug_m = _SLUG_RE.search(fm)
    phase_m = _CURRENT_PHASE_RE.search(fm)
    id_m = _EXPERIMENT_ID_RE.search(fm)
    if not slug_m or not phase_m or not id_m:
        raise ValueError(f"frontmatter missing slug/current_phase/experiment_id: {path}")
    return PipelineDoc(
        path=path,
        slug=slug_m.group(1),
        experiment_id=int(id_m.group(1)),
        current_phase=int(phase_m.group(1)),
        body=body,
        frontmatter=fm,
    )


def _write_doc(doc: PipelineDoc, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{doc.frontmatter}---\n{doc.body}", encoding="utf-8")


def find_docs(*, slug: str | None = None) -> list[PipelineDoc]:
    docs: list[PipelineDoc] = []
    for path in sorted(_PIPELINE_ROOT.rglob("*.md")):
        if path.name == "README.md":
            continue
        if path.parent.name == "99-archive":
            continue
        try:
            doc = _parse_doc(path)
        except ValueError:
            continue
        if slug is not None and doc.slug != slug:
            continue
        docs.append(doc)
    return docs


def bin_for_path(path: Path) -> str | None:
    parent = path.parent.name
    return parent if parent in _BIN_TO_PHASE else None


def check_docs(*, slug: str | None = None) -> list[str]:
    issues: list[str] = []
    by_slug: dict[str, list[PipelineDoc]] = {}
    for doc in find_docs(slug=slug):
        by_slug.setdefault(doc.slug, []).append(doc)

    for s, group in sorted(by_slug.items()):
        if len(group) > 1:
            paths = ", ".join(str(d.path.relative_to(_REPO_ROOT)) for d in group)
            issues.append(f"duplicate slug {s!r}: {paths}")
        for doc in group:
            actual = bin_for_path(doc.path)
            if actual is None:
                issues.append(f"{doc.path}: not under a phase bin")
                continue
            if actual != doc.expected_bin:
                issues.append(
                    f"{doc.path.relative_to(_REPO_ROOT)}: "
                    f"current_phase={doc.current_phase} expects {doc.expected_bin}/ "
                    f"but file is in {actual}/"
                )
    return issues


def _update_readme_doc_link(doc: PipelineDoc) -> bool:
    if not _README.exists():
        return False
    text = _read_text(_README)
    rel = doc.expected_path().relative_to(_PIPELINE_ROOT).as_posix()
    link_target = f"]({rel})"
    # Row contains slug in backticks — update Doc column link for that row.
    pattern = re.compile(
        rf"(\|\s*{doc.experiment_id}\s*\|\s*`{re.escape(doc.slug)}`\s*\|\s*)\[[^\]]+\]\([^)]+\)",
    )
    new_text, n = pattern.subn(rf"\1[{doc.filename}]({rel})", text, count=1)
    if n:
        _README.write_text(new_text, encoding="utf-8")
        return True
    return False


def _fix_repo_links(old_rel: str, new_rel: str) -> list[Path]:
    """Replace stale pipeline doc paths under backend/scripts/experiments."""
    old_posix = old_rel.replace("\\", "/")
    new_posix = new_rel.replace("\\", "/")
    touched: list[Path] = []
    search_roots = [
        _REPO_ROOT / "backend" / "scripts" / "experiments",
        _REPO_ROOT / "docs",
    ]
    for root in search_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix not in {".md", ".py", ".json"}:
                continue
            if "pipeline_doc.py" in path.name:
                continue
            try:
                text = _read_text(path)
            except (OSError, UnicodeDecodeError):
                continue
            if old_posix not in text:
                continue
            path.write_text(text.replace(old_posix, new_posix), encoding="utf-8")
            touched.append(path)
    return touched


def sync_bin(*, slug: str | None = None, dry_run: bool = False) -> list[str]:
    actions: list[str] = []
    for doc in find_docs(slug=slug):
        if bin_for_path(doc.path) == doc.expected_bin:
            continue
        old_rel = doc.path.relative_to(_REPO_ROOT).as_posix()
        dest = doc.expected_path()
        actions.append(f"move {old_rel} -> {dest.relative_to(_REPO_ROOT).as_posix()}")
        if dry_run:
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists() and dest.resolve() != doc.path.resolve():
            raise FileExistsError(f"destination exists: {dest}")
        doc.path.rename(dest)
        doc.path = dest
        new_rel = dest.relative_to(_REPO_ROOT).as_posix()
        if _update_readme_doc_link(doc):
            actions.append(f"updated README Doc link for {doc.slug}")
        fixed = _fix_repo_links(old_rel, new_rel)
        for p in fixed:
            actions.append(f"fixed link in {p.relative_to(_REPO_ROOT).as_posix()}")
    return actions


def _set_frontmatter_field(fm: str, key: str, value: str) -> str:
    pat = re.compile(rf"^{re.escape(key)}:.*$", re.MULTILINE)
    line = f"{key}: {value}"
    if pat.search(fm):
        return pat.sub(line, fm, count=1)
    return fm.rstrip() + "\n" + line + "\n"


def _phase_block_exists(body: str, phase: int) -> bool:
    return bool(_PHASE_HEADING_RE.search(body) and f"## Phase {phase} —" in body)


def close_phase(
    *,
    slug: str,
    dry_run: bool = False,
    skip_phase_check: bool = False,
) -> list[str]:
    """Advance current_phase after phase N documented; move bin + update README."""
    docs = find_docs(slug=slug)
    if not docs:
        raise SystemExit(f"No pipeline doc for slug {slug!r}")
    if len(docs) > 1:
        raise SystemExit(f"Duplicate docs for slug {slug!r} — run check first")
    doc = docs[0]
    n = doc.current_phase
    if n >= 4:
        raise SystemExit(f"{doc.slug} already at phase 4")

    actions: list[str] = []
    if not skip_phase_check and not _phase_block_exists(doc.body, n):
        raise SystemExit(
            f"## Phase {n} block missing in {doc.path} — run /document-experiment-step first"
        )

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    fm = doc.frontmatter
    fm = re.sub(
        rf'^(\s*"{n}":\s*\{{[^}}]*status:\s*)(\w+)',
        rf'\1done',
        fm,
        count=1,
        flags=re.MULTILINE,
    )
    fm = re.sub(
        rf'(\s*"{n}":\s*\{{[^}}]*completed_utc:\s*)([^\n]+)',
        rf'\1"{now}"',
        fm,
        count=1,
        flags=re.MULTILINE,
    )
    new_phase = n + 1
    fm = _set_frontmatter_field(fm, "current_phase", str(new_phase))
    if n == 2:
        fm = _set_frontmatter_field(fm, "run_lock_holder", "null")
    doc.frontmatter = fm
    doc.current_phase = new_phase

    actions.append(f"advance {doc.slug} current_phase {n} -> {new_phase}")
    if dry_run:
        actions.append(f"would move to {doc.expected_bin}/")
        return actions

    _write_doc(doc, doc.path)
    actions.extend(sync_bin(slug=slug))
    return actions


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Pipeline experiment doc bin sync")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_check = sub.add_parser("check", help="List bin vs current_phase mismatches")
    p_check.add_argument("--slug", default=None)

    p_sync = sub.add_parser("sync-bin", help="Move doc(s) to bin matching current_phase")
    p_sync.add_argument("--slug", default=None)
    p_sync.add_argument("--dry-run", action="store_true")

    p_close = sub.add_parser(
        "close-phase",
        help="Mark phase done, advance current_phase, sync-bin (for /close-experiment-step)",
    )
    p_close.add_argument("--slug", required=True)
    p_close.add_argument("--dry-run", action="store_true")
    p_close.add_argument(
        "--skip-phase-check",
        action="store_true",
        help="Advance without ## Phase N block (escape hatch)",
    )

    args = parser.parse_args(argv)

    if args.cmd == "check":
        issues = check_docs(slug=args.slug)
        if issues:
            print("Pipeline doc issues:")
            for line in issues:
                print(f"  - {line}")
            return 1
        print("OK — all pipeline docs in correct bins")
        return 0

    if args.cmd == "sync-bin":
        actions = sync_bin(slug=args.slug, dry_run=args.dry_run)
        if not actions:
            print("Nothing to sync")
            return 0
        for line in actions:
            print(line)
        return 0

    if args.cmd == "close-phase":
        actions = close_phase(
            slug=args.slug,
            dry_run=args.dry_run,
            skip_phase_check=args.skip_phase_check,
        )
        for line in actions:
            print(line)
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
