# Task 39 Scope Reconciliation - Guard Auto-Fix Mode

## Current Taskmaster Scope
Task 39 asks for automatic correction capabilities in `scripts/codex-guard`: common fixable issues, `--auto-fix`, preview mode, post-application validation, fix history, configuration, and selective fixes.

## Current System Reality
The guard is now a broad workflow enforcement tool, not only an S:W:H:E regex checker. It validates session state, active work-tracking folders, Taskmaster activity evidence, plan/tracker sync, branch policy, runtime artifacts, timestamp discipline, template metadata, GAC guidance, continuation evidence, and drift.

That means an unrestricted auto-fix mode would be dangerous. Many guard failures are intentional blockers that require human/agent judgment, for example:

- missing or mismatched session/plan/work-tracking state
- branch/task mismatch
- missing Taskmaster evidence for task state changes
- protected runtime artifacts
- stale session edits
- emergency bypass policy gaps
- documentation guidance drift that needs semantic wording choices

## Decision
Implement a bounded, preview-first auto-fix framework inside `scripts/codex-guard validate`, with one proven safe initial fixer.

The initial fixer should target active work-tracking tracker metadata only:

- Fix kind: `tracker-last-updated`
- Target: `docs/ai/work-tracking/active/*-ACTIVE/TRACKER.md`
- Behavior: update or insert the `**Last Updated**: YYYY-MM-DD` line to match today's date
- Why this is safe: it is deterministic metadata inside the active task tracker, does not infer missing evidence, and does not rewrite user-authored progress content

## Non-Goals
- Do not auto-create sessions, plans, active folders, Taskmaster status, or work-tracking entries.
- Do not auto-rewrite S:W:H:E entries.
- Do not auto-edit templates, `CODEX.md`, `.codex/`, Taskmaster JSON, or generated task files.
- Do not make `--auto-fix` the default.
- Do not hide remaining guard failures after a fix is applied.

## CLI Shape
Add options to `python3 scripts/codex-guard validate`:

- `--fix-preview`: print available fixes without mutating files; exit remains nonzero while guard issues exist.
- `--auto-fix`: apply supported fixes, write fix history, then rerun validation.
- `--fix-kind <kind>`: allow selective fixes. Initial supported value: `tracker-last-updated`.
- `--fix-history <path>`: optional JSONL history path for applied fixes. Default: `reports/guard-fixes/history.jsonl`.

## Validation Contract
Preview mode must be read-only. Auto-fix mode must:

1. collect guard issues
2. collect supported fixes for changed files
3. apply only explicitly supported fixes
4. append a JSONL fix-history row for each applied fix
5. rerun validation after applying fixes
6. return success only when the post-fix validation passes

## Test Plan
Focused tests should cover:

- preview lists `tracker-last-updated` without changing the file
- auto-fix updates a stale tracker `Last Updated` line
- auto-fix can insert a missing `Last Updated` line near the tracker header
- selective fix filtering excludes unsupported requested kinds
- post-fix validation still reports non-fixable failures
- fix history receives a JSONL entry for applied fixes

## Open Follow-On Candidates
Future tasks can add more fixers after each is scoped separately:

- ordered changelog row sorting when rows are table-structured and lossless
- canonical newline normalization for guarded markdown files
- safe template metadata skeleton generation only when a template metadata policy provides exact defaults
- command guidance marker insertion only from a reviewed canonical snippet
