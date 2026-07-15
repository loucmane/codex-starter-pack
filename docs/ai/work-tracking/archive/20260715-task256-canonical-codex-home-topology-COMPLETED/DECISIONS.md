# Decisions

- 2026-07-15 — **Accepted** — The steady state is one official Codex binary, one canonical
  `CODEX_HOME`, one canonical `CODEX_SQLITE_HOME`, one native Remote Control server, one
  session database, and one client-local exact-definition hook trust store. The Task 255
  dual-home bridge remains transitional compatibility only.
- 2026-07-15 — **Accepted** — Task 256 is read-only with respect to host topology. It may
  inspect bounded non-secret metadata and emit a deterministic Task 257 plan, but it may not
  edit either live home, manage a server, signal a process, edit shell routing, touch Blog,
  copy state, approve hooks, retire the wrapper, or perform the cutover.
- 2026-07-15 — **Accepted** — On-disk project trust, tracked hook-review guidance, visible
  client hash records, and actual `/hooks` approval remain distinct. Diagnostics never infer
  actual hook trust.
- 2026-07-15 — **Accepted** — The exact stale-thread diagnosis is emitted only when a valid
  current trust fact has a reliable effective timestamp and a reliably owned thread has an
  earlier start timestamp. Otherwise freshness is `unknown` and the migration planner fails
  closed when that uncertainty affects active work.
- 2026-07-15 — **Accepted** — `/home/loucmane/.codex` is the expected canonical home for
  Task 257 planning because it is the ordinary attended home, but it is not a cutover fact.
  Task 257 must revalidate home, SQLite, session, binary, and server authority before any
  mutation.
- 2026-07-15 — **Accepted** — Process absence is safety evidence only when the caller
  explicitly declares a host-complete process scope and the bounded scan completes without
  truncation. A sandbox-visible empty process list is `unknown`, never proof that no active
  child work exists.
- 2026-07-15 — **Accepted** — Multiple control sockets, session stores, executable
  identities, or SQLite roots are independently reported split-brain indicators. Multiple
  SQLite roots without an explicit authoritative selection are a blocking ambiguity.
- 2026-07-15 — **Accepted** — Task 257 will use a ten-phase drain-first procedure: revalidate,
  immutable snapshot, prove drain, stop through the native owner, consolidate durable state,
  simplify routing, start natively, create a fresh Blog session, review `/hooks`, create a
  second post-approval session, run canaries, and quarantine the old topology for observation.
