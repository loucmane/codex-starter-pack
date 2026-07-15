# Codex Remote Control Trust Contract

## Problem

Codex resolves project trust from the `config.toml` under the effective `CODEX_HOME`. The normal user home and Aegis Remote Control home are intentionally separate, but the current bridge has no durable way to record which projects the autonomous context may load. A project can therefore be trusted interactively and still have its local `.codex/config.toml`, hooks, and exec policies disabled when attached through Remote Control.

## Security boundary

Four states must remain distinct:

1. Normal-user Codex project trust.
2. Autonomous Remote Control project trust.
3. Tracked Aegis guidance requiring `.codex/hooks.json`, `/hooks`, exact-definition hashing, and no bypass.
4. Actual Codex client-local hook approval for exact current hook-definition hashes.

Aegis may manage state 2 and verify the tracked guidance in state 3. It must never infer or claim state 4, copy state 4 between homes, or allow a project install to grant state 2 to itself.

## Host state

The Remote Control home owns:

- `trusted-projects.toml`: explicit operator approvals with canonical path, actor, timestamp, and reason.
- `config.toml`: active Codex configuration containing one delimited Aegis-managed trust block.
- `.aegis-project-trust.lock`: host-local mutation lock.
- `config.toml.aegis-last-known-good`: exact pre-apply backup for deterministic rollback.

All files are user-local and mode `0600`. They are never installed into or tracked by a governed project.

## CLI

```text
aegis codex bridge status [--project PATH]
aegis codex bridge plan
aegis codex bridge apply
aegis codex trust status --project PATH
aegis codex trust add --project PATH --reason TEXT [--approved-by USER] [--apply]
aegis codex trust remove --project PATH --reason TEXT [--apply]
```

Every command accepts explicit normal and Remote Control home overrides for isolated tests and non-default installations. Status and plan are read-only. Trust add/remove are previews unless `--apply` is supplied.

## Allowlist validation

- Require schema version 1 and an exact supported field set.
- Require existing absolute directories for additions.
- Canonicalize with strict `resolve()` and store the canonical path.
- Reject duplicate canonical identities, including symlink aliases.
- Require non-empty actor, timestamp, and reason.
- Permit removal of a now-missing stored path by its exact lexical value.
- Refuse malformed TOML, unknown keys, unsupported versions, invalid timestamps, and non-table entries.

## Config projection

1. Acquire the Remote Control lock with a bounded timeout.
2. Read and parse the complete active config.
3. Locate at most one exact Aegis begin/end marker pair; malformed or duplicate markers fail closed.
4. Remove the old managed block in memory, preserving every other byte.
5. Parse the unmanaged base and inspect its `[projects]` table.
6. Treat an identical unmanaged trusted entry as externally satisfied and leave it untouched.
7. Refuse unmanaged untrusted or malformed entries, and canonical path aliases that conflict with an allowlisted project.
8. Render only missing allowlisted entries in deterministic canonical-path order inside the managed block.
9. Parse the complete proposed config and prove every effective allowlisted project is exactly `trust_level = "trusted"`.
10. Report bounded hashes, inventory, conflicts, and a unified diff during preview.

## Apply and rollback

Apply repeats planning under the exclusive lock. If no semantic or byte delta exists, it returns idempotently without touching timestamps or backups. Otherwise it:

1. Atomically snapshots the current config to the last-known-good path.
2. Atomically replaces the active config while retaining its file mode.
3. Re-reads, parses, and validates the bytes from disk.
4. Restores the exact backup atomically on any write or post-write validation failure.
5. Reports a terminal rollback failure without hiding either file if restoration itself fails.

Trust add/remove updates the allowlist and config as one lock-scoped transaction. If config application fails, the prior allowlist and active config are both restored.

## Diagnostics

Project status reports separately:

- canonical project identity;
- normal-home configured trust;
- Remote Control allowlist membership;
- Remote Control effective configured trust;
- whether project-local Codex files are eligible to load;
- tracked Aegis hook-review guidance validity;
- count and presence of Remote Control client-local hook hash records;
- `client_trust_asserted: false` unconditionally;
- the exact reconnect and `/hooks` review guidance.

The report must explain a mismatched `CODEX_HOME` instead of pointing only at the normal config.

## Acceptance matrix

- Preview is side-effect free.
- Add, apply, status, and remove lifecycle is deterministic and idempotent.
- Existing unrelated config bytes, permissions, hook hashes, and connector tables survive exactly.
- Normal-home trust and hook state are never copied.
- Missing, malformed, and duplicate allowlists fail closed.
- Existing untrusted entries and canonical aliases fail closed.
- Concurrent writers serialize or time out without corruption.
- Injected post-write failure restores both config and allowlist.
- Changed project hook definitions never update client hash records and always direct the operator to `/hooks`.
- Root and packaged documentation remain identical.
- Full source tests, guard, plan-sync, closeout, witness, and hosted CI pass.
