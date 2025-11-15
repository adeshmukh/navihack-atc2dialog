# Review Branch Against Main

You are a coding agent tasked with reviewing the current branch's changes relative to `main`. Focus **only** on the diff; do not critique untouched code.

## Pre-flight

1. **Verify repository state**
   - Run `git status --short` and stop if there are uncommitted changes. Inform the user before proceeding.
2. **Identify branches**
   - Capture the current branch via `git branch --show-current`.
   - Ensure `main` is up to date: `git fetch origin main:main` (or confirm with the user if fetch is undesirable).

## Generate Diff

- Use `git diff main...<current-branch>` to collect only the commits unique to the branch.
- Limit inspection to files present in this diff.

## Review Focus Areas

For every hunk in the diff:

1. **Idiomatic Python 3.10+**
   - Prefer `list`, `dict`, `tuple`, and built-in collection annotations over `typing.List`, etc.
   - Use `| None` instead of `Optional[...]` unless interop dictates otherwise.
   - Watch for outdated typing or pattern-matching antipatterns.
2. **Logic & Initialization**
   - Spot uninitialized or conditionally skipped variables/fields.
   - Flag stale references, dead code, or incorrect branching.
3. **Comment Quality**
   - Identify superfluous comments that merely restate the code.
   - Preserve or request explanatory comments only when they add context or rationale.
4. **Docstring Accuracy**
   - Ensure docstrings match function/class signatures, parameter names, return types, and side effects.
   - Flag mismatches or missing docstrings when behavior is non-obvious.

## Reporting

- Organize findings by severity (High, Medium, Low) with `file:path` references and brief reasoning.
- If no issues are found, explicitly state that the diff looks good and mention any residual risks or testing gaps.
- Keep summaries concise; emphasize actionable feedback tied to the diff.
