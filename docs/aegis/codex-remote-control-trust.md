# Codex Remote Control project trust

Aegis keeps attended Codex and autonomous Remote Control as separate security contexts. A
project trusted in an ordinary Codex session is therefore not automatically trusted by a
Remote Control daemon whose effective `CODEX_HOME` is different.

This subsystem manages one explicit, host-scoped project allowlist and projects only those
authorizations into an Aegis-delimited section of the active Remote Control
`config.toml`. It never copies hook hashes, connector approvals, sessions, credentials,
model settings, or unrelated project trust from another Codex home.

## Four states that must not be conflated

| State | Durable source | What it proves |
|---|---|---|
| Attended Codex project trust | The normal Codex home's `config.toml` | Project-local config may load in that attended context. |
| Remote Control project authorization | `trusted-projects.toml` in the Remote Control home | An operator explicitly authorized Aegis to project that canonical project path into the autonomous config. |
| Tracked Aegis hook-review guidance | The project's managed `codex.hook_trust` manifest gate | The project declares `.codex/hooks.json`, `/hooks`, exact-definition hashing, and no bypass as the required review contract. |
| Actual hook trust | Codex client/session-local, exact-hash state | The operator reviewed and approved the exact definitions currently shown by `/hooks`. |

Tracked guidance is not client trust. A project authorization is not hook trust. Aegis
reports these states separately and never claims that project hooks are trusted.

## Host state

The effective Remote Control `CODEX_HOME` owns:

- `trusted-projects.toml`: schema-versioned explicit authorizations;
- `config.toml`: the active Codex configuration;
- `.aegis-project-trust.lock`: the bounded inter-process mutation lock;
- `config.toml.aegis-last-known-good`: the exact config bytes from before the latest
  changed projection.

The allowlist, lock, backup, and newly written config files use owner-only permissions
unless an existing config has a more specific mode, in which case its mode is preserved.
Aegis refuses symlinked host-state files and resolves project paths to canonical absolute
directory identities.

Aegis owns only this delimited config block:

```toml
# AEGIS:BEGIN codex-remote-control-project-trust v1
[projects."/absolute/canonical/project"]
trust_level = "trusted"

# AEGIS:END codex-remote-control-project-trust v1
```

All bytes outside that block remain operator- or Codex-owned. An existing exact unmanaged
`trusted` entry satisfies an authorization without being adopted. An unmanaged
non-trusted entry or canonical-path alias is a conflict and fails closed.

## Discover the active contexts

```bash
aegis codex bridge status --project /absolute/project
aegis codex trust status --project /absolute/project
```

The status output shows the active `CODEX_HOME`, the normal and Remote Control homes,
normal project trust, the explicit allowlist, effective Remote project trust, tracked hook
guidance, the current hook-definition digest, and any client hash records that are visible.
Even when records are visible, `client_trust_asserted` remains false: use `/hooks` for the
authoritative review.

Home discovery uses explicit CLI arguments first, then
`AEGIS_REMOTE_CONTROL_HOME`/`CODEX_GLOBAL_DIR`, then the active context or Aegis source
bridge. If discovery is ambiguous, pass both homes explicitly:

```bash
aegis codex bridge status \
  --normal-codex-home /home/operator/.codex \
  --remote-codex-home /srv/aegis/.codex/remote-control \
  --project /srv/projects/example
```

## Explicit authorization lifecycle

Adding or removing trust is preview-only unless `--apply` is present.

```bash
aegis codex trust add \
  --project /absolute/project \
  --reason "owner approved autonomous work in this repository"

aegis codex trust add \
  --project /absolute/project \
  --reason "owner approved autonomous work in this repository" \
  --apply
```

A successful add stores the canonical path, operator identity, UTC approval timestamp, and
reason. It then updates the allowlist and managed config projection in one locked
transaction. Repeating the same authorization is idempotent and does not rewrite files or
replace its original authority metadata.

To revoke access:

```bash
aegis codex trust remove \
  --project /absolute/project \
  --reason "autonomous engagement complete"

aegis codex trust remove \
  --project /absolute/project \
  --reason "autonomous engagement complete" \
  --apply
```

The first command previews. The second removes only the explicit authorization and its
Aegis-owned projection. It does not rewrite an independently owned Codex project entry.

For an already edited allowlist, use:

```bash
aegis codex bridge plan
aegis codex bridge apply
```

Direct editing is discouraged because the CLI canonicalizes paths and records complete
authority metadata. `bridge apply` validates but does not invent or broaden authority.

## Transaction and rollback behavior

Every mutating operation:

1. takes the host-scoped lock with a bounded timeout;
2. re-reads and validates current state after acquiring the lock;
3. validates the full current TOML and managed-marker structure;
4. builds and parses the complete proposed config;
5. writes temporary files with restrictive modes and fsyncs them;
6. atomically replaces the destination;
7. re-reads and validates the durable allowlist and complete config.

Before a changed config projection, Aegis writes the exact old config to
`config.toml.aegis-last-known-good`. If post-write validation fails, it restores both the
allowlist and config snapshots. An incomplete rollback is a terminal error and reports the
backup path; do not continue the daemon until the host state is inspected.

No command creates trust from the normal Codex config. No command follows symlinked config
or allowlist files. Malformed TOML, duplicate paths, canonical aliases, duplicate managed
markers, missing projects, and weakened hook guidance all remain visible failures.

## Why the Codex homes are not symlinked

The attended and autonomous contexts intentionally differ in approvals, permissions,
connectors, sessions, credentials, and hook decisions. Symlinking the complete
`config.toml` or `CODEX_HOME` would collapse those boundaries, leak unrelated trust, and
make a change intended for one context silently affect the other. Aegis instead projects
the minimum explicit project-trust fact into a bounded managed block.

Individual project hook files also are not copied into host config. Their exact definitions
remain in the repository, and their approval remains local to the active Codex client and
hash.

## Safe project rollout

After the upstream Aegis implementation is merged:

1. inspect the target repository and reach a safe workflow checkpoint;
2. preview and apply its supported Aegis runtime update;
3. run strict Aegis verification;
4. from the host context, preview then apply `aegis codex trust add` for the canonical
   project path;
5. reconnect the Remote Control project session so project-local `.codex/` config can
   load;
6. open `/hooks`, review every exact definition and hash, and approve them explicitly.

Stop before step 6 when the owner has not attended the hash review. Never bypass hook trust,
copy stale hash state, synthesize approval evidence, or infer authorization merely because
the repository is globally trusted elsewhere.
