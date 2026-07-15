# Decisions

- 2026-07-15 — Keep normal Codex and autonomous Remote Control as separate `CODEX_HOME` security contexts; do not symlink either whole config or whole home.
- 2026-07-15 — Require an explicit operator-owned Remote Control allowlist. A project install may diagnose missing trust but may never add itself automatically.
- 2026-07-15 — Project trust only makes project-local config, rules, and hooks eligible to load. Actual hook approval remains Codex-owned, exact-definition-hash-bound client state and is never asserted by Aegis.
- 2026-07-15 — Preserve unowned Remote Control config bytes and tables. Aegis owns only a delimited project-trust block, parses the complete TOML before and after generation, and refuses conflicting unmanaged entries.
- 2026-07-15 — Mutating commands are previews unless `--apply` is explicit. Apply uses a host-local lock, atomic replacement, last-known-good backup, post-write validation, and rollback on failure.
- 2026-07-15 — Do not copy normal-home `[hooks.state]`, connector approvals, sessions, databases, credentials, or arbitrary project settings into Remote Control.
- 2026-07-15 — Represent zero authorizations explicitly as schema-versioned `projects = []`; revocation removes the Aegis projection but does not delete the durable contract or an independently owned Codex entry.
- 2026-07-15 — Require the host allowlist, lock, and backup to be owner-only and refuse symlinked authority/config state. Preserve an existing config's mode rather than silently broadening or narrowing unrelated operator policy.
- 2026-07-15 — Treat `hook_review_required` as a distinct post-trust state. Even a visible matching client record is diagnostic only; Aegis always leaves the authoritative exact-definition decision to `/hooks`.
