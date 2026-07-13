# Aegis Agent Adapter Contract

Aegis is agent-neutral at the workflow layer. The installed project owns workflow state and enforcement; each agent adapter supplies the entrypoint, tool guidance, and available hook surfaces needed to follow that workflow.

## Adapter Rules

- Aegis MCP/CLI is the control plane for install, status, next-action guidance, kickoff, logging, verification, and closeout.
- Native agent tools perform implementation reads, edits, test runs, and git inspection.
- In other words, native agent tools perform implementation; Aegis records and gates workflow state.
- Agents must not write `.aegis/` directly.
- Mechanical enforcement beats prompt guidance. Prompt text is never workflow evidence.
- Each adapter must declare mutation surfaces, hook capability, protected paths, and verification commands before it is considered implemented.

## Adapter Matrix

| Adapter | Status | Entry Files | Hook Capability | MCP Registration | Mutation Surfaces | Enforcement Level | Evidence Model | Required Verification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Claude | implemented default | `CLAUDE.md`, `.claude/settings.json`, `.claude/scripts/*.sh` | PreToolUse, PostToolUse, Stop hooks for supported tools | `claude mcp add --scope user/project aegis ...` or project `.mcp.json` fallback | Edit, Write, MultiEdit, NotebookEdit, Bash, MCP calls routed through Claude Code | mechanical for hookable mutations, policy-only for unsupported memory/MCP surfaces | S:W:H:E entries in session, tracker, implementation, changelog, handoff, and plan evidence | readiness, pending-tracking block, protected path guard, strict verify, closeout |
| Codex | implemented passive-evidence adapter | `CODEX.md`, `.codex/hooks.json`, `scripts/codex-*` | synchronous SessionStart, PostToolUse, SubagentStart, and SubagentStop recorders; project hook trust required | `codex mcp add ... aegis ...` | Bash, apply_patch, MCP calls, and supported lifecycle events | passive recording plus delivery-time verification; no Claude-style interior PreToolUse gate | shared out-of-worktree ledger plus complementary S:W:H:E surfaces | structural hook merge, trust/reload marker, linked-worktree/child capture, strict verify, branch-safe witness/replay |
| Gemini | planned adapter | future `GEMINI.md` or client-native entrypoint | unverified | generic MCP stdio registration if supported by client | client-specific file edit, shell, MCP surfaces | planned | same portable Aegis state, with adapter limitations recorded | hookability discovery and live smoke required |
| Future agents | planned | agent-specific entrypoint plus `.aegis/contract.md` | discovered per client | generic stdio or native client registration | declared by adapter task | planned until tested | Aegis S:W:H:E plus adapter-specific limitations | inspect/install/kickoff/log/verify/closeout live row |

## Claude Adapter Baseline

Claude is the default implemented adapter because Claude Code exposes project hooks that can mechanically gate common mutation tools. The required installed files are:

- `CLAUDE.md`
- `.claude/settings.json`
- `.claude/scripts/readiness.sh`
- `.claude/scripts/pretooluse-gate.sh`
- `.claude/scripts/posttooluse-tracking.sh`
- `.claude/scripts/tracking-stop-gate.sh`
- `.claude/scripts/bash-command-guard.sh`
- `.claude/scripts/codex-path-guard.sh`
- `.claude/scripts/gate_lib.py`

Claude-specific acceptance requires:

- cold session blocks persistent mutation when readiness is BLOCKED
- READY session allows task-scoped evidence writes
- pending tracking blocks the next mutation and Stop until logged
- protected-path Edit and Bash bypasses are refused
- `aegis.next`, `plan_step=auto`, strict verify, closeout-ready dry-run, and final closeout guide a fresh Claude client without hand-editing workflow files

## Codex Adapter Baseline

Codex project hooks are a passive evidence surface, not a clone of Claude's strict
interior mutation gate. The installer structurally merges these handlers into
`.codex/hooks.json`:

- `SessionStart` (`startup|resume|clear|compact`) → capsule/session-begin recording;
- `PostToolUse` (`Bash`, `apply_patch`, and MCP tools) → successful and failed tool evidence;
- `SubagentStart` → child lifecycle start;
- `SubagentStop` → child lifecycle end with valid JSON hook output.

Every command resolves `$(git rev-parse --show-toplevel)/.aegis/bin/aegis`, so starting
Codex in a subdirectory remains stable. Handlers are synchronous because current Codex
parses but skips asynchronous command hooks; Aegis's recorder is fail-open and must never
block the tool or subagent lifecycle. Project-local command hooks require trust for their
exact definition hash. The client-reload marker therefore remains blocking for Codex
workflow mutations until the operator restarts Codex, reviews/trusts the hook with
`/hooks`, and triggers a trusted SessionStart (`/clear` or another restart).

Linked worktrees use the same repository-owned out-of-worktree ledger through their Git
common directory. Each row still records its own repository identity, worktree root,
branch, full HEAD, session, agent, and supported parent identifier. No `.aegis/state`
copy is installed or maintained per worktree. Current Codex payloads support factual
child-to-session-root attribution; deeper nested parent-agent ancestry remains an
explicit capability limitation unless the client or launcher supplies
`AEGIS_PARENT_AGENT_ID`.

Codex-specific acceptance requires:

- install/update preserves unrelated hooks and refuses invalid JSON rather than replacing it;
- all four exact Aegis registrations verify mechanically and contain no unsupported `async` flag;
- Claude and Codex reload markers clear independently in a multi-agent install;
- two child worktrees record mutations, failures, lifecycle, branch, HEAD, and attribution into one store;
- SQLite lock contention loses no events, worktree teardown loses no history, and sibling verification cannot satisfy the current branch;
- replay defaults to the current repository/branch and exposes explicit cross-branch corpus mode.

## Future Adapter Promotion

An adapter moves from planned to implemented only when a task provides:

- entrypoint files and installation assets
- hookability taxonomy with verified, CI-detectable, and policy-only labels
- MCP registration proof
- protected path and workflow state mutation tests
- live acceptance row proving the full Aegis workflow in a fresh project
