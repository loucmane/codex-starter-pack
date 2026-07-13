# Task 241 Quiet Deterministic Witness

## Scope

Task 241 makes `aegis witness` the quiet, deterministic pre-delivery boundary while
preserving advisory enforcement, legacy plans/sessions/trackers/handoffs, and S:W:H:E
narration as complementary context.

## Binding Decisions

- Semantic classes are `pass`, `fail`, `unsupported`, and
  `not_derivable_in_ci`; process exits are 0, 1, 2, and 0 respectively.
- Deterministic safety failures outrank incomplete evidence. CI cannot hide a test
  deletion or other git-derivable failure behind a not-derivable result.
- Local ledger evidence is filtered by repository, branch, and canonical worktree;
  null attribution remains readable only for legacy compatibility.
- Verification requires exact current HEAD identity. Event timestamps never substitute
  for commit identity.
- Complete JSON and Markdown delivery artifacts retain every path; only agent-facing
  stdout is context-budgeted.
- Native CI remains delegated, no LLM or prose reconciliation is introduced, and no
  PR-4 retirement is authorized.

## Evidence

- Contract: `docs/ai/work-tracking/active/20260713-task241-quiet-deterministic-witness-ACTIVE/designs/quiet-witness-contract.md`
- Runtime: `.claude/scripts/witness_lib.py`
- Packaged mirror: `aegis_foundation/assets/.claude/scripts/witness_lib.py`
- CLI: `aegis_foundation/cli.py`
- Regressions: `tests/claude_adapter/test_witness.py`

## Continuation

Implement the contract in the isolated Task 241 worktree, run focused and broad tests,
dogfood the real branch, store measurements and rollback evidence, then complete and
publish Task 241 through normal exact-head policy. Preserve all unrelated primary-checkout
drift.
