# Task 254 Complete strict Codex hook-trust portability contract – Implementation Notes

## Implemented workstreams

### Tracked contract and schema

- Extended both byte-identical installer assets so `codex.hook_trust` persists the exact
  `settings_path`, `review_command`, `hash_scope`, and `bypass_allowed` contract.
- Extended both byte-identical foundation-manifest schemas with an exact conditional contract for
  the `codex.hook_trust` gate.

### Strict verification

- Strict verification now reads and validates the tracked manifest gate.
- Generated install-report data is supplemental diagnostic evidence only.
- Verification explicitly reports that it does not assert client-local trust.
- Invalid, missing, bypass-permitting, wrong-path, wrong-command, or weak-hash tracked guidance
  fails closed even when a stale install report contains previously valid guidance.

### Regression coverage

- Added clean clone/worktree strict verification and closeout dry-run coverage.
- Added valid-with/without-report, malformed contract, stale report, and changed-hook-definition
  renewal coverage.
- Added safe migration coverage from the Task 253 manifest shape.
- Kept root/package installer and schema assets byte-identical.

### Target acceptance

- Reproduced `/tmp/blog-task42` failing only `codex.hook_trust_guidance` under the previous source.
- Re-ran strict verification with Task 254 runtime and explicit tracked guidance: zero required
  failures without copying or synthesizing an install report.
- Restored the original manifest/report/capsule bytes in a `finally` boundary and proved the exact
  dirty status plus all 1,031 Git-visible Task 42 records were unchanged.
