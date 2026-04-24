# Task 100 Foundation Bootstrap Layer Outline

## Objective

Provide a reusable bootstrap path so a new or existing repository can adopt the portable workflow foundation without manually copying configuration, policy files, or lifecycle scaffolding one file at a time.

## Inputs

- `templates/engine/core/portable-foundation-spec.md`
- `docs/ai/work-tracking/archive/20260424-task98-externalize-repo-structure-config-COMPLETED/designs/repo-structure-config-contract.md`
- `.codex/config.toml`
- `templates/metadata/template-metadata-policy.json`
- current helper surfaces in `scripts/codex-task` and `scripts/codex-guard`

## Bootstrap Deliverables

1. A bootstrap command under the existing `scripts/codex-task` surface.
2. Starter assets for repo-local configuration and policy files.
3. Migration-safe behavior for repositories that already contain workflow directories or template docs.
4. Setup documentation that explains how to initialize the foundation and how to review the generated state.

## Recommended Direction

### Command surface

Keep bootstrap inside `python3 scripts/codex-task` rather than introducing a parallel standalone installer. That preserves one operational entrypoint for kickoff, archive, plan sync, audit, and bootstrap.

### Bootstrap flow

The bootstrap command should:

1. read the portable foundation contract and repo-structure defaults
2. generate starter repo-local config and policy assets
3. scaffold missing workflow roots without overwriting existing repo content by default
4. emit a summary of created, skipped, and pre-existing files so adoption is reviewable

### Migration-safe rules

- never overwrite an existing config or policy file without explicit force
- create missing directories and starter files only where they do not exist
- treat existing workflow roots as valid inputs rather than errors
- keep generated paths rooted in `[repo_structure]` defaults or user-provided overrides

## Out of Scope

- cross-project fixture coverage for multiple repo shapes
- migration guides for humans beyond the bootstrap quickstart
- UI/dashboard work

Those belong to Tasks 101 and 102.
