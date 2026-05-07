# Task 21 Template Frontmatter Schema – Handoff Summary

## Current State
- Task 21 is active on `feat/task-21-template-frontmatter-schema`.
- Scope reconciliation is complete: Task 21 builds on Task 91 instead of repeating broad metadata migration work.
- Added `templates/metadata/template-frontmatter.schema.json` as the permanent frontmatter schema contract.
- Updated `templates/metadata/template-metadata-policy.json` to reference the schema through policy defaults.
- Updated `scripts/codex-guard` to parse YAML frontmatter, validate it through `jsonschema`, and then apply policy-required key checks.
- Focused guard tests passed with `66 passed`.
- Broader guard/task helper tests passed with `94 passed`.
- Taskmaster Task 21, subtask 21.1, and subtask 21.2 are done.
- Final verification evidence is stored in `reports/template-frontmatter-schema/final-verification-2026-05-07.md`.
- PR #41 initially failed because CI did not install `pyyaml`/`jsonschema` dependencies before importing `scripts/codex-guard`; both guard workflows now install project dependencies from `pyproject.toml`.

## Next Steps
- Push the CI fix commit, confirm PR #41 checks pass, merge, then archive the active Task 21 work-tracking folder.
- Archived on 2026-05-07 16:57 CEST — Folder moved to archive and tracker marked COMPLETED.
