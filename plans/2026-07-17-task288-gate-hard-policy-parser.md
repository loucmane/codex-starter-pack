---
session_id: 2026-07-17-001
work_context: task288-gate-hard-policy-parser
handler_target: .claude/scripts/gate_lib.py
task_ids: [288]
branch_policy: codex/task-288-gate-hard-policy-parser
evidence_summary:
  - tests/fixtures/aegis/gate-hard-policy-corpus.json
  - tests/claude_adapter/test_pretooluse_gates.py
  - tests/claude_adapter/test_break_glass.py
  - docs/ai/work-tracking/active/20260717-task288-gate-hard-policy-parser-ACTIVE/
plan_version: v1
emergency_bypass: false
---

# Plan - PR Scope 288 Gate Hard-Policy Parser

## Header
- **Session ID (S)**: 2026-07-17-001
- **Work Context (W)**: task288-gate-hard-policy-parser
- **Handler Target (H)**: `.claude/scripts/gate_lib.py`
- **Task IDs**: 288
- **Branch Policy**: codex/task-288-gate-hard-policy-parser
- **Evidence Summary (E)**: `tests/fixtures/aegis/gate-hard-policy-corpus.json`, `tests/claude_adapter/test_pretooluse_gates.py`, `tests/claude_adapter/test_break_glass.py`, `docs/ai/work-tracking/active/20260717-task288-gate-hard-policy-parser-ACTIVE/`
- **Plan Version**: v1
- **Emergency Bypass**: false

Task ID `288` is a pull-request-scoped workflow compatibility identifier. It is not a
Taskmaster task. Taskmaster is frozen for the Gas City transition, and this change creates,
updates, regenerates, or reinitializes no Taskmaster state.

## Plan Table
| Step ID | Description | Evidence | Status |
|---------|-------------|----------|--------|
| plan-step-scope | Freeze the prerequisite PR boundary, sensitive command families, and no-Taskmaster constraint | plans/2026-07-17-task288-gate-hard-policy-parser.md | completed |
| plan-step-test-first | Add a shared adversarial corpus and prove the vulnerable implementation fails before changing gate behavior | tests/fixtures/aegis/gate-hard-policy-corpus.json; tests/claude_adapter/test_pretooluse_gates.py; tests/claude_adapter/test_break_glass.py | completed |
| plan-step-implement | Make both source and packaged gates fail closed for concealed sensitive commands and parse RFC3339 expiry values as datetimes | .claude/scripts/gate_lib.py; aegis_foundation/assets/.claude/scripts/gate_lib.py | completed |
| plan-step-verify | Run focused, adapter, release, lint, parity, guard, witness, and CI verification without touching the dirty primary checkout | docs/ai/work-tracking/active/20260717-task288-gate-hard-policy-parser-ACTIVE/HANDOFF.md; docs/ai/work-tracking/active/20260717-task288-gate-hard-policy-parser-ACTIVE/TRACKER.md | in-progress |
| plan-step-emergency | Record any emergency bypass and post-mortem requirement | plans/2026-07-17-task288-gate-hard-policy-parser.md | n/a |

## Scope
- `.claude/scripts/gate_lib.py`
- `aegis_foundation/assets/.claude/scripts/gate_lib.py`
- `tests/claude_adapter/test_pretooluse_gates.py`
- `tests/claude_adapter/test_break_glass.py`
- `tests/fixtures/aegis/gate-hard-policy-corpus.json`
- `plans/2026-07-17-task288-gate-hard-policy-parser.md`
- `plans/current`
- `sessions/2026/07/2026-07-17-001-task288-gate-hard-policy-parser.md`
- `sessions/current`
- `sessions/state.json`
- `docs/ai/work-tracking/active/20260717-task288-gate-hard-policy-parser-ACTIVE/`
- `.serena/memories/2026-07-17_task288_gate_hard_policy_parser.md`
- `.plan_state/sync.log`

Out of scope are `/home/loucmane/codex`, Taskmaster data, Gas City runtime state, provider
credentials, GitHub App credentials, live workers, and every tx35a change beyond the
read-only Checkpoint A inventory.

## Branch Policy
- Working branch: `codex/task-288-gate-hard-policy-parser`
- Work occurs only in `/tmp/aegis-gate-security-pr-20260717`, a standalone clean clone.
- The dirty primary checkout remains untouched until the attended tx35a Checkpoint F.

## Amendments & Versioning
- 2026-07-17 - v1 records the already test-first gate-security slice and the workflow-only
  metadata required by repository guard and witness checks.

## Continuation
- Finish local guard/witness verification and draft PR CI.
- Do not merge automatically.
- After the prerequisite PR is reviewable, continue only with tx35a Checkpoint A, then stop.
- Keep Taskmaster frozen and do not reinterpret scope ID 288 as Taskmaster authority.

## Conflict & Scope Declaration
- The prerequisite security change is independent of existing dirty work in
  `/home/loucmane/codex`; no reset, stash, clean, rebase, or rewrite is authorized there.
- PR workflow metadata is additive evidence only and does not modify the gate policy result.

## Emergency Bypass Protocol
- No bypass is authorized.
