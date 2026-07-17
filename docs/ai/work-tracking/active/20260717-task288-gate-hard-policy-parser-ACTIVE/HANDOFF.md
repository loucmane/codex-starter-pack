# PR Scope 288 Gate Hard-Policy Parser - Handoff

## Current state

- Test-first gate implementation is committed in the standalone clone.
- Source and packaged gate files are byte-identical.
- Focused and adjacent local regression suites pass.
- Workflow metadata remediation is in progress for guard/witness CI.
- Taskmaster and the dirty primary checkout remain untouched.

## Remaining prerequisite-PR work

1. Synchronize plan/tracker state.
2. Run local plan, guard, witness, parity, and focused regression checks.
3. Push the task-scoped branch and open a replacement draft PR.
4. Confirm required PR checks are green; do not auto-merge.
5. Continue with read-only tx35a Checkpoint A and stop at that boundary.

## Safety boundary

Do not modify `/home/loucmane/codex`, Taskmaster, Gas City runtime state, or credentials as
part of this PR. Any contradiction stops the transaction.
