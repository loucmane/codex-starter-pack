# Task 126 Acceptance Fixture Hardening

- Branch: `feat/task-126-harden-aegis-acceptance-fixtures`.
- Added semantic helper module `tests/meta_workflow_guard/aegis_acceptance_assertions.py` for structured S:W:H:E parsing, plan table parsing, workflow evidence assertions, web cart-button semantic checks, and BrandMark accessibility semantic checks.
- Added `tests/meta_workflow_guard/test_aegis_acceptance_assertions.py` with positive variants and negative regressions for comments, dead strings, and unattached buttons.
- Refactored `test_installed_web_target_real_feature_change_updates_full_workflow` to use semantic web verification evidence (`semantic:web-cart-button:src/main.ts`) instead of `rg "Add to cart" src/main.ts` source-grep evidence.
- Updated `docs/aegis/live-acceptance-matrix.md` and mirrored `aegis_foundation/assets/docs/aegis/live-acceptance-matrix.md` to state that app behavior evidence should be semantic, while Aegis protocol literals remain intentional.
- Focused suite passed: 83 passed, 4 optional smoke tests skipped. Ruff passed for modified Python test files.