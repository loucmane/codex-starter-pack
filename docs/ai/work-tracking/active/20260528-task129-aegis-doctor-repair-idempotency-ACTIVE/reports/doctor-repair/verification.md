# Task 129 Doctor/Repair Verification

Date: 2026-05-29

## Syntax Checks

- `python3 -m py_compile scripts/_aegis_installer.py aegis_foundation/cli.py aegis_mcp/server.py scripts/codex-task .claude/scripts/gate_lib.py`
- `python3 -m py_compile aegis_foundation/assets/scripts/_aegis_installer.py aegis_foundation/assets/scripts/codex-task aegis_foundation/assets/.claude/scripts/gate_lib.py`
- `git diff --check`

Result: PASS

## Focused Regression Suite

Command:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_mcp_server.py tests/meta_workflow_guard/test_aegis_schemas.py tests/meta_workflow_guard/test_aegis_installer.py
```

Result:

```text
93 passed, 1 skipped in 8.48s
```

The skipped test is the existing release-certification smoke test that requires `AEGIS_RUN_CERTIFICATION_SMOKE=1`.

## Covered Behavior

- `doctor()` reports installed projects with no active work as `installed_no_current_work` without writing repair reports.
- `repair()` preview is read-only and does not restore files or write `.aegis/reports/repair-report.json`.
- `repair(apply=True)` restores a missing project-local `.aegis/bin/aegis` shim, preserves executable permissions, and writes a repair report.
- MCP `aegis.doctor` and dry-run `aegis.repair` preserve read-only tool response semantics.
- MCP `aegis.repair apply=true` is a mutating tool response and writes the repair report.
- Claude hook classification treats `mcp__aegis__aegis_doctor` and dry-run `mcp__aegis__aegis_repair` as read-only and does not create pending tracking.
- Replaying `start_local_work()` for the same in-progress local task returns `already_started` without allocating another local task id, branch, session, plan, or active folder.
- Replaying the same `log_work()` S:W:H:E event returns `already_logged` and does not duplicate session or tracker entries.
- Replaying the same `log_work()` S:W:H:E event with additional requested surfaces backfills only the missing surfaces without duplicating session/tracker entries.
- Repair apply recreates missing `sessions/current` and `plans/current` symlinks from current-work state while leaving unrelated stale ACTIVE folders untouched.
- Repair apply is blocked while pending S:W:H:E tracking exists and does not write a repair report.

## Live Claude Validation

- `claude-live-test-1.md` captured the first real Claude run. It passed functionally and exposed the `log_work` replay/backfill flaw.
- `claude-live-test-2.md` captured the second real Claude run after the fix. Fresh-project MCP install/start/edit/verify/handoff/closeout/doctor completed without synthetic handler names or direct edits to `IMPLEMENTATION.md` / `CHANGELOG.md`.
