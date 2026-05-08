# Task 33 Training Materials Scope Reconciliation

## Purpose

Reconcile Taskmaster Task 33's historical "training materials" wording with the current repository state before implementation.

Task 33 originally mentions interactive tutorials, recorded videos, office hours, knowledge-base articles, exercises, certification checklists, and feedback surveys. That wording came from an earlier migration phase. The current repository has since shifted into a portable foundation with Codex workflow enforcement, Taskmaster integration, a template registry, lifecycle policy, Claude runtime adapter, and repository-portability helpers.

## Current Evidence

- `templates/guides/index.md` and `templates/guides/quickstart/getting-started.md` exist, but they are Claude-centered user guides from an older state.
- `templates/guides/index.md` references several files that do not exist in the current tree, including `quickstart/first-request.md`, `reference/quick-actions.md`, `troubleshooting/errors.md`, `troubleshooting/performance.md`, `workflows/advanced.md`, and advanced handler/system-extension paths.
- Current foundation adoption material exists in `templates/engine/validation/foundation-adoption-guide.md`.
- The Claude runtime contract exists in `.claude/engine/runtime-contract.md`.
- Task 31 compaction protocol is done, so training material can reference the current compaction/session lifecycle instead of old "memory only" behavior.
- The current template system already has metadata, registry, lifecycle, and guard coverage. Task 33 does not need to create another registry or workflow engine.

## Scope Decision

Implement Task 33 as repository-native training/onboarding material for the current portable foundation, not as external training operations.

In scope:

- Add a current training path for new maintainers/users of the Codex foundation and Claude runtime adapter.
- Include hands-on exercises that can be performed inside a real task session without bypassing the workflow.
- Include a completion checklist that proves the user understands session start, work tracking, plan sync, guard, evidence, PR merge, and archive closeout.
- Update guide navigation so it points to existing, current files.
- Add focused tests that validate the training guide navigation and the minimum expected training sections.

Out of scope:

- Recording videos.
- Scheduling office hours.
- Creating external feedback surveys.
- Replacing the portable foundation specification, runtime contracts, or Taskmaster workflows.
- Broadly fixing every historical guide in `templates/guides/`.

## Proposed Implementation Surface

- `templates/guides/training/foundation-onboarding.md`
- `templates/guides/index.md`
- `tests/meta_workflow_guard/test_training_materials.py`
- Work-tracking docs and final evidence under this Task 33 folder.

## Verification Strategy

- Focused test for training guide metadata, required sections, and links to existing repository paths.
- Focused test for `templates/guides/index.md` links so new navigation does not point to missing guide files.
- Guard validation to confirm new guide metadata follows the current template metadata policy.
- Plan sync, work-tracking audit, Taskmaster health, and diff-check evidence.
