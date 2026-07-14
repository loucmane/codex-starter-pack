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

- Contract: `docs/ai/work-tracking/archive/20260713-task241-quiet-deterministic-witness-COMPLETED/designs/quiet-witness-contract.md`
- Runtime: `.claude/scripts/witness_lib.py`
- Packaged mirror: `aegis_foundation/assets/.claude/scripts/witness_lib.py`
- CLI: `aegis_foundation/cli.py`
- Regressions: `tests/claude_adapter/test_witness.py`

## Continuation

Signed implementation commit `9fd71b5734c9ada5cea48942ad5f65d6ab588746`
passes the exact registered gate with 1,772 tests and four documented opt-in skips.
The real witness passed at exact HEAD in 0.18 seconds with 17 lines / 797 bytes,
58/58 paths accounted, complete JSON/Markdown artifacts, and a generated legacy
projection. The canonical ledger is readable but not writable in the current Remote
Control sandbox, so the successful local dogfood used a clearly labelled isolated
out-of-worktree store and did not claim canonical capture. Complete Taskmaster/source
closeout, create a signed terminal commit, publish through normal exact-head policy,
and require hosted CI. Preserve all unrelated primary-checkout drift.
