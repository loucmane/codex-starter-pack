# Task 154 Scope Evidence

## Objective

Harden the reconcile apply validation path so a future status write is checked at both layers:

- Path layer: unexpected files, directories, symlinks, modes, or refs remain blocked by the existing side-effect oracle.
- Semantic layer: expected aggregate files must only contain the approved semantic change for the target task.

## In Scope

- Add semantic validation for `.taskmaster/tasks/tasks.json` after applying the same canonicalization model to before and after content.
- Treat Taskmaster toolchain normalization as version-scoped canonicalization, not as a broad exemption for arbitrary cross-task changes.
- Ensure the only surviving semantic difference for a valid apply is the target task status moving to `done`.
- Add generated task markdown validation for the target task artifact.
- Add type-sensitive task id comparison coverage so numeric/string normalization cannot break task joins.
- Harden terminal rollback failure handling with a hard-deny state, governed-repo target refusal, behavioral reachability checks, and enable-source checks.

## Out of Scope

- No enablement of live apply.
- No `--apply`, MCP apply tool, codex-task agent route, or operator-local apply.
- No post-merge shadow accumulation.
- No hand-editing Taskmaster-owned state to clean up normalization.

## Design Notes

Task 153 proved the write apparatus is default-off and rollback-capable, but marking the task done through Taskmaster normalized id/dependency types across `tasks.json`. That is an expected toolchain transform, but it exposed a path-level blind spot: a path delta of `tasks.json` alone does not prove that only the target task changed.

Task 154 therefore keeps the existing path oracle as the outer boundary and adds a semantic validator inside it. The validator parses both snapshots, canonicalizes both under the pinned Taskmaster toolchain model, and compares the semantic result. Canonicalization must factor out known representation churn; it must not become an allow-all bucket for unrelated dependency, id, title, priority, or status changes.

## Acceptance Gate

Before implementation begins:

- Taskmaster Task 154 is `in-progress`.
- Task 153 work tracking has been archived through `scripts/codex-task work-tracking archive`.
- This scope evidence exists and is referenced by the active plan.
- The active tracker records scope and Serena memory evidence for the session.
