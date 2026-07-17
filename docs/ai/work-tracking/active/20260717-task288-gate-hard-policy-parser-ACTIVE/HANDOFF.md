# PR Scope 288 Gate Hard-Policy Parser - Handoff

## Current state

- Test-first gate implementation is committed in the standalone clone.
- Source and packaged gate files are byte-identical.
- Focused and adjacent local regression suites pass.
- Draft PR #289 is open from exact head `2c9f71cb44d7a7dfeccded84b93a7590776f6e11`.
- Python 3.11/3.12, all guard jobs, Aegis witness, and evidence-gated delivery passed.
- Taskmaster and the dirty primary checkout remain untouched.

## Remaining prerequisite-PR work

1. Push the evidence-only workflow update and confirm its final CI rerun.
2. Do not auto-merge the draft PR.
3. Finish read-only tx35a Checkpoint A and stop at that boundary.

## Safety boundary

Do not modify `/home/loucmane/codex`, Taskmaster, Gas City runtime state, or credentials as
part of this PR. Any contradiction stops the transaction.
