# Task 256 Canonical-Home Topology Contract

## Purpose

Task 256 replaces ad hoc dual-home diagnosis with a deterministic, secret-safe view of Codex
state and a no-mutation migration plan. It does not perform the migration.

## Supported CLI

```text
aegis codex topology status
aegis codex topology plan
```

Both commands accept an explicit canonical Codex home, optional additional candidate homes,
optional project paths, optional thread IDs, and an injectable process root for deterministic
tests. Process completeness is a separate explicit input: the default is `unknown`, while
`--process-scope host` is an operator assertion allowed only from a host-complete view. They print
bounded structured JSON and never create reports, locks, caches, backups, or temporary files.

## Evidence Model

Every material fact carries:

- `value`: the normalized value or `null`;
- `state`: `known`, `unknown`, `invalid`, or `not_applicable`;
- `source`: the exact file, environment key, process metadata surface, or derived rule;
- `observed`: whether the source was directly observed;
- `detail`: a bounded non-secret explanation.

The collector may read file metadata, selected non-secret TOML keys, bounded session metadata,
safe executable identity, socket metadata, and sanitized process identity. It must never emit
configuration bodies, auth material, tokens, transcript text, hook trust records, or arbitrary
process arguments.

## Canonical Architecture

- one official Codex executable identity;
- one canonical `CODEX_HOME` for config, auth, logs, sessions, skills, and package metadata;
- one canonical `CODEX_SQLITE_HOME` for SQLite-backed state;
- one native Remote Control app server owned by that home;
- project-local `.codex/` configuration and hooks gated by project trust;
- exact-definition `/hooks` review in the same client trust store;
- no CWD-routed home selection and no cross-home session picker.

Task 255 dual-home bridge commands remain available during Task 256. Their existence is reported
as transitional topology, not silently treated as the target architecture.

## Split-Brain Rules

The status is `split_brain` when directly observed evidence shows any of:

- more than one distinct existing Codex home owns sessions or SQLite state;
- live Codex server processes resolve to more than one home;
- more than one home exposes an app-server control socket;
- SQLite state files exist under more than one root;
- multiple command candidates resolve to different executable identities or versions;
- a wrapper can select different homes by context;
- one requested thread is owned by a non-canonical home;
- project trust differs across active contexts in a way that can change project-local config.

Unknown process ownership, unknown active work, malformed config, ambiguous aliases, unreadable
session metadata, or unresolved home identity do not become `split_brain` facts. They become
explicit blockers in the migration plan.

## Thread Freshness Rules

The exact diagnostic text is:

> Project is trusted on disk; this session predates the trust change and requires a fresh session.

It is emitted only when all are true:

1. the project identity is canonical and currently trusted in the owning home;
2. the trust effective time comes from durable authority metadata, not a generic file mtime;
3. the thread ID is found in exactly one candidate home;
4. the thread start timestamp is parsed from bounded session metadata; and
5. the thread start precedes the trust effective time.

If any premise is missing or ambiguous, freshness is `unknown`. A fresh thread proves only that
it started after trust; it does not prove project hooks loaded or were approved.

## Migration Planner

The planner consumes the status payload and emits deterministic phases for Task 257. It never
runs those phases. The plan is blocked when active work is present or unknown, a server owner is
unknown, process inventory scope is unproven, sessions are cross-home without a preservation
disposition, config is malformed, SQLite authority is ambiguous, the canonical executable is
ambiguous, or rollback snapshots cannot be specified.

Required phases are preflight, inventory freeze, drain, native server stop, canonical state
consolidation, shell and wrapper cutover, one native server start, fresh-session and `/hooks`
review, verification, rollback observation, and deferred legacy-home quarantine. Every phase has
preconditions, attended boundaries, verification, and rollback instructions.

## No-Mutation Oracle

Tests snapshot every fixture file path, byte digest, mode, symlink target, and directory entry
before and after status and plan operations. Equality is required. Process runners, lifecycle
commands, network clients, and write helpers are not dependencies of the topology module.
