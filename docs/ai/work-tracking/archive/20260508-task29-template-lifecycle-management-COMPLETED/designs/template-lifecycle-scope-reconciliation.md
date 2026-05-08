# Task 29 Template Lifecycle Scope Reconciliation

## Current-State Findings

- Task 91 established the portable metadata baseline: `title`, `type`, and `status`.
- Task 21 added `templates/metadata/template-frontmatter.schema.json` and wired schema-backed metadata validation into `scripts/codex-guard`.
- Task 8 added `scripts/template_registry.py`, which discovers template records and exposes parsed `status` metadata, but it does not define lifecycle transitions or deprecation rules.
- Current real template statuses are mostly `stable`, with smaller `draft`, `beta`, and `deprecated` slices. `templates/registry/index.md` uses `status: modular` as an aggregate registry exception.
- The existing schema allows `stable`, `beta`, `deprecated`, `draft`, and `experimental`; it does not include the historical Task 29 `review` or `archived` states.
- The repository has at least one real deprecated template tombstone, `templates/behaviors/session/compaction-detection.md`, but there is no machine-readable lifecycle audit for deprecation age, migration notice, replacement target, or archival readiness.

## Scope Decision

Task 29 should not mass-rewrite templates or implement a destructive auto-archival mover. The current proven gap is a portable lifecycle policy and audit layer over existing template metadata.

Implementation should:

- add a repo-local lifecycle policy file under `templates/metadata/`
- keep lifecycle semantics data-driven and portable through the configured templates root
- support canonical lifecycle states `draft`, `review`, `stable`, `deprecated`, and `archived`
- preserve existing compatibility states such as `beta` and `experimental` by mapping them onto canonical lifecycle phases rather than breaking current metadata
- extend the frontmatter schema with lifecycle metadata fields such as `deprecated_since`, `replacement`, `migration_notice`, and `archive_after`
- add a small lifecycle helper module that can validate transitions, bump semantic versions, generate deprecation/migration warnings, and audit template records without mutating files
- add focused tests for transition rules, version bumping, deprecation grace/archival logic, policy loading, and real registry audit behavior

## Out of Scope

- Bulk status migration across `templates/**`.
- Moving template files to archive automatically.
- Full version history, rollback, or compatibility migration tooling; Task 58 covers robust template versioning later.
- Replacing the template registry or guard metadata policy.
- Treating `beta` and `experimental` as errors before a separate migration plan exists.

## Proven Gap

The repo has schema-backed metadata and registry discovery, but no central lifecycle contract that callers can use to answer:

- Is this status canonical, compatibility-only, or invalid?
- Is a transition from one lifecycle state to another allowed?
- What semantic version should follow a major/minor/patch bump?
- Should a deprecated template emit a migration warning?
- Has the 30-day deprecation grace period expired?
- Is the template past the 90-day archival threshold?

## Implementation Boundary For 29.2

Expected code/data surface:

- `templates/metadata/template-lifecycle-policy.json`
- `scripts/template_lifecycle.py`
- `tests/meta_workflow_guard/test_template_lifecycle.py`
- targeted schema update in `templates/metadata/template-frontmatter.schema.json`

Expected behavior:

- lifecycle policy loads from the configured templates root
- canonical transitions are deterministic and tested
- compatibility statuses map to canonical lifecycle phases
- semver bumping handles major, minor, and patch increments
- deprecated templates produce structured warnings and archival recommendations based on dates and policy thresholds
- the module reports audit results without modifying template files

## Verification Plan

- Run focused lifecycle tests.
- Run template registry tests to ensure registry behavior still sees metadata correctly.
- Run guard metadata tests to confirm schema-backed validation still accepts governed templates.
- Run full pytest before closing the task.
- Capture plan sync, audit, guard, and diff-check evidence.
