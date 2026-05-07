# Task 105 Claude Runtime Adapter Hardening Kickoff

Date: 2026-05-07
Branch: feat/task-105-claude-runtime-adapter-hardening
Taskmaster: Task 105, Validate and Harden Claude Runtime Adapter, status in-progress. Subtask 105.1 is in progress.

Context:
- Task 103 already completed the initial Claude Runtime Adapter and is archived at docs/ai/work-tracking/archive/20260506-task103-claude-runtime-adapter-COMPLETED/.
- Task 105 is not a duplicate rebuild. It is a validation and hardening follow-up created because the user wants Claude enforcement to be mechanical and unavoidable rather than memory or documentation based.
- Task 105 intentionally takes priority over Task 10 by explicit user direction because multimodal and multi-agent enforcement is foundational for later project work.

Current scaffold:
- Session: sessions/2026/05/2026-05-07-002-task105-claude-runtime-adapter-hardening.md
- Plan: plans/2026-05-07-task105-claude-runtime-adapter-hardening.md
- Active work tracking: docs/ai/work-tracking/active/20260507-task105-claude-runtime-adapter-hardening-ACTIVE/

Initial findings:
- Official Claude Code hook docs confirm PreToolUse can block tool calls with exit code 2 and MCP tools can be matched using mcp__<server>__<tool> names.
- Task 103 current implementation already has readiness.sh, pretooluse-gate.sh, gate_lib.py, codex-path-guard.sh, bash-command-guard.sh, handoff-nudge.sh, .claude/settings.json, and focused tests.
- Initial hardening gaps are current-state specific: .claude/engine/runtime-contract.md is stale after Task 103 archive, MCP mutating tools are not currently routed through PreToolUse, ConfigChange and UserPromptExpansion/lifecycle hooks need audit, and memory/MCP hookability labels must stay test-backed or policy-only.

Next steps:
1. Complete plan-step-scope by finalizing docs/ai/work-tracking/active/20260507-task105-claude-runtime-adapter-hardening-ACTIVE/designs/hook-surface-audit.md and updating tracker/plan.
2. Run plan sync and guard until baseline passes.
3. Only then implement narrow hardening changes backed by tests.