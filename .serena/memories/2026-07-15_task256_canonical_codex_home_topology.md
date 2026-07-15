# Task 256 — Canonical Codex Home Topology Diagnostics and Migration Plan

## Scope

Task 256 is plan-first and read-only with respect to host topology. It must not edit either live Codex home, start/stop/signal a server, edit shell routing or the wrapper, touch Blog, copy auth/sessions/SQLite/trust/hook hashes, approve hooks, execute the cutover, or start Taskmaster-to-Gas-Town migration.

## Binding architecture

The steady state is one official Codex binary, one canonical CODEX_HOME, one canonical CODEX_SQLITE_HOME, one native Remote Control server, one session inventory, native project trust/config/hooks, and one client-local exact-definition /hooks trust store. The Task 255 bridge is transitional. `/home/loucmane/.codex` is the expected Task 257 canonical home, but Task 257 must revalidate authority before mutation.

## Delivered

- `aegis_foundation/codex_topology.py`: bounded, read-only, secret-safe topology status and deterministic no-mutation planning.
- `aegis_foundation/cli.py`: `aegis codex topology status|plan`.
- Strict tracked and packaged status/plan schemas.
- Byte-identical packaged docs/schemas.
- Binding ADR: `docs/aegis/canonical-codex-home-architecture.md`.
- Exact ten-phase drain-first Task 257 plan: `docs/aegis/task257-canonical-codex-home-cutover-plan.md`.
- Focused topology and schema tests.

Diagnostics separate durable trust, tracked review guidance, visible hash records, and authoritative `/hooks` approval. They never assert client trust. Unknown/truncated process or session scope fails closed. Multiple sockets, session stores, executables, or SQLite roots are split-brain signals.

## Dogfood

The sandbox-visible host view reports separate normal and Remote Control session stores, two control sockets, multiple executable identities, and two SQLite roots under the normal home. Process scope is not host-complete, so active-work safety remains unknown. SQLite authority is ambiguous and blocks Task 257. Wrapper diagnostics emit classified routing signals and a digest, never wrapper source.

## Verification

- Focused topology/schema: 50 passed.
- Adjacent Remote trust: 42 passed.
- Release distribution: 14 passed, 2 opt-in skips.
- Output budget: 17 passed.
- Runnable full suite: 2,130 passed, 4 opt-in skips.
- Slow precision corpus: passed independently in 34.26s.
- Ruff, codex_topology mypy, compile, parity, schema, guard, and diff checks passed.
- Black reported both new Python files unchanged before sandboxed worker shutdown timed out. Modified legacy files preserve independently confirmed pre-existing non-Black-clean formatting.
- Two editable-install tests fail identically on untouched main because package downloads are blocked.
- One stdio MCP test times out identically on untouched main.
- One target-location test fails only because the isolated clone is under `/tmp`; it passes in the canonical `/home` checkout.

## State and continuation

Taskmaster Task 256 is done and the complete tracking bundle is archived. Readiness, Taskmaster health, plan sync, S:W:H:E guard, and diff checks pass; the audit has only the expected no-ACTIVE-folder warning between tasks. Stage only Task 256 (including the force-added ignored verification report), commit, push, and open an attended exact-head PR. Do not merge automatically. Task 257 starts only after owner review/merge and must follow its cutover document with attended boundaries.
