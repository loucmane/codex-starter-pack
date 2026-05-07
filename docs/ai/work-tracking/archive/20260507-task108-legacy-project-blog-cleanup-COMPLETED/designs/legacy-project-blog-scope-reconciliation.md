# Task 108 Legacy PROJECT-BLOG Scope Reconciliation

## Trigger
Task 18 added `security_validator.py` and produced a baseline report with one remaining path traversal finding:

- `templates/PROJECT-BLOG.md`, line 236: `../../../packages/backend`

The user confirmed this file likely comes from an old blog-project iteration.

## Evidence Reviewed
- `templates/PROJECT-BLOG.md` is titled "Animal Protection Foundation Blog - Project Configuration" and contains project-specific Next.js, Tailwind, donation, CMS, and animal-welfare content rules.
- `templates/PROJECT-BLOG.md` is not portable foundation guidance. It belongs to an old product/project context.
- `docs/ai/work-tracking/archive/20260425-task1-codebase-structure-analysis-COMPLETED/reports/codebase-analysis/migration-readiness-scores.md` already called out `templates/PROJECT-BLOG.md` as a remaining not-migrated legacy root.
- `docs/ai/work-tracking/archive/20251004-task87-replace-monolith-COMPLETED/designs/legacy-inventory.md` listed `templates/PROJECT-BLOG.md` as legacy inventory whose links were partially updated, not as newly validated portable foundation material.
- Live current references are limited to:
  - `templates/shared/tools/tool-selection-matrix.md`
  - `templates/tools/index.md`
  - `templates/metadata/template-overview.md`
  - `templates/metadata/template-summary.csv`
  - `templates/metadata/template-inventory.txt`
  - `scripts/template-ssot-scanner/migration_detector.py`
  - `scripts/template-ssot-scanner/safe_reorganize.py`

## Options

| Option | Pros | Cons | Decision |
| --- | --- | --- | --- |
| Allowlist the finding | Fastest; no content changes | Teaches the system to accept stale project-specific content; weakens the meaning of a clean baseline | Rejected |
| Rewrite only the flagged import line | Keeps diff tiny and clears the security report | Leaves a project-specific blog template in the portable foundation | Rejected |
| Remove the legacy file and update its small reference surface | Aligns portable foundation with current scope; clears the security report without weakening rules | Slightly broader than a one-line edit because metadata/navigation/helper lists must be updated | Selected |

## Selected Scope
Remove `templates/PROJECT-BLOG.md` from the portable template set and update the small live reference surface:

- Delete `templates/PROJECT-BLOG.md`.
- Remove PROJECT-BLOG navigation references from `templates/shared/tools/tool-selection-matrix.md` and `templates/tools/index.md`.
- Remove PROJECT-BLOG metadata rows from `templates/metadata/template-overview.md`, `template-summary.csv`, and `template-inventory.txt`.
- Remove `templates/PROJECT-BLOG.md` from scanner helper monolith/denylist fixtures in `migration_detector.py` and `safe_reorganize.py`.
- Update scanner tests only if expectations directly depend on the old project-specific root being canonical.

## Non-Goals
- No broad template reorganization.
- No scanner rule weakening.
- No security-validator allowlist entry.
- No cleanup of generated ignored `scripts/template-ssot-scanner/output/**` artifacts.
- No unrelated removal of other legacy monolith roots.

## Verification Plan
- `python3 scripts/template-ssot-scanner/security_validator.py --base . --output docs/ai/work-tracking/active/20260507-task108-legacy-project-blog-cleanup-ACTIVE/reports/legacy-project-blog-cleanup/security-validation-2026-05-07.json`
- `python3 -m pytest scripts/template-ssot-scanner`
- `python3 scripts/codex-task plan sync`
- `python3 scripts/codex-task work-tracking audit`
- `python3 scripts/codex-guard validate --include-untracked`
- `python3 scripts/codex-task taskmaster health`
- `git diff --check`
