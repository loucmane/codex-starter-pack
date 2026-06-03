# Task 155 Scope Note

## Objective

Task 155 is a test-only hardening pass for the semantic validator introduced in Task 154.

The implementation boundary is deliberately narrow:

- Add paired negative tests in `tests/meta_workflow_guard/test_aegis_reconcile_shadow_apply.py`.
- Exercise `validate_taskmaster_apply_semantic_delta` from `aegis_foundation/reconcile_shadow_apply.py`.
- Do not change production validator behavior unless an existing acceptance invariant is demonstrably wrong.
- Do not add apply enablement, CLI `--apply`, MCP apply surfaces, codex-task apply routes, or any agent-facing mutation path.

## Required Coverage

- Target status must transition exactly to `done`; non-`done` target statuses reject.
- Any non-target task status or content drift rejects.
- `updatedAt` and tag metadata exemptions remain narrow and do not hide adjacent semantic changes.
- Dependency ID type normalization does not hide dropped, added, or changed dependencies.
- Absent `subtasks` and empty `subtasks: []` are equivalent only for absent-vs-empty normalization; deleting real subtasks rejects.

## Verification Boundary

Required evidence:

- Focused shadow apply tests.
- Adjacent default-off apply apparatus tests.
- Ruff on the touched test file.
- Taskmaster health, work-tracking audit, Codex guard, and `git diff --check` before closeout.
