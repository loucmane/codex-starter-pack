# Task 49 Communication Templates Scope Reconciliation

## Purpose

Reconcile Taskmaster Task 49's historical "communication templates" wording with the current portable foundation before implementation.

Task 49 originally mentions weekly status templates, distribution-list management, a communication archive, automated template filling, and feedback collection. That wording came from an earlier migration-operations backlog. The current repository now operates as a portable Codex foundation with Taskmaster tasks, session logs, plans, work-tracking folders, guard validation, template metadata, direct Git execution, and a Claude runtime adapter.

## Current Evidence

- `templates/guides/index.md` is the current guide hub for foundation onboarding, Taskmaster alignment, work-tracking enforcement, session lifecycle, and Claude runtime behavior.
- `templates/guides/training/foundation-onboarding.md` trains the current workflow but does not provide reusable communication payloads for PRs, task completion, breaking changes, incidents, milestones, or feedback capture.
- `templates/conventions/git/pr-conventions.md` contains a generic PR template, but it is not tied to Taskmaster IDs, work-tracking folders, evidence logs, guard output, or the direct Git execution mode.
- `templates/conventions/git/commit-format.md` defines the current commit/Git response modes and explicitly reserves `gac` for explicit user requests only.
- `templates/workflows/session/lifecycle.md` and `templates/workflows/taskmaster/alignment.md` define session and evidence behavior, but they do not package user-facing communication templates.
- No `.github/PULL_REQUEST_TEMPLATE*` file exists, and there is no dedicated `templates/guides/communication/` guide.

## Scope Decision

Implement Task 49 as repository-native communication templates for the current foundation, not as external distribution-list or enterprise-status automation.

In scope:

- Add a governed guide with copy-ready templates for current repo communication.
- Cover PR descriptions, task completion updates, breaking-change notices, incident/regression notices, milestone announcements, and feedback/follow-up capture.
- Require communication payloads to cite Taskmaster IDs, active work-tracking folders, S:W:H:E evidence, guard/test evidence, and direct Git/GitHub state where relevant.
- Update the guide hub so maintainers can discover the communication guide.
- Add focused tests that validate guide metadata, navigation, required sections, links, and workflow/evidence commands.

Out of scope:

- Distribution-list management.
- Automated email or chat delivery.
- External communication archives outside the repository.
- Replacing GitHub PR UI fields with a committed `.github/PULL_REQUEST_TEMPLATE*`.
- Broad rewrites of the existing generic PR convention or session lifecycle documents.

## Proposed Implementation Surface

- `templates/guides/communication/foundation-communication-templates.md`
- `templates/guides/index.md`
- `tests/meta_workflow_guard/test_communication_templates.py`
- Work-tracking docs and verification evidence under this Task 49 folder.

## Verification Strategy

- Focused test for communication guide metadata and links.
- Focused test for required communication-template sections and evidence commands.
- Focused test that the guide hub links to the communication guide.
- Guard validation to confirm the new guide follows metadata policy.
- Plan sync, work-tracking audit, Taskmaster health, and diff-check evidence before commit.
