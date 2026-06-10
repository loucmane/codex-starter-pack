# Task 209 Capsule PR-3.5: delivery witness v0 – Implementation Notes

## What was built
- witness_lib.py (assets + live mirror, stdlib-only): the four deterministic checks
  from spec 5.1 — scope mapping (confirmed scope record > inferred > task-NN branch
  convention), diff accounting against scope globs + brief.json witness.always_in_scope
  with DELETED-test escalation, verification-at-head from the ledger (commit equality
  OR a pass recorded after the head commit existed — the spec's at-or-after wording),
  and done-flip containment (uncommitted tasks.json done-flips fail). CI greenness is
  DELEGATED to native required checks, never re-implemented. Output = the generated
  delivery report (.aegis/reports/witness-report.json + rendered summary) — the
  replacement for the old hand-fed closeout.
- aegis witness CLI (--base/--json/--ci, exit 0/1), read-only gate classification.
- .github/workflows/aegis-witness.yml running `aegis witness --ci` on PRs (dogfood).
  Flipping it to a REQUIRED check is the owner's branch-protection action.
- Spec-revision finding (CI split): the out-of-worktree ledger does not travel to CI,
  so a required check cannot evaluate ledger-dependent verification; --ci runs the
  git+config-derivable checks and reports verification_at_head as not_derivable_in_ci.
  Full resolution (witness report as PR artifact/attestation) feeds the next spec rev.
- Dogfood: this repo's own .aegis/brief.json seeded (codex:tests gate, source_roots,
  always_in_scope); first live witness run correctly FAILED verification_at_head
  because no suite run was on record at that HEAD — negative-space teeth working.

## Verification
12 new tests: in-scope pass, out-of-scope fail, test-deletion escalation, stale vs
after-head verification, confirmed-scope precedence, done-flip containment, CI split,
CLI exit codes, delegation, gate classification, support files, copy parity. Full
suite 1284 passed.
