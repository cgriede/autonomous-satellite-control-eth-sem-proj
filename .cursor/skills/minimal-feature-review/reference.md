# Reference — Minimal Feature Review

Patterns and anti-patterns named in SKILL.md. Read on demand; do not preload.

## Working-tree hygiene in detail

A mixed working tree at review start is the single most expensive mistake in this loop. Concrete failure mode from the worked example:

1. Start review with `git status` showing 100+ unrelated paths (other agent's WIP, untracked notebooks, layout migration).
2. Do focused cleanup work on a different subset (5 files).
3. Commit only the focused 5 files. The 100+ are still hanging in the tree.
4. `git pull` brings in a remote refactor that moved modules.
5. The pull now has to reconcile remote changes against your 100+ untracked paths *and* your committed cleanup.
6. What should have been one merge conflict in `analysis_image_extractor.py` becomes six modify/delete conflicts on test files, plus content conflicts on the imports.

The Phase 0 commit costs ~30 seconds and prevents this entirely. Pattern:

```
git status
# if anything unrelated to the review is present:
git add <unrelated paths>
git commit -m "chore: <one-line description of pre-existing tree state>"
# then start Phase 1
```

If the user disputes the boundary between "related" and "unrelated", ask once and proceed. Do not include unrelated noise in the focused commit.

## Smell: dataclass-where-a-tuple-suffices

Signal:

- The dataclass is defined immediately above one function that returns it.
- It has no methods, no validation, no `@property` accessors.
- It is consumed in exactly one call site, which immediately destructures it.
- The fields are flat scalars (no nesting that benefits from named access).

Refactor: return a plain tuple. Annotate the tuple shape in the function signature. The call site reads `dt, raw, fallback_used, warning = parse(...)` either way.

Counter-signal (keep the dataclass): more than one call site, the type is exported, the fields are named in tests for readability, or there are >5 fields where positional access becomes opaque.

## Smell: hardcoded-data-that-should-be-a-fixture-file

Signal:

- A Python file declares `FIXTURES = [...]` or `CASES = {...}` with dozens of fields per entry.
- The data describes inputs and expected outputs for a parametrized test.
- Edits to the data require a Python edit (touching the test module on every regime addition).
- Sister test fixtures already live in a `fixtures/` directory as `.json`, `.yaml`, or `.csv`.

Refactor: extract each entry to a fixture file under `fixtures/<group>/<name>.json`. Replace the hardcoded list with a glob loader:

```python
def _load_fixture(meta_path: Path) -> dict:
    return json.loads(meta_path.read_text(encoding="utf-8"))

FIXTURES = [_load_fixture(p) for p in sorted(FIXTURE_DIR.glob("*.json"))]
```

The test stays parametrized; new regimes are added by dropping a JSON file.

## Datetime parsing review checklist

External datetime strings (OCR, scraped text, third-party APIs) need explicit thought. Check each item:

- **Is the offset format ISO or named?** `+02:00` and `+0200` parse correctly with `dateutil.parser.isoparse`. `UTC+2` does not — `dateutil` interprets it with POSIX semantics (east is negative), so `12:00 UTC+2` becomes `12:00-02:00 = 14:00 UTC` instead of the intended `10:00 UTC`. Normalise named offsets to ISO before parsing.
- **Is naive-vs-aware handled?** Decide which one the API returns. Convert at the boundary to one shape (typically aware UTC) and keep it that way.
- **Is the fallback explicit?** If the parse fails, does the caller know? Silent fallback to "now" or "epoch" is almost always wrong. Either raise, or return a flag the caller must read.
- **Is there a fuzzy-parse layer?** `dateutil.parser.parse(text, fuzzy=True)` accepts almost anything. Use only as a last resort, log when it triggers.

## Stale-Jupyter-kernel false positive

Symptom: you edit a function, save, run a notebook cell that imports it, the cell raises `TypeError` or `AttributeError` that contradicts the file on disk.

Confirmation procedure (do this before suspecting your code):

1. `git diff HEAD <path>` — does the diff actually show your change?
2. `git show HEAD:<path>` for committed changes — does the committed file have the right signature?
3. If both show the correct code, the kernel is the problem. Restart it: in the notebook UI, Kernel -> Restart. Re-run cells from top.

Reason: `importlib.reload(mod)` only reloads `mod` itself, not transitively. A second module that imported `mod.OldClass` at its own load time still holds the old reference. Kernel restart is the cleanest reset.

Do not paper over this with `importlib.invalidate_caches()` or `del sys.modules[...]` chains — they hide real import bugs and produce confusing intermittent state.

## Anti-patterns specific to review work

- **Removing tests during cleanup.** A test you do not understand is not noise. Read it, identify what it covers, decide. If it duplicates another test, delete with a one-line commit note. Otherwise keep.
- **Widening assertions to make the new shape pass.** If the refactor changed semantics enough to break an assertion, the refactor is no longer "minimal"; surface the semantic change to the user.
- **Refactoring code the user did not name.** The review scope is the named commits or branch. Drive-by reformatting of adjacent files inflates the diff and obscures the cleanup. Resist.
- **Inventing new tests during the cleanup commit.** Add tests only for failures the review surfaced (e.g. the `UTC+2` bug). Coverage gaps unrelated to the cleanup are a separate ticket.
- **Skipping Phase 0 because "the tree is mostly clean".** If `git status --short` has any line that is not part of the focused review, run Phase 0.

## Net-line-count discipline

The user asked twice during the worked example: "how many lines did we add vs remove?". Track this. A "cleanup" that adds 36 lines is suspicious; check what is actually being simplified.

Heuristic: if a refactor is net-positive on line count, one of these must be true to justify it:

1. The new code removes a class of bugs the old code shipped (tests prove it).
2. The new shape eliminates duplication that was about to be copied a third time.
3. A type was made explicit at an external boundary where runtime data must be validated.

Otherwise stop and reconsider.
