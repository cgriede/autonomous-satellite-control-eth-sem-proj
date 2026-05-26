---
name: targeted-cleanup-pass
description: Execute a scoped codebase cleanup: package regroups, renames, module splits, dead-code removal, import sweeps, and deliberation/test hygiene. Runs an upfront scoping round before touching anything, then works in phases with explicit verification gates. Use when the user says "cleanup pass", "let's clean this up", "regroup the package", "rename this module", or asks to remove legacy/dead code from a defined area.
---

# Targeted Cleanup Pass

Five phases. Phase 0 is the gate that makes the rest go smoothly; skip it and you will need mid-flight corrections.

## Phase 0 — Intake (ask before touching anything)

Run `git status --short` and read the working-tree state. Then ask one batched AskQuestion round covering:

**Scope questions (required):**
- What is **in scope** for this pass? (package, dir, files, specific operations like "only renames" or "also split modules")
- What is **explicitly out of scope**? List candidates the user might expect to clarify (e.g. "bulk data migration", "promote helpers to production modules", "fib helpers promotion").
- Where does this code **live** — is there a dedicated workspace/notebook dir that must stay in place and not be moved elsewhere?

**Done criteria (required — state as observable checks):**
- `grep <old_name> backend/` → 0 hits?
- Specific test suite passes, and which subset proves real behavior (fixture-level, not just mocked unit count)?
- Notebook first cell runs?
- Docs/plans updated?
- Commit at end of this session?

**Cleanup type questions (pick what applies):**
- Are there deliberation `.md` files? Rule: delete stale boilerplate (empty intent, no matching test behavior). Keep only files that encode a non-obvious scope decision.
- Are there test files for deleted modules? Delete test + deliberation together.
- Is there a module split involved? Identify the circular-import risk upfront (e.g. if a helper calls back into the class being split out, where does the shared util land?).

Do not write a single file until the user confirms scope and done criteria. If the user already answered some of these in their request, skip those questions — do not re-ask.

## Phase 1 — Structural work

Execute in this order to minimize broken-import windows:

1. **New files / directories first** (create target locations before moving anything).
2. **Moves and renames** (git mv where possible so history tracks).
3. **Deletes** (confirmed dead modules, legacy stubs, stale artifacts).
4. **Content edits** (API renames, envelope rewrites, `__init__.py` updates).
5. **Module splits last** — splitting a large file is the highest-risk operation; do it after the rest of the tree is stable.

For a module split:
- Extract the private helpers and data classes into the new submodule.
- Keep any shared utility (e.g. `configure_tesseract_cmd`) in the existing shared utils file, not the new submodule, to avoid circular imports.
- Re-export from the old module's `__init__.py` so existing importers see no change until you explicitly update them.

## Phase 2 — Import sweep

After structural work, run a grep sweep before touching tests:

```powershell
# Example: check for stale old module name
rg "old_module_name" backend/ --glob "*.py" --glob "*.ipynb" --glob "*.mdc"
```

Fix every hit. **Include:** scripts, tests, notebooks (cell source), cursor rules (globs in `.mdc` files), session/benchmark files. Do not leave `# noqa` as a fix for a stale import.

When the grep returns zero hits in `backend/`, note it explicitly. That is one of the observable done criteria.

## Phase 3 — Test gate

Run the targeted test suite. Report results in this format — do not collapse everything into a single pass count:

```
Fixture tests (real images/data, Tesseract live):
  test_axis_calibration_fixtures[avalanche_15m]  PASSED
  test_axis_calibration_fixtures[chainlink_2d]   PASSED
  ... (N fixtures)

Unit/mocked tests: 55 passed

Total: 60 passed
```

Fixture tests are the meaningful signal after a module split or rename; mocked unit tests only confirm wiring. If the user cares about a specific real-data proof, name it explicitly in the report.

If any fixture test fails, treat it as a blocker. Debug with runtime evidence per `.cursor/skills/debug-workflow/SKILL.md` before declaring done.

## Phase 4 — Git hygiene commit

```powershell
# Verify working tree — identify what is ours vs pre-existing noise
git status --short
git diff --stat   # for each suspicious file: is this part of the cleanup?
```

Stage only files the cleanup pass actually touched. Leave unrelated pre-existing changes unstaged (scraper runtime data, ops status JSONs, unrelated import fixes, editor config). Call out each excluded file and why.

Commit message shape:

```
<type>: <one-line summary of the cleanup scope>

<optional 2-3 bullet body if the scope is complex>
```

PowerShell heredoc (not bash):
```powershell
$msg = @"
refactor: <summary>

- bullet 1
- bullet 2
"@
git add <explicit paths> ; git commit -m $msg
```

Verify with `git show HEAD --stat` that only the intended files are in the commit.

## Recurring corrections to avoid

These are the mid-flight corrections that happened in the reference session — the Phase 0 intake is designed to prevent them:

| What went wrong | Phase 0 question that prevents it |
|---|---|
| Agent moved notebooks to wrong parent dir | "Where does this workspace live and must it stay there?" |
| Pass count reported without isolating fixture tests | Ask: "What proof do you want in the test report?" |
| Import sweep missed notebook cells and `.mdc` globs | Scope the grep to `*.py`, `*.ipynb`, `*.mdc` explicitly |
| Unrelated files crept into the commit | Phase 4 diff review before staging |
| Doc/plan sync left to the user | "Are docs and active plans in scope for this pass?" |

## Pointers

- Deliberation files rule: delete when intent section is empty and no test behavior would be lost. Keep when the file encodes a non-obvious decision about test scope or policy.
- Backward compatibility default for cleanup passes: **none** — renames and moves are breaking by design; callers are updated in the same commit.
- Related skills: [minimal-feature-review](../minimal-feature-review/SKILL.md) (for reviewing what another agent produced), [debug-workflow](../debug-workflow/SKILL.md) (for fixture test failures).
