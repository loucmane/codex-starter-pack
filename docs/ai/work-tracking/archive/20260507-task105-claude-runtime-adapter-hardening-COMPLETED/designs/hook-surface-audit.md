# Claude Hook Surface Audit

## Purpose
Task 105 validates and hardens the completed Task 103 Claude runtime adapter against the current repository state and current Claude Code hook behavior. The goal is mechanical enforcement, not stronger wording. A future Claude session should hit gates before it can perform hookable persistent mutations without the required task/session/plan/work-tracking state.

## Sources Checked
- Official Claude Code hooks reference: `https://code.claude.com/docs/en/hooks`
- Official Claude Code hooks guide: `https://code.claude.com/docs/en/hooks-guide`
- Task 103 archive: `docs/ai/work-tracking/archive/20260506-task103-claude-runtime-adapter-COMPLETED/`
- Permanent adapter files under `.claude/`
- Focused tests under `tests/claude_adapter/`

## Current Verified Behavior
| Surface | Current file | Current behavior | Evidence |
| --- | --- | --- | --- |
| File tool mutation | `.claude/settings.json`, `.claude/scripts/pretooluse-gate.sh` | `Edit|Write|MultiEdit|NotebookEdit` routes through the dispatcher. When readiness is `BLOCKED`, hookable file mutations are refused. | `tests/claude_adapter/test_pretooluse_gates.py` |
| Bash mutation | `.claude/scripts/gate_lib.py` | Bash commands classified as persistent mutations route through readiness and protected-path checks. | `tests/claude_adapter/test_pretooluse_gates.py` |
| Protected Codex-owned paths | `.claude/scripts/gate_lib.py` | Direct file writes and tested Bash bypasses against `CODEX.md`, `templates/**`, `.codex/**`, `scripts/codex-*`, and `scripts/template-*` are blocked. | `tests/claude_adapter/test_pretooluse_gates.py` |
| Readiness identity | `.claude/scripts/readiness.sh` | Branch task ID, Taskmaster status, `sessions/current`, `plans/current`, ACTIVE tracker, and plan/tracker alignment are required for `READY`. | `tests/claude_adapter/test_readiness_gate.py` |
| Stop reminder | `.claude/scripts/handoff-nudge.sh` | Emits a non-blocking reminder when dirty workflow state or missing audit trail needs attention. | `tests/claude_adapter/test_adapter_contract_files.py` |

## Gaps To Harden
| Gap | Why it matters | Proposed direction |
| --- | --- | --- |
| Permanent runtime contract is stale | `.claude/engine/runtime-contract.md` still says Task 103 is draft and points to active Task 103 paths after archive completion. Future Claude sessions may reload outdated state. | Update the permanent contract to completed/current state and link Task 105 as hardening follow-up. Add tests that reject stale active Task 103 references. |
| MCP tool mutation is not routed through PreToolUse | Current settings match `Edit|Write|MultiEdit|NotebookEdit|Bash` only. Current Claude docs say MCP tools appear as `mcp__<server>__<tool>` and can be matched. | Add matcher coverage for mutating MCP tool names where safe, or document policy-only limitations if matcher behavior cannot be verified locally. |
| Hook configuration weakening is not explicitly protected | If `.claude/settings.json` or local settings disable gates during a ready task, the runtime can be weakened. Current docs include `ConfigChange`, which can block config changes. | Evaluate a `ConfigChange` hook or PreToolUse path protection for hook-bearing settings. Tests must prove any claim. |
| Slash command expansion is not audited | Current docs include `UserPromptExpansion`, which can block slash-command expansion before Claude receives it. Commands that mutate workflow state may deserve a gate before tool use. | Audit current `.claude/commands/` wrappers. Add expansion guard only if it materially improves enforcement and can be tested. |
| Task and subagent lifecycle hooks are not audited | Current docs include `SubagentStart`, `SubagentStop`, `TaskCreated`, and `TaskCompleted`. These can affect multi-agent behavior. | Decide which lifecycle hooks are relevant for this repo. Add context/blocking hooks only where there is a concrete gap. |
| Memory and private side channels remain label-driven | Task 103 taxonomy marks several memory/MCP surfaces as unverified or policy-only. User concern is specifically that Claude may choose memory instead of system. | Promote hookable surfaces with tests. Keep non-hookable surfaces visibly policy-only and never count them as evidence. |

## Implementation Rules
- Do not duplicate Task 103. Only change files where this audit identifies a current gap.
- Do not edit Codex-owned paths as part of Claude-side hardening unless explicitly scoped.
- Do not change tests merely to pass. Tests must preserve the intended block/allow behavior.
- Do not use documentation or memory as enforcement evidence. Runtime hooks, settings, focused tests, and captured command evidence define completion.
- Keep readiness first in the mutation path: mutation request, dispatcher, readiness, block if `BLOCKED`, then narrower target checks if `READY`.

## Implementation Outcomes
| Gap | Outcome |
| --- | --- |
| MCP tool mutation is not routed through PreToolUse | Implemented. `.claude/settings.json` now matches `mcp__.*` through the dispatcher. `gate_lib.py` treats known mutating MCP tools as persistent, allows known read-only MCP tools for inspection, and treats unknown MCP tools as persistent until proven otherwise. |
| Hook configuration weakening is not explicitly protected | Implemented for project settings. `.claude/scripts/config-change-guard.sh` blocks project `.claude/settings.json` changes from applying when required runtime hooks are removed or changed. |
| Permanent runtime contract is stale | Implemented. `.claude/engine/runtime-contract.md` now reflects Task 103 completion and Task 105 hardening rather than stale active Task 103 paths. |
| Slash command expansion is not audited | Audited, no hook added in this patch. Current custom slash commands expand to prompts and subsequent persistent mutations still hit PreToolUse. Add `UserPromptExpansion` only if a concrete slash command mutates before tool use or a skill direct path bypass is observed. |
| Task and subagent lifecycle hooks are not audited | Audited, no hook added in this patch. Existing sub-agent docs require readiness first; task lifecycle hooks are reserved for Claude team workflows once those tools are actively used in this repo. |

## Initial Acceptance Tests
- Cold-session file mutation remains blocked.
- Cold-session Bash write mutation remains blocked.
- Protected Codex-owned path writes remain blocked when ready.
- Runtime contract test rejects stale Task 103 draft/ACTIVE references.
- MCP mutating tools are blocked when readiness is `BLOCKED`; read-only MCP tools remain available for inspection.
- Project `ConfigChange` is blocked when required runtime hooks are removed or changed.
- Any UserPromptExpansion or lifecycle hook claim remains documented as audited/no-current-code until a concrete mutating bypass exists.
