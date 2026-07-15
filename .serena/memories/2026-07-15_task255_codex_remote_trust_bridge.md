# Task 255 — Codex Remote Control trust bridge

Date: 2026-07-15
Branch: `feat/task-255-codex-remote-trust-bridge`
Worktree: `/tmp/codex-task255`
Taskmaster: Task 255 is `done`
Evidence: `docs/ai/work-tracking/archive/20260715-task255-codex-remote-trust-bridge-COMPLETED/`

## Objective and result

Implemented host-scoped, explicit Codex Remote Control project-trust management without
symlinking security contexts, inheriting global trust, copying hook hashes, or claiming
client-local `/hooks` approval. Source implementation and closeout are complete; hosted
delivery remains.

## Implemented

- `aegis_foundation/codex_remote_trust.py` owns schema-versioned host authorization,
  canonical project identities, an Aegis-delimited config projection, restrictive authority
  modes, bounded locking, atomic replacement, last-known-good backup, verified rollback,
  and normal-versus-Remote trust diagnostics.
- `aegis_foundation/cli.py` exposes `aegis codex bridge status|plan|apply` and
  `aegis codex trust status|add|remove`; mutations preview unless `--apply` is explicit.
- `docs/aegis/codex-remote-control-trust.md` and its packaged mirror document normal
  project trust, Remote authorization, tracked hook guidance, and actual client-local
  exact-hash trust as four distinct states.
- `tests/meta_workflow_guard/test_codex_remote_trust.py` covers malformed input, aliases,
  symlinks, modes, concurrency, lock timeout, idempotence, preservation, rollback, CLI,
  and hook-hash renewal.

## Verified

- Task 255 focused tests: 42 passed.
- Adjacent Codex adapter/bootstrap/schema tests: 37 passed.
- Distribution tests: 14 passed; default opt-in smokes skipped.
- Installer tests: 153 passed; default opt-in certification smoke skipped.
- Explicit installed-wheel CLI smoke: 1 passed.
- Full repository suite: 2,100 passed and four documented opt-in smokes skipped. One
  pre-existing test exposed a temporary-root assumption because the entire source worktree
  is under `/tmp`; the exact test passed with a non-overlapping `TMPDIR`.
- Ruff, mypy, new-file Black, Taskmaster health, plan sync, work-tracking audit, source
  guard, and diff checks pass.
- Live read-only diagnosis confirms normal Codex trusts Blog while the separate Remote
  Control home does not. Blog and both host homes remain unmodified; `/hooks` review remains
  required.
- Supported source closeout marked Task 255 done and archived all evidence. Post-archive
  readiness returns `READY | task=255`; Taskmaster has 254 tasks, 386 subtasks, 443 valid
  dependency references, and no invalid references.

## Continue with

1. Review the final Task 255 diff, create the signed commit, push, and open the draft PR.
2. Run hosted CI/witness/secret checks and follow evidence-governed merge policy.
3. Synchronize main without touching unrelated primary-checkout drift.
4. Only after upstream merge, prepare the attended Blog rollout. Do not mutate Blog from the
   upstream task session and stop before exact-hash `/hooks` approval.

The primary `/home/loucmane/codex` checkout contains unrelated local `.codex`, `.agents`,
and runtime drift; preserve it. Do not begin the Taskmaster-to-Gas-Town migration.