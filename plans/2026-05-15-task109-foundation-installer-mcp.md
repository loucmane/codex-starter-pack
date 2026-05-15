---
session_id: 2026-05-15-008
work_context: task109-foundation-installer-mcp
handler_target: docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/designs/foundation-installer-mcp-architecture.md
task_ids: [109]
branch_policy: feature-required
evidence_summary:
  - docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/
  - docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/designs/foundation-installer-mcp-architecture.md
  - .taskmaster/tasks/task_109.md
  - docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/DECISIONS.md
plan_version: v1
emergency_bypass: false
---

# Plan - Task 109 Portable Foundation Installer and MCP Distribution Contract

## Header
- **Session ID (S)**: 2026-05-15-008
- **Work Context (W)**: task109-foundation-installer-mcp
- **Handler Target (H)**: docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/designs/foundation-installer-mcp-architecture.md
- **Task IDs**: 109
- **Branch Policy**: feature-required
- **Evidence Summary (E)**: docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/, docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/designs/foundation-installer-mcp-architecture.md, .taskmaster/tasks/task_109.md, docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/DECISIONS.md
- **Plan Version**: v1
- **Emergency Bypass**: false

## Plan Table
| Step ID             | Description | Evidence | Status |
|---------------------|-------------|----------|--------|
| plan-step-scope | Document the portable foundation installer and MCP distribution architecture, including alternatives, chosen direction, manifest/profile model, tool contract, and test strategy | docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/designs/foundation-installer-mcp-architecture.md | completed |
| plan-step-implement | Implement or further specify the manifest/profile schema, generic-profile CLI command surface, fixture/idempotence strategy, and MCP contract from the Option B scope lock | docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/IMPLEMENTATION.md; docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/designs/foundation-installer-mcp-architecture.md | pending |
| plan-step-verify | Store evidence, refresh handoff docs, and confirm Taskmaster status, guard, work-tracking audit, and diff-check | docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/TRACKER.md | pending |
| plan-step-emergency | _Optional_ - only if bypass required | Waiver + post-mortem plan | n/a |

## Scope
- `docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/`
- `docs/ai/work-tracking/active/20260515-task109-foundation-installer-mcp-ACTIVE/designs/foundation-installer-mcp-architecture.md`
- `.taskmaster/tasks/task_109.md`
- `scripts/codex-task`
- `tests/`
- Taskmaster Task `109`

## Branch Policy
- Working branch: `feat/task-109-foundation-installer-mcp`

## Amendments & Versioning
- 2026-05-15 - Task 109 kickoff created via the guided wizard flow.
- 2026-05-15 - Corrected the generic kickoff plan wording to the actual installer/MCP architecture scope and completed plan-step-scope.
- 2026-05-15 - Locked Task 109 to Option B before implementation: architecture + schemas + generic-profile CLI prototype + fixture/idempotence tests + MCP contract.
- 2026-05-15 - Tested Taskmaster Codex CLI routing: parent `update-task` remains too slow for interactive use, `update-subtask` succeeded for 109.2, and Taskmaster stays on `codex-cli`/`gpt-5.2` with medium reasoning.
- 2026-05-15 - Added `gpt-5.5` as the active Taskmaster `codex-cli` model and configured Taskmaster to use the PATH-resolved global Codex CLI 0.130.0 executable because the bundled 0.60.1 binary is too old for that model.
- 2026-05-15 - Retested parent `update-task` with `codex-cli`/`gpt-5.5`; it completed, narrowed Task 109 parent details/test strategy to Option B, and required a targeted generated-file refresh plus drift review.
- 2026-05-15 - End-of-day checkpoint prepared with Task 109 still active; next continuation should start with 109.2 schema contracts.

## Continuation & Handoff
- Next owner: loucmane (default)
- Context reload steps:
  1. Read `sessions/current` and this plan.
  2. Review Taskmaster Task 109 and its subtasks.
  3. Review the foundation installer/MCP architecture artifact before changing helper behavior.
  4. Use `task-master update-subtask` for targeted notes and parent `task-master update-task` only for narrow scope updates; after either path, run `python3 scripts/codex-task taskmaster generate-one --id 109` and inspect the diff.
  5. Run `python3 scripts/codex-task plan sync` after tracker updates.
- Outstanding risks/todos: keep the MCP server as a wrapper around the deterministic CLI/library core, do not expand V1 beyond the generic-profile CLI prototype without an explicit decision entry, and treat AI-backed Taskmaster updates as reviewed changes because they may emit task/subtask drift warnings even when Taskmaster restores identity.

## Conflict & Scope Declaration
- Related plans: Tasks 94-95 enforcement groundwork, Task 97 dashboard follow-on.
- Guard cross-check: wizard flows must preserve plan/tracker/session compliance as the default path.

## Evidence Checklist
- Foundation installer/MCP architecture note under `designs/`
- Tracker/session entries for kickoff and implementation progress
- Stored test and guard evidence once the wizard implementation lands

## Emergency Bypass Protocol
- No bypass authorized.
