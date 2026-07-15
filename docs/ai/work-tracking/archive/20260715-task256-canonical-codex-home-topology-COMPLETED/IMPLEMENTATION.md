# Task 256 Canonical Codex Home Topology Diagnostics and Migration Plan – Implementation Notes

## Delivered Workstreams

### Architecture and contract

- `docs/aegis/canonical-codex-home-architecture.md` separates official Codex behavior from
  Aegis policy and binds the one-binary, one-home, one-SQLite-root, one-server, one-session-
  inventory, native-project-config steady state.
- The packaged documentation mirror is byte-identical.
- The design contract freezes evidence provenance, redaction, uncertainty, stale-thread,
  split-brain, planner, and no-mutation requirements.

### Read-only topology runtime

- `aegis_foundation/codex_topology.py` collects bounded metadata for candidate homes,
  effective SQLite roots, session ownership, server sockets, executable/version identity,
  selected non-secret configuration, wrapper routing signals, tracked hook guidance,
  project trust, and caller-declared process scope.
- It never emits auth material, transcript content, hook trust-store contents, arbitrary
  process arguments, or wrapper source.
- It distinguishes durable guidance and visible hash records from authoritative client
  `/hooks` approval and always leaves actual approval unasserted.
- Unknown, truncated, malformed, duplicated, or ambiguously owned evidence fails closed.

### CLI and schemas

- `aegis codex topology status` emits a strict, schema-validated, secret-safe inventory.
- `aegis codex topology plan` emits a deterministic ten-phase Task 257 plan and never
  executes it.
- Tracked and packaged Draft 2020-12 schemas are byte-identical and reject weakened hook
  trust, mutable Task 256 plans, malformed blockers, and inconsistent readiness states.

### Task 257 cutover plan

- The exact plan records expected and observed paths, commands, prerequisites, active-work
  proof, snapshot inventory, native lifecycle ownership, durable-state preservation,
  routing simplification, fresh-session requirements, attended `/hooks` review, canaries,
  rollback triggers, quarantine, and an observation window.
- It explicitly forbids copying auth, sessions, live SQLite databases, trust stores, or hook
  hashes and forbids killing shared servers or mutating Blog during Task 256.

## Verification

- Focused topology and schema suite: 50 passed.
- Adjacent Codex Remote trust suite: 42 passed.
- Release distribution suite: 14 passed, 2 environment-gated skips.
- Output-budget suite: 17 passed.
- Runnable full suite: 2,130 passed, 4 opt-in smoke skips in 64.26 seconds after precisely
  deselecting four independently reproduced baseline/environment constraints.
- The slow sacrificial Taskmaster precision-corpus test passed independently in 34.26
  seconds.
- Ruff, module-level mypy, Python compile, source/package `cmp`, schema validation, and
  `git diff --check` passed. Black reported both new Task 256 Python files unchanged before
  its sandboxed worker shutdown timed out; modified legacy files retain pre-existing
  non-Black-clean formatting to avoid unrelated churn.
- Whole-program mypy is not a repository CI gate and reports existing legacy errors outside
  Task 256; no type errors were introduced in `codex_topology.py`.

## Preserved State

No live Codex home, SQLite database, socket, process, shell file, wrapper, Blog checkout,
session store, credential, trust record, hook hash, or Gas Town migration surface was
modified. The implementation occurred in `/tmp/codex-task256-clone` because the canonical
checkout's `.git` directory is sandbox read-only.
