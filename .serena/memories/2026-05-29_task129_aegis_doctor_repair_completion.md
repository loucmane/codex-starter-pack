# Task 129 Aegis Doctor/Repair Completion

Task 129 added Aegis doctor, repair, and replay/idempotency hardening.

Key evidence:

- `docs/aegis/state-recovery-model.md` defines the state recovery model and safe repair boundary.
- `scripts/_aegis_installer.py` implements read-only `doctor`, dry-run/apply `repair`, replay-safe start/kickoff, and replay-safe log backfill.
- `aegis_foundation/cli.py`, `scripts/codex-task`, and `aegis_mcp/server.py` expose doctor/repair through package CLI, repo wrapper, and MCP.
- `.claude/scripts/gate_lib.py` and packaged assets classify doctor and repair preview as read-only, while repair apply remains mutating.
- Focused verification passed: 93 tests passed, 1 release-certification smoke skipped.
- Two real Claude live tests were recorded under `docs/ai/work-tracking/active/20260528-task129-aegis-doctor-repair-idempotency-ACTIVE/reports/doctor-repair/`.
- The first live test exposed a `log_work` replay/backfill flaw; the second live test passed end-to-end after the fix without synthetic handlers or direct implementation/changelog edits.

Taskmaster Task 129 is marked done and ready for commit/PR.
