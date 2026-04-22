# Task 91 Template Metadata Inventory

## Inventory Timestamp
- 2026-04-21 17:17 CEST

## Summary
- Total markdown files under `templates/`: 256
- Files with no parseable frontmatter block: 42
- Files missing `title`: 115
- Files missing `type`: 85
- Files missing `status`: 121

## Observed Classes

### 1. Fully annotated modular templates
The dominant healthy pattern already present in the repo is:

```yaml
---
id: ...
type: ...
category: ...
title: ...
status: stable
---
```

Examples:
- `templates/shared/tools/tool-selection-matrix.md`
- many entries already surfaced through `templates/metadata/template-overview.md`

### 2. Partially annotated modular templates
Many handler, behavior, and engine module files already have frontmatter but rely on older keys such as:
- `name`
- `role`
- `domain`
- `stability`
- `trigger`
- `action`

Representative examples:
- `templates/handlers/orchestrators/session-start.md`
- `templates/behaviors/session/session-end.md`
- `templates/engine/core/session-resolver.md`

These appear to be the primary batch-update targets for Task 91.

### 3. Aggregate, index, and report-style docs with no frontmatter
The repo also contains top-level and generated/reference-style docs that currently have no frontmatter:
- `templates/BEHAVIORS.md`
- `templates/CONVENTIONS.md`
- `templates/HANDLERS.md`
- `templates/MATRICES.md`
- `templates/TOOLS.md`
- `templates/USER-GUIDE.md`
- `templates/metadata/template-overview.md`
- `templates/engine/README.md`

These should not automatically be treated the same as modular templates until the schema boundary is defined.

## Initial Scope Conclusion
- Task 91 is not just a guard tweak; there is material metadata debt in the template tree.
- The first-pass rollout should focus on true modular template files before deciding how to treat aggregate/generated docs.
- `title`, `type`, and `status` are the most obvious cross-cutting keys to standardize because they already appear throughout the metadata and discoverability surfaces.

## Post-Handler Slice Snapshot
After standardizing all handler families (`triggers`, `orchestrators`, `operators`), the repo-wide counts became:
- files with no frontmatter: 42
- files missing `title`: 43
- files missing `type`: 13
- files missing `status`: 49

This confirms the handler family was the highest-leverage first-pass target.

## Post-Behavior Slice Snapshot
After standardizing the behavior family (excluding the aggregate `templates/behaviors/index.md`), the repo-wide counts became:
- files with no frontmatter: 42
- files missing `title`: 32
- files missing `type`: 2
- files missing `status`: 38

This confirms the policy-driven rollout works across a second family with a different legacy frontmatter shape.

## Post-Guide Slice Snapshot
After standardizing the guide family and enabling the guide policy rule, the repo-wide counts became:
- files with no frontmatter: 42
- files missing `title`: 32
- files missing `type`: 1
- files missing `status`: 31

Remaining modular debt is now concentrated in:
- `templates/engine/**`
- `templates/matrices/**`
- `templates/registry/**`
- `templates/shared/patterns/ultrathink-format.md`
- `templates/handlers/tools/external/consult-gpt5.md`

## Post-Matrices Slice Snapshot
After standardizing all eight matrix files and enabling the matrices policy rule:
- every file under `templates/matrices/**` now carries `title`, `type`, and `status`
- `templates/matrices/index.md` remains policy-exempt as the aggregate navigation entry, but it still carries the canonical keys for consistency
- targeted guard tests, `codex-guard validate --include-untracked`, `codex-task work-tracking audit`, and `codex-task plan sync` all pass

Remaining non-exempt metadata debt is now concentrated in:
- `templates/registry/**`
- selected `templates/engine/**`
- `templates/shared/patterns/ultrathink-format.md`
- `templates/handlers/tools/external/consult-gpt5.md`

## Post-Registry Slice Snapshot
After standardizing the registry component family and enabling the registry policy rule:
- every non-exempt file under `templates/registry/**` now carries `title`, `type`, and `status`
- `templates/registry/index.md` remains policy-exempt as the aggregate registry entry, and `templates/registry/MIGRATION-REPORT.md` remains exempt as a narrative migration report
- targeted guard tests, `codex-guard validate --include-untracked`, and `codex-task work-tracking audit` all pass

Remaining non-exempt metadata debt is now concentrated in:
- selected `templates/engine/**`
- `templates/shared/patterns/ultrathink-format.md`
- `templates/handlers/tools/external/consult-gpt5.md`

## Progress Log
- **2026-04-21 17:17** — [S:20260421|W:task91-standardize-template-metadata|H:analysis|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-inventory.md] Recorded the kickoff metadata inventory and the three major file classes driving Task 91 scope
- **2026-04-21 17:30** — [S:20260421|W:task91-standardize-template-metadata|H:analysis|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-inventory.md] Recorded the post-handler-slice counts showing the largest metadata debt block has been standardized
- **2026-04-21 17:56** — [S:20260421|W:task91-standardize-template-metadata|H:analysis|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-inventory.md] Recorded the post-behavior-slice counts after enabling the second policy-driven family
- **2026-04-21 18:40** — [S:20260421|W:task91-standardize-template-metadata|H:analysis|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-inventory.md] Recorded the post-guide-slice counts and the now-concentrated remaining debt in engine, matrices, registry, shared patterns, and one external handler
- **2026-04-22 15:53** — [S:20260422|W:task91-standardize-template-metadata|H:analysis|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-inventory.md] Recorded the post-matrices slice status: eight matrix files standardized, matrices policy enabled, and the remaining non-exempt debt narrowed to registry, selected engine modules, and two outliers
- **2026-04-22 16:00** — [S:20260422|W:task91-standardize-template-metadata|H:analysis|E:docs/ai/work-tracking/active/20260421-task91-standardize-template-metadata-ACTIVE/designs/template-metadata-inventory.md] Recorded the post-registry slice status: registry components standardized and the remaining non-exempt debt narrowed to selected engine modules and two outliers
