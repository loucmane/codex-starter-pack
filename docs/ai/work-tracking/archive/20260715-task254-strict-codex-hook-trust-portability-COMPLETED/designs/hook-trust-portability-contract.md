# Task 254 — Strict Codex Hook-Trust Portability Contract

## Problem

Strict verification must be reproducible from tracked repository state in a clean clone or
additional Git worktree. Generated `.aegis/reports/install-report.json` state is intentionally
ignored and worktree-local, so it cannot be the sole authority for the required Codex hook-trust
review procedure.

Task 253 removed the hard dependency on that report, but derived the procedure from runtime
constants. Task 254 makes the procedure explicit, schema-validated, and reviewable in the tracked
foundation manifest.

## Durable tracked contract

The managed `codex.hook_trust` manifest gate MUST contain exactly:

```json
{
  "settings_path": ".codex/hooks.json",
  "review_command": "/hooks",
  "hash_scope": "exact_hook_definition",
  "bypass_allowed": false
}
```

The root and packaged foundation-manifest schemas require these values whenever the gate ID is
`codex.hook_trust`. A missing gate, missing field, malformed field, alternate settings path,
alternate review command, weaker hash scope, or enabled bypass is invalid tracked guidance and
must fail strict verification.

## Authority separation

- The tracked manifest proves only the safe procedure an operator must use to review hook hashes.
- Actual Codex hook trust remains client/session-local and bound to the exact hook definition.
- A manifest, install report, reload marker, or successful verifier run MUST NOT assert that the
  client has trusted the hooks.
- Any managed hook-definition change requires renewed review through `/hooks`.

## Supplemental installation evidence

If `.aegis/reports/install-report.json` exists, strict verification may report whether its
reload/trust guidance is present and agrees with the tracked contract. That diagnostic is
supplemental only:

- its absence cannot fail an otherwise valid clean clone/worktree;
- its presence cannot repair invalid tracked guidance;
- stale report contents cannot override the manifest;
- it is never evidence that the client actually trusted a hash.

## Verification algorithm

1. Parse and schema-validate the tracked foundation manifest.
2. Locate exactly one `codex.hook_trust` gate.
3. Validate all four durable fields against the exact contract above.
4. Return a required failure if any tracked requirement is absent or weakened.
5. Attach supplemental install-report diagnostics without using them to determine pass/fail.
6. Explicitly report `client_trust_asserted: false`.

## Acceptance matrix

- Valid tracked guidance, no install report: pass.
- Valid tracked guidance, matching install report: pass.
- Missing or malformed tracked guidance: fail closed.
- `bypass_allowed: true`: fail closed.
- Wrong settings path, review command, or hash scope: fail closed.
- Stale matching report plus invalid tracked guidance: fail closed.
- Changed managed hook definition: safe managed update plus renewed `/hooks` review guidance;
  never persist a trust claim.
- Clean secondary worktree: strict verification and closeout dry-run pass without copying or
  synthesizing generated reports.
- `/tmp/blog-task42`: strict verification has zero required failures under the Task 254 runtime,
  while all Task 42 Git-visible bytes and dirty-state records remain unchanged.

## Delivery and rollback

The live and packaged installer copies and schema copies must remain byte-identical. Rollback is a
single reviewed revert of Task 254; no ignored report migration or target-repository repair is
required.
