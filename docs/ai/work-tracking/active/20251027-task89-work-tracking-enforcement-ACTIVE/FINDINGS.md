# Findings

- 2025-10-27 — Documented enforcement coverage scenarios for guard updates.
- 2025-10-27 — Guard confirms archived folders bypass deletion warning when completed tracker present.
- 2025-11-25 — Resumed verification using restored ACTIVE folder; guard now requires fresh tracker/findings/decisions entries plus evidence paths before passing on multi-day work.
- 2025-11-25 — Updated folder-name guard to check tracked state before enforcing YYYYMMDD prefixes so reusing older ACTIVE folders for evidence logging no longer fails validation.
- 2026-04-20 — Codex runtime config had drifted from the documented workflow: `.codex/config.toml` no longer declared MCP servers even though templates and handoffs still expected Serena and Taskmaster.
- 2026-04-20 — The old config backup contained useful MCP intent but was not safe to restore wholesale because it mixed legacy command names, old home-directory overrides, optional stale MCPs, and embedded third-party secrets.
- 2026-04-20 — Taskmaster parent tasks 83 and 86 had drifted from their subtasks: all subtasks were done, but the parents remained `in-progress`.
- 2026-04-20 — Parallel `task-master set-status` calls can race on `.taskmaster/tasks/tasks.json`; Task 86 had to be rerun sequentially before the done state persisted.

## Progress Log
- **2025-11-25 11:52** — [S:20251125|W:task89-work-tracking|H:docs/findings|E:docs/ai/work-tracking/active/20251027-task89-work-tracking-enforcement-ACTIVE/FINDINGS.md] Logged multi-day verification requirement + guard evidence expectations
- **2026-04-20 13:44** — [S:20260420|W:task89-work-tracking|H:docs/findings|E:docs/ai/work-tracking/active/20251027-task89-work-tracking-enforcement-ACTIVE/FINDINGS.md] Documented MCP/config drift and why the old backup should not be restored wholesale
- **2026-04-20 14:16** — [S:20260420|W:task89-work-tracking|H:docs/findings|E:docs/ai/work-tracking/active/20251027-task89-work-tracking-enforcement-ACTIVE/FINDINGS.md] Logged Taskmaster parent-status drift and parallel write race behavior
