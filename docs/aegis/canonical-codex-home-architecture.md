# Canonical Codex Home Architecture

Status: **Accepted for planning and diagnostics**

Decision owner: repository owner

Implemented by: Task 256 diagnostics and migration planner

Host cutover: **deferred to Task 257**

## Decision

The supported steady state is:

- one official Codex executable identity;
- one canonical `CODEX_HOME`;
- one canonical `CODEX_SQLITE_HOME`, normally the same canonical directory;
- one native Codex Remote Control app server owned by that home;
- one session and thread inventory;
- project-local `.codex/config.toml`, `.codex/hooks.json`, rules, and agent configuration
  loaded through native trusted-project behavior;
- one client-local exact-definition hook trust store reviewed through `/hooks`; and
- native `codex remote-control start|stop|pair` lifecycle commands executed in an explicit,
  diagnosed context.

For the currently observed host, Task 257 should prefer the existing attended home,
`/home/loucmane/.codex`, as the canonical destination because it already owns the ordinary
configuration, authentication context, and primary session history. That path is a migration-plan
input, not a Task 256 mutation. Task 257 must revalidate it before cutover.

The separate Aegis Remote Control home introduced before Task 256 remains a transitional source
until Task 257 safely drains and reconciles it. The Task 255 trust bridge is retained during the
transition, but a permanent dual-home topology selected by a CWD-sensitive wrapper is explicitly
rejected.

## Why this decision exists

The dual-home design solved one narrow problem: it allowed an autonomous Remote Control context to
receive explicit project trust without copying all trust from the ordinary Codex home. It also
created a wider state-partition problem:

- sessions in one home are absent from the other home;
- config and project trust can be current in one context and stale in another;
- hook hash review remains local to each client trust store;
- different app servers and client versions can remain live simultaneously;
- lifecycle commands can target the wrong server when routing is inferred from CWD;
- resume and fork selectors cannot truthfully bridge independent session stores; and
- an already running thread can retain a pre-change configuration snapshot even when the trusted
  entry is now correct on disk.

A wrapper can conceal some of those differences, but it cannot turn two independent state roots
into one coherent state machine. Adding attach, resume, import, and lifecycle routing around the
split would deepen the accidental architecture.

## Official Codex facts

Task 256 treats the following as product facts, not Aegis inventions:

| Fact | Consequence | Official source |
|---|---|---|
| `CODEX_HOME` owns Codex config, auth, logs, sessions, skills, and standalone package metadata. | Different homes are different persistent client contexts. | [Environment variables](https://learn.chatgpt.com/docs/config-file/env-vars) |
| `CODEX_SQLITE_HOME` owns SQLite-backed CLI and app-server state; the config `sqlite_home` value has higher precedence. | SQLite ownership must be diagnosed separately and then converged explicitly. | [Environment variables](https://learn.chatgpt.com/docs/config-file/env-vars) |
| Project `.codex/` config and hooks load only for trusted projects. | On-disk trust is a prerequisite, not proof that a running thread loaded the layer. | [Configuration basics](https://learn.chatgpt.com/docs/config-file/config-basic) |
| Non-managed hooks require review of the exact definition, and changed hashes require review again. | Aegis must never copy or infer hook approval. | [Hooks](https://learn.chatgpt.com/docs/hooks) |
| `/hooks` is the interactive surface for inspecting and trusting hook definitions. | Exact-hash review remains an attended boundary. | [Hooks](https://learn.chatgpt.com/docs/hooks) |
| `codex remote-control start` starts the native daemon and `stop` stops it. | Lifecycle actions belong to the native owner context, not to a CWD guess. | [Developer commands](https://learn.chatgpt.com/docs/developer-commands) |
| `--remote` attaches supported Codex commands to a specified app-server endpoint. | Attach and lifecycle management are distinct operations. | [CLI reference](https://learn.chatgpt.com/docs/cli/reference) |
| Codex builds its instruction chain when a run starts. | Startup-derived context must not be assumed to retrofit an existing run. | [AGENTS.md guidance](https://learn.chatgpt.com/docs/codex/agents-md) |

The product documentation does not give Aegis authority to claim that a particular live thread
loaded a particular project config generation. That remains an evidence question.

## Aegis conclusions

The following are Aegis design conclusions derived from the official ownership boundaries and the
observed dogfood failure:

1. Distinct `CODEX_HOME` paths are distinct state authorities even when files happen to look
   similar.
2. Copying auth, sessions, configuration, trust records, hook hashes, or SQLite files between live
   homes is not a safe synchronization protocol.
3. A CWD-routed wrapper is not a reliable lifecycle authority when multiple app servers exist.
4. A session picker must be scoped to its owning home. Cross-home absence is not a missing-session
   error; it is a topology fact.
5. A stale trust warning can coexist with valid on-disk trust when the current thread predates a
   reliable trust-change event.
6. A fresh thread started after trust is necessary for fresh configuration, but it does not prove
   that hooks executed or that `/hooks` approval exists.
7. Unknown active work, unknown server ownership, or ambiguous session ownership blocks cutover.

## Target ownership model

| Surface | Canonical owner after Task 257 | Trust boundary |
|---|---|---|
| Config, profiles, skills, packages, logs | one canonical `CODEX_HOME` | operator-owned |
| Authentication | the same canonical home or its configured OS credential store | never copied by Aegis |
| Sessions and thread metadata | the canonical home | preserved through an explicit drain and handoff |
| SQLite-backed state | one canonical `CODEX_SQLITE_HOME` | migrated only while native server state is quiescent |
| Remote Control server | one native app server using the canonical homes | managed by explicit native lifecycle |
| Project configuration | each trusted repository under `.codex/` | repository-owned, trust-gated |
| Hook definitions | project `.codex/hooks.json` | exact tracked definitions |
| Hook approval | canonical client trust store | attended `/hooks`, hash-bound |
| Task and continuity evidence | each project plus Aegis ledger/capsule surfaces | never substituted for Codex client trust |

## Task 256 interfaces

Task 256 adds two read-only commands:

```text
aegis codex topology status
aegis codex topology plan
```

`status` reports bounded metadata with provenance and explicit known, unknown, invalid, or
not-applicable state. It may inspect:

- canonical and candidate home identities;
- selected non-secret config keys;
- canonical SQLite-home resolution;
- session ownership and bounded session metadata;
- executable identities and wrapper-shadowing signals;
- socket and process ownership metadata without contacting or signaling a process;
- project trust and durable trust-effective timestamps when available; and
- split-brain and thread-freshness conclusions.

It does not emit config bodies, auth data, tokens, transcript text, hook trust-store content, or
arbitrary process arguments.

Process absence is safety evidence only when the caller explicitly proves that the procfs view
covers the host. The default scope is `unknown`, and the Task 257 plan fails closed. A sandboxed
or container PID namespace must never be presented as proof that host servers or child work are
absent.

`plan` consumes the same status model and emits a deterministic Task 257 plan. It does not create
a report file, acquire a lock, change a config, contact a server, or run a lifecycle command.

## Evidence states

Every fact that can affect a conclusion must expose:

- a normalized value or `null`;
- `known`, `unknown`, `invalid`, or `not_applicable`;
- its exact bounded source;
- whether it was directly observed; and
- a non-secret detail string.

Absence of evidence never becomes a safe default.

## Split-brain classification

Direct evidence of any of these conditions produces `split_brain`:

- more than one distinct existing home owns sessions or SQLite state;
- live Codex server processes resolve to different homes;
- more than one home exposes an app-server control socket;
- SQLite state files exist under more than one root;
- command candidates resolve to different executables or versions;
- a wrapper selects different homes by execution context;
- a requested thread is owned by a non-canonical home; or
- an active project would receive materially different trusted project configuration across
  simultaneously active contexts.

Malformed or unreadable state is reported as `invalid` or `unknown`. It blocks migration when it
affects safety, but it is not mislabeled as directly observed split brain.

## Stale-thread classification

Aegis may emit exactly:

> Project is trusted on disk; this session predates the trust change and requires a fresh session.

only when:

1. the project currently has valid trust in the thread-owning home;
2. the trust effective time comes from durable authority metadata rather than a generic config
   modification time;
3. the thread ID is owned by exactly one candidate home;
4. the thread start time is parsed from bounded session metadata; and
5. the thread start time is earlier than the trust effective time.

If any premise is absent or ambiguous, the result is `unknown`. If the thread is newer, Aegis may
say it does not predate the trust change; it still must not claim project hooks loaded, executed,
or were trusted.

## Hook boundaries

Task 256 preserves four distinct truths:

1. tracked hook-review guidance;
2. on-disk project trust;
3. visible client hash records; and
4. authoritative exact-definition approval through `/hooks`.

No topology diagnostic promotes one truth into another. Aegis never reads or copies a hook trust
store to make a migration appear complete. Task 257 must stop for attended `/hooks` review after
the canonical fresh session displays the definitions, then require another fresh SessionStart
before claiming hook execution.

## Task boundaries

Task 256 may:

- read bounded non-secret metadata;
- produce JSON on stdout;
- create source code, tests, ADRs, and ordinary Task 256 workflow evidence in the isolated task
  checkout; and
- describe exact Task 257 mutations and rollback.

Task 256 must not:

- write either live Codex home;
- start, stop, restart, contact, signal, or kill an app server or child process;
- edit shell startup files, PATH, the host wrapper, or symlinks;
- touch the Blog checkout;
- copy sessions, SQLite state, auth, connectors, project trust, hook hashes, or credentials;
- approve or bypass hooks;
- retire the wrapper or Task 255 bridge;
- perform any host cutover; or
- begin Taskmaster-to-Gas-Town migration.

## Alternatives rejected

### Keep two homes and improve the wrapper

Rejected as a steady state. Better routing cannot unify session, SQLite, config-generation, and
hook-trust ownership.

### Symlink the homes

Rejected. Symlinks collapse security contexts without providing an atomic migration, rollback
boundary, or coherent live-server ownership model.

### Copy only sessions or SQLite files

Rejected while either context may be live. File copying is not a supported transaction protocol
for active client state and can produce duplicate or divergent ownership.

### Automatically trust project hooks

Rejected. Exact-definition review is a client security boundary, not repository metadata.

### Restart every server to force reload

Rejected. Project configuration freshness is a session concern; a shared-server restart can
interrupt unrelated active work and does not authorize hook trust.

## Consequences

Positive:

- one project has one predictable Codex context;
- resume and fork use one session inventory;
- native lifecycle commands target one owner;
- project-local configuration no longer depends on wrapper-selected home;
- exact hook approval occurs in one trust store; and
- stale-thread diagnosis can be specific without lying about on-disk trust.

Costs:

- Task 257 requires an attended drain and exact preservation inventory;
- cross-home sessions need explicit preserve, handoff, archive, or retire dispositions;
- the wrapper and bridge cannot be removed until post-cutover verification passes; and
- rollback must preserve both original homes until an observation window closes.

## Rollback

Task 256 itself is reverted by removing the topology module, CLI subcommands, tests, and these
documents. It changes no host topology.

Task 257 rollback must restore the exact pre-cutover wrapper and shell routing, restart only the
previously owned server through its proven native context, and retain both original homes. It must
never reconstruct state from synthesized reports or copied hook trust.

## Task 257 entry criteria

Task 257 may begin only after Task 256 is merged and all of these are true:

- the canonical and candidate homes can be diagnosed without invalid metadata;
- every relevant thread has an explicit ownership and preservation disposition;
- active child work is proven drained, not merely unobserved;
- native server ownership and lifecycle target are proven;
- the process inventory is proven host-complete rather than merely readable;
- one canonical SQLite root is explicitly selected when more than one candidate exists;
- executable identity and version are unambiguous;
- exact byte, mode, owner, and symlink snapshots can be taken without exposing secrets;
- the rollback path is executable before any mutation;
- the owner attends host routing changes and later `/hooks` review; and
- Blog and other projects are at safe checkpoints.
