# Task 129 Aegis Doctor, Repair, and Idempotency Hardening – Implementation Notes

## Planned Workstreams
- Completed state recovery model documentation in `docs/aegis/state-recovery-model.md` and packaged docs under `aegis_foundation/assets/docs/aegis/`.
- Added `doctor()` to `scripts/_aegis_installer.py` as a read-only diagnostic surface that reports current Aegis state, strict checks, summary counts, next action, and a safe repair plan.
- Added `repair()` to `scripts/_aegis_installer.py` with dry-run preview by default and explicit `apply=True` behavior for safe mechanical repairs only.
- Safe repairs currently cover missing manifest-managed assets, non-executable local CLI shim, missing active reports directory, broken `sessions/current` / `plans/current` symlinks, and completed-closeout current-work normalization.
- Added concise CLI commands in `aegis_foundation/cli.py` and `scripts/codex-task`: `aegis doctor` and `aegis repair [--apply]`.
- Added MCP tools in `aegis_mcp/server.py`: `aegis.doctor` is read-only and `aegis.repair` is read-only unless `apply=true`.
- Updated Claude hook classifier in `.claude/scripts/gate_lib.py` and packaged assets so MCP `aegis.doctor` / dry-run `aegis.repair` do not create pending tracking, while `aegis repair --apply` and MCP `aegis.repair apply=true` remain mutation surfaces.
- Synced runtime changes into `aegis_foundation/assets/scripts/` and `aegis_foundation/assets/.claude/scripts/` so future MCP installs receive the same behavior.
- Hardened replay behavior: repeated `start_local_work()` / `kickoff()` for the same in-progress work returns `already_started`, different in-progress work is refused, and repeated `log_work()` for an already-recorded S:W:H:E token returns `already_logged` without duplicating session/tracker entries.
- Hardened repair safety: repair apply recreates current symlinks from current-work state, preserves stale ACTIVE folders for manual lifecycle handling, and refuses to mutate while pending tracking exists.
- Live Claude validation exposed that `log_work` replay also needs to backfill missing requested surfaces. Updated the replay path so already-recorded S:W:H:E tokens do not duplicate session/tracker entries but can still write missing implementation/changelog/handoff/findings/decisions surfaces and missing plan evidence.

## Evidence
- [S:20260528|W:task129-aegis-doctor-repair-idempotency|H:codex:implementation|E:scripts/_aegis_installer.py] Implemented doctor/repair core and report formatting.
- [S:20260528|W:task129-aegis-doctor-repair-idempotency|H:codex:implementation|E:aegis_mcp/server.py] Exposed doctor/repair over MCP with read-only/apply semantics.
- [S:20260528|W:task129-aegis-doctor-repair-idempotency|H:codex:implementation|E:.claude/scripts/gate_lib.py] Updated gate classification for doctor and repair.
- [S:20260528|W:task129-aegis-doctor-repair-idempotency|H:codex:implementation|E:tests/meta_workflow_guard/test_aegis_installer.py] Added installer and hook-classifier regression tests.
- [S:20260528|W:task129-aegis-doctor-repair-idempotency|H:codex:implementation|E:tests/meta_workflow_guard/test_aegis_mcp_server.py] Added MCP tool registration and repair-preview regression tests.
- [S:20260528|W:task129-aegis-doctor-repair-idempotency|H:claude-live-test|E:docs/ai/work-tracking/active/20260528-task129-aegis-doctor-repair-idempotency-ACTIVE/reports/doctor-repair/claude-live-test-1.md] Captured the first real Claude test and the live-test-driven log replay fix.
- [S:20260529|W:task129-aegis-doctor-repair-idempotency|H:claude-live-test|E:docs/ai/work-tracking/active/20260528-task129-aegis-doctor-repair-idempotency-ACTIVE/reports/doctor-repair/claude-live-test-2.md] Captured the second real Claude test after the fix: fresh MCP install, local start, native source edit, verification, handoff repair, closeout, and doctor completed without synthetic handler workarounds or direct implementation/changelog edits.
