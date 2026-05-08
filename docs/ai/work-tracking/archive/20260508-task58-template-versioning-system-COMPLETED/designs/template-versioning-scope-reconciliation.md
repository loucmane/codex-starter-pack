# Task 58 Template Versioning Scope Reconciliation

**Captured**: 2026-05-08 20:33 CEST  
**Task**: 58 - Implement Template Versioning System

## Historical Task Wording

Task 58 asks for robust template versioning:

- semantic versioning for templates
- version comparison logic
- backward compatibility checking
- version migration tools
- version history tracking
- version conflict resolution
- rollback capability
- version documentation

That wording predates the current portable foundation, so the implementation must reconcile it against already-completed registry, lifecycle, and scanner work before adding new behavior.

## Current Repository Evidence

- Task 28 completed dual-path discovery by extending `scripts/template_registry.py` with compatibility redirects, discovery traces, local suggestions, and usage metrics.
- Task 29 completed template lifecycle management with `templates/metadata/template-lifecycle-policy.json`, `scripts/template_lifecycle.py`, semantic version bumping, deprecation audit, and lifecycle schema fields.
- Task 29 explicitly kept full version history, rollback, and compatibility migration tooling out of scope because Task 58 owns robust template versioning later.
- `templates/metadata/template-frontmatter.schema.json` already defines a `version` field and lifecycle metadata fields.
- `scripts/template_registry.py` can serialize and exact-filter record metadata versions, but it does not compare semantic versions or assess compatibility between two versions.
- There is no portable versioning policy file that tells callers which version changes are compatible, require migration, or should generate warnings.

## Scope Decision

Task 58 should add a non-mutating versioning layer over the existing lifecycle and registry foundation. It should not duplicate lifecycle state handling, discovery behavior, or scanner metadata collection.

Implementation should:

- add a repo-local versioning policy file under `templates/metadata/`
- load that policy through the configured portable templates root
- parse and compare semantic template versions, including prerelease ordering and build-metadata handling
- classify version changes as `same`, `patch`, `minor`, `major`, `downgrade`, `release`, or `prerelease`
- assess backward compatibility from a previous/current version pair using policy-defined change classes
- generate structured, reviewable history entries with compatibility and rollback target data
- expose a small non-mutating CLI for comparison, assessment, and history-entry generation
- add focused tests for policy loading, comparison, compatibility assessment, rollback-plan data, and CLI behavior

## Out of Scope

- Bulk editing template frontmatter.
- Automatically migrating templates.
- Moving templates between lifecycle states.
- Executing rollback or mutating files as part of rollback.
- Replacing `scripts/template_lifecycle.py` semver bumping; Task 58 complements it with comparison and compatibility assessment.
- Replacing registry discovery, compatibility maps, or scanner metadata.

## Proven Gap

The repository can bump a version and discover a template's current metadata version, but it cannot answer:

- Is `1.2.0` older than `1.2.0-rc.1`, and how should prereleases compare?
- Is a change from `1.2.3` to `1.3.0` backward compatible under repo policy?
- Does a change from `1.2.3` to `2.0.0` require migration guidance?
- What rollback version should a reviewable history entry point to?
- Can a caller produce deterministic version evidence without changing template files?

## Implementation Boundary For 58.2

Expected code/data/test surface:

- `templates/metadata/template-versioning-policy.json`
- `scripts/template_versioning.py`
- `tests/meta_workflow_guard/test_template_versioning.py`
- Task 58 work-tracking evidence under `reports/template-versioning-system/`

Expected behavior:

- versioning policy loads from `.codex/config.toml` configured templates root
- semantic versions normalize `MAJOR.MINOR` to `MAJOR.MINOR.0` for compatibility with existing lifecycle behavior
- comparison ignores build metadata and orders prerelease identifiers deterministically
- compatibility assessment is policy-driven and non-mutating
- history entries include path, previous version, current version, change type, compatibility result, migration requirement, rollback target, timestamp, and optional note
- CLI output is available as text or JSON for automation and evidence capture

## Verification Plan

- Run focused Task 58 versioning tests.
- Run lifecycle and registry tests to ensure the new helper complements rather than breaks existing foundation behavior.
- Run full pytest before closeout.
- Capture plan sync, work-tracking audit, guard, diff-check, and Taskmaster health evidence.
