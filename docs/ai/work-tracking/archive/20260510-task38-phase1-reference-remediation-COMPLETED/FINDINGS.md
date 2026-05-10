# Findings

- 2026-05-10 — Task 38 findings recorded for scanner dry-run, Markdown link locality, and remaining manual-review reference scope.

## 2026-05-10 — Fresh scanner output has 141 automatic reference updates

Regenerating the scanner suite on 2026-05-10 produced current fix recommendations with 186 broken references and 188 total fixes. The safe runner dry-run reports 141 automatic `would-change` reference updates across template index, pattern, integration, registry, guide, matrix, and behavior files.

This is actionable for Task 38 only through the safe runner and only after rollback checkpoint evidence is captured. The remaining manual-review references, circular dependencies, orphaned files, and monolith-completion items require separate scope decisions.

## 2026-05-10 — Markdown link locality was a real post-apply regression

The initial automatic apply reduced scanner findings but caused `tests/meta_workflow_guard/test_training_materials.py::test_guide_index_links_resolve_to_existing_files` to fail. The generated root-style target `templates/guides/training/foundation-onboarding.md` is valid as a scanner repo path but invalid as a Markdown link from `templates/guides/index.md`, where it resolves to `templates/guides/templates/guides/...`.

Resolution:
- Updated `apply_reference_fixes.py` to write Markdown link targets relative to each source file.
- Updated `analyze_references.py` to resolve nested bare links relative to source files before legacy template-root fallback.
- Added regression tests instead of weakening the failing test.
- Normalized already-applied Markdown links and reran scanner/tests.

## 2026-05-10 — Remaining scanner findings are not automatic safe-runner fixes

Final scanner output after runner/scanner fixes reports 41 broken references and 43 total fixes. The safe runner dry-run reports `Summary: no fixes`, which means the remaining findings require manual review, broader migration, circular-dependency decisions, or orphan cleanup rather than another automatic apply.
