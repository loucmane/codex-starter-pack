# Agent Runtime Contract Map

## Purpose

Tasks 103-107 proved the Claude runtime adapter can operate inside the workflow with mechanical gates. Task 62 remains pending as "Create Agent Compatibility Layer." This map defines how to turn that into a durable multi-agent contract instead of another one-off adapter.

## Completed Inputs

| Task | Completed contribution |
| --- | --- |
| 103 | Claude runtime adapter, readiness hard gate, PreToolUse dispatcher, command wrappers, sub-agent docs, tests. |
| 104 | Targeted Taskmaster generated-file updates to avoid broad task-file churn. |
| 105 | Claude runtime hardening against current harness behavior. |
| 106 | In-harness smoke test proving cold-session mutation blocking, ready-session allowed evidence writes, protected path blocking, and Bash bypass blocking. |
| 107 | Direct Git execution mode so Codex uses standard Git/GitHub flow when auth caches are available, with GAC as fallback only. |

## Current Contract Surfaces

| Surface | Current artifact | Role |
| --- | --- | --- |
| Claude runtime | `.claude/engine/runtime-contract.md` | Permanent Claude-specific contract. |
| Claude readiness | `.claude/scripts/readiness.sh` | Single truth source for workflow alignment. |
| Claude gate | `.claude/scripts/pretooluse-gate.sh` | Tool-boundary enforcement for hookable mutations. |
| Claude command wrappers | `.claude/commands/*.md` | Agent-facing workflow commands. |
| Claude sub-agents | `.claude/agents/*.md` | Sub-agent first-action/readiness rules. |
| Codex runtime | `CODEX.md`, templates, `scripts/codex-*` | Codex operating surface and shared helper layer. |
| Shared workflow | `sessions/`, `plans/`, `docs/ai/work-tracking/`, Taskmaster | Agent-agnostic state and evidence system. |

## Proposed Task 62 Re-Scope

Task 62 should become the permanent compatibility layer for agent runtime adapters:

**Title candidate**: Agent Runtime Compatibility Layer

**Scope candidate**:

- Define a shared adapter manifest schema for agents.
- Record required surfaces for each agent:
  - entrypoint file
  - readiness command
  - mutation gate command
  - allowed/blocked path policy
  - session/plan/work-tracking integration
  - memory policy
  - Git/GitHub behavior
  - smoke-test commands
- Convert Claude-specific lessons into a general contract without weakening Claude gates.
- Add a compatibility matrix that identifies verified, unverified, CI-detectable, and policy-only mutation surfaces per agent.
- Add tests that verify at least Codex and Claude adapter manifests are present and consistent with the shared workflow contract.

## Why This Belongs In Task 62

Task 62 already names agent compatibility. Tasks 103-107 completed the first concrete adapter, so Task 62 can now generalize from evidence instead of speculation.

This avoids creating duplicate "Claude adapter v2" work and keeps future agents from relying on memory-only instructions.

## MCP Relationship

MCP is a tool/control-plane surface, not the entire compatibility layer. The compatibility contract should say how an agent uses MCP safely:

- read-only MCP calls may be allowed during inspection;
- mutating MCP calls must be gated by readiness where the host supports hooks;
- non-hookable MCP mutation surfaces must be labeled policy-only and covered by CI or follow-up guard design where possible;
- no agent-specific MCP wrapper may fork the source-of-truth workflow semantics from `scripts/codex-task` or `scripts/codex-guard`.

## Acceptance Direction

Task 62 should not be considered complete until:

- a shared agent adapter contract exists;
- Codex and Claude have explicit adapter entries;
- hookability/mutation surfaces are classified per agent;
- smoke tests prove at least one blocked cold-session mutation and one allowed ready-session evidence write for every hookable adapter;
- policy-only surfaces are visible in handoff/decision docs and are not counted as mechanical enforcement.

## Progress Log

- **2026-05-10 16:00** — [S:20260510|W:task48-remaining-template-alignment|H:docs/design|E:docs/ai/work-tracking/active/20260510-task48-remaining-template-alignment-ACTIVE/designs/agent-runtime-contract-map.md] Mapped completed Claude runtime work into a proposed Task 62 agent compatibility contract instead of creating duplicate adapter tasks.
