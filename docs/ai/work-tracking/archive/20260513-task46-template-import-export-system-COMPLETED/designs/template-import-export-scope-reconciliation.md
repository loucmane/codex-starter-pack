# Task 46 Template Import/Export Scope Reconciliation

## Purpose

Task 46 was originally written as a broad template portability and sharing task: ZIP bundle format, dependency resolution, import conflict detection, marketplace integration, signing, compatibility checks, preview, and bulk import/export.

The project has since moved to a portable-foundation architecture with local registries, explicit metadata, static audits, and non-destructive planning helpers. This document reconciles the old task text with the current system so implementation stays useful and bounded.

## Current Evidence

| Surface | Current State | Evidence |
| --- | --- | --- |
| Template registry | `TemplateRegistry` discovers templates from the configured template root and `templates/registry/index.json`, resolves IDs, paths, compatibility redirects, legacy files, and Serena fallback messages. | `scripts/template_registry.py`; Task 8 handoff |
| Discovery API | `TemplateDiscoveryAPI` wraps registry lookup, search, category listing, serialization, and dependency resolution from template frontmatter. | `scripts/template_registry.py`; Task 22 handoff |
| Metadata contract | Frontmatter schema already defines `id`, `title`, `type`, `status`, `category`, `version`, `dependencies`, `exports`, and tags. | `templates/metadata/template-frontmatter.schema.json`; Task 21 |
| Compatibility | Legacy-to-current template path compatibility map exists and is consumed by the registry. | `templates/registry/compatibility-map.json`; Task 13 |
| Lifecycle governance | Static lifecycle policy and audit helper already classify template states without mutating templates. | `scripts/template_lifecycle.py`; Task 29 |
| Bootstrap portability | `codex-task bootstrap init` scaffolds starter foundation directories and policy files into target repositories. | `scripts/codex-task`; Task 100 |
| Cross-repo sync | `codex-task sync plan` compares foundation assets between source and target repos without copying files. | `scripts/codex-task`; Task 30 |

## Scope Decision

Task 46 should implement a local, deterministic template bundle planner, not a hosted marketplace or cryptographic package manager.

The selected implementation target is:

- Add a `codex-task template bundle-plan` helper.
- Resolve requested templates through `TemplateRegistry` and `TemplateDiscoveryAPI`.
- Include dependency resolution using current template frontmatter.
- Emit a JSON manifest and Markdown runbook.
- Include compatibility and conflict preview data for a target repository.
- Stay non-destructive: no ZIP creation, extraction, marketplace publishing, remote calls, signing keys, or target-repo writes.

## Why This Is The Correct Gap

The current foundation already has the registry, metadata, compatibility, lifecycle, bootstrap, and cross-repo sync pieces. What is missing is the bridge between "I know which template I want" and "I can safely move or share this template set with another project." A bundle-plan helper gives agents and humans a portable handoff artifact while preserving the project's established static-file-backed and non-destructive workflow.

## Deferred Historical Scope

| Historical Item | Task 46 Treatment | Reason |
| --- | --- | --- |
| ZIP bundle generation | Deferred | Archive format is secondary until the manifest and conflict preview are proven. |
| Import/extract mutations | Deferred | Current foundation favors non-destructive plans first, then explicit apply steps. |
| Hosted marketplace integration | Out of scope | No marketplace service exists in the repo, and portability currently means local/cross-repo use. |
| Template signing | Deferred | Requires key management, trust policy, and verification workflow beyond this low-priority task. |
| Bulk import/export | Deferred | Can layer on top of deterministic bundle plans after the single-plan contract stabilizes. |
| Template preview UI | Deferred | No UI/dashboard surface is required for the current portability gap. |

## Proposed Command Contract

```bash
python3 scripts/codex-task template bundle-plan \
  --template <id-or-path> \
  --template <id-or-path> \
  --target-dir <target-repo> \
  --label <label> \
  --report-file <manifest.json> \
  --runbook-file <runbook.md>
```

The command should:

- Resolve each requested template to a registry record.
- Add frontmatter dependencies to the plan.
- Report missing templates and unresolved dependencies.
- Compare each planned source path against the optional target repository.
- Classify target conflicts as `missing`, `identical`, `different`, or `source-missing`.
- Recommend verification commands using existing bootstrap, guard, registry, and Taskmaster health surfaces.
- Write only the requested manifest/runbook files in this repository unless `--dry-run` is used.

## Acceptance Criteria

- The command is parser-visible as `python3 scripts/codex-task template bundle-plan`.
- Unit tests cover parser support, dependency inclusion, missing dependency reporting, target conflict classification, and dry-run output.
- Evidence is captured under `reports/template-import-export-system/` inside this active work-tracking folder.
- Plan/tracker/session entries cite this scope document before implementation is marked complete.
