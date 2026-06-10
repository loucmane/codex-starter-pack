# 2026-06-10 Task 202 Capsule PR-1a kickoff

Task 202 starts Phase 1 of the Session Zero Capsule program (binding contract:
`docs/aegis/AEGIS_CAPSULE_SPEC.md`, nine-PR slicing in section 1.2).

Session scope (branch `feat/task-202-capsule-ledger-core`):
1. Contract check-in: capsule spec + `AEGIS_VNEXT_PROGRAM.md` pointer/G3-supersession in one commit.
2. Backlog wiring: tasks for PRs 1a-4 with strict build-order dependencies; reconcile 194-201
   (198 superseded by 1a/1b, 196 absorbed by 1b+3.5, 195 TP-label fix, 194 subtask audit).
3. Build PR-1a only: `aegis_foundation/assets/.claude/scripts/ledger_lib.py` (stdlib-only,
   SQLite at XDG state dir keyed on git common dir, WAL+busy_timeout, redaction helpers,
   backend-agnostic reader + JSONL fallback), `docs/aegis/LEDGER_SCHEMA.md`,
   `aegis ledger path` + status surfacing, tests in `tests/claude_adapter/`. No hook
   registration, zero behavior change.

State repaired during bootstrap: stale task-199 envelope (advisory-mode work, merged as
be569cd) archived; TM #199 still needs status reconciliation (its ID was borrowed by the
advisory work; the mode-lattice scope is largely superseded by spec sections 1 and 5.2).
Enforcement was set to advisory by the owner for this program work
(`.aegis/state/enforcement.json`).
