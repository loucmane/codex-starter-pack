# Task 36 Template Governance Scope Reconciliation

**Captured**: 2026-05-12 15:48 CEST  
**Task**: 36 - Implement Template Governance Board

## Historical Task Wording

Task 36 asks for a template governance board:

- board composition and roles
- charter and responsibilities
- weekly meeting schedule during migration
- change review process
- voting mechanism for breaking changes
- decision tracking
- escalation procedures
- stakeholder notification system

That wording predates the current portable foundation. Treat it as historical intent, not a mandate to create live meeting, notification, or service infrastructure.

## Current Repository Evidence

- `templates/engine/core/portable-foundation-spec.md` defines the portable foundation and separates core behavior from repo-local adapter policy.
- `templates/metadata/template-lifecycle-policy.json` and `scripts/template_lifecycle.py` provide lifecycle states, transitions, deprecation thresholds, and non-mutating lifecycle audit behavior.
- `templates/metadata/template-versioning-policy.json` and `scripts/template_versioning.py` provide semantic version comparison, compatibility assessment, migration-required detection, rollback target data, and reviewable history entries.
- `templates/handlers/triggers/docs/record-decision.md` documents the decision-record handler, and active work-tracking folders already provide `DECISIONS.md`, `FINDINGS.md`, `CHANGELOG.md`, `IMPLEMENTATION.md`, and `HANDOFF.md`.
- There is no repo-local governance policy that maps lifecycle transitions, version change classes, or emergency flags to a required review class, reviewers, approval model, escalation path, and notification evidence.

## Scope Decision

Task 36 should implement a lightweight, file-backed governance assessor, not a human board workflow or external notification system.

Implementation should:

- add a repo-local governance policy under `templates/metadata/`
- load that policy through the configured portable templates root
- map change signals to governance review classes such as routine, coordinated, breaking, and emergency
- expose a non-mutating CLI that assesses a proposed template change and prints the required review path
- include role, approval, escalation, notification, and required evidence fields in the assessment payload
- integrate with the existing versioning helper for version-change classification when previous/current versions are supplied
- keep notifications as evidence instructions only; do not send messages or call external services
- add focused tests for policy loading, decision precedence, version-change integration, lifecycle-transition handling, CLI output, and real-policy behavior

## Out of Scope

- Live calendar scheduling, recurring meetings, or meeting tools.
- Automatic votes, chat notifications, webhooks, email, dashboards, or stakeholder delivery.
- Mutating template files or work-tracking files from the governance helper.
- Replacing `DECISIONS.md`, lifecycle policy, versioning policy, emergency response policy, or Taskmaster.
- Adding repo-level pre-commit/pre-push hooks; those belong to hook/CI tasks.

## Proven Gap

The current foundation can answer whether a template lifecycle state or version transition is valid, but it cannot answer:

- Which review class does this proposed change require?
- Which roles must review it?
- Is a single owner approval enough, or does the change need quorum/unanimous approval?
- What escalation path applies to a breaking or emergency template change?
- Which evidence artifacts should be attached before the change is considered governed?
- Which audiences need notification evidence, without sending notifications automatically?

## Implementation Boundary For 36.2

Expected code/data/test surface:

- `templates/metadata/template-governance-policy.json`
- `scripts/template_governance.py`
- `tests/meta_workflow_guard/test_template_governance.py`
- Task 36 work-tracking evidence under `reports/template-governance-board/`

Expected behavior:

- governance policy loads from `.codex/config.toml` configured templates root
- review class precedence is deterministic: emergency > breaking > coordinated > routine
- major/downgrade version changes require breaking review
- prerelease changes require coordinated review
- stable-to-deprecated, stable-to-archived, deprecated-to-stable, and archived transitions require breaking review
- emergency flag forces emergency review
- CLI supports text and JSON output without mutating repository files

## Verification Plan

- Run focused governance tests.
- Run lifecycle and versioning tests to confirm the assessor complements existing helpers.
- Run Taskmaster health, plan sync, work-tracking audit, guard, and diff-check before closeout.
