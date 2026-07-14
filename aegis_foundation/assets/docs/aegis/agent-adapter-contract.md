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
| Codex | implemented managed adapter | `CODEX.md`, `.codex/hooks.json`, shared `.claude/scripts/*` dispatch runtime | PreToolUse, PostToolUse, SessionStart, Stop, SubagentStart, and SubagentStop command hooks; canonical `apply_patch` is parsed directly | `codex mcp add ... aegis ...` | Bash, canonical `apply_patch`, MCP calls, and supported lifecycle events | mechanical for trusted hook definitions; passive lifecycle recording plus policy/manual handling for the client-owned exact-hash trust decision | one atomic patch event with all affected paths in the shared out-of-worktree ledger, hierarchical attribution where supported, and complementary S:W:H:E surfaces | managed install parity, exact-hash `/hooks` review, canonical payload regressions, linked-worktree/child capture, strict verify, and branch-safe witness/replay |
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

Codex is an implemented managed adapter. It uses Codex's project hook surface while sharing Aegis's agent-neutral gate and evidence runtime. The installer owns:

- `CODEX.md`
- `.codex/hooks.json`
- `.claude/scripts/readiness.sh`
- `.claude/scripts/pretooluse-gate.sh`
- `.claude/scripts/posttooluse-tracking.sh`
- `.claude/scripts/tracking-stop-gate.sh`
- `.claude/scripts/ledger-record.sh`
- `.claude/scripts/session-brief.sh`
- `.claude/scripts/gate_lib.py` and its support libraries
- the Codex guard, task, delivery-policy, template-governance, and repository-structure scripts

The shared runtime is installed for a Codex-only project even when Claude is disabled. A multi-agent install manages one shared runtime rather than duplicating mutable state or dispatch code.

The managed hook set also records lifecycle and passive evidence synchronously:

- `SessionStart` (`startup|resume|clear|compact`) records capsule/session-begin context;
- `PostToolUse` records successful and failed Bash, `apply_patch`, and MCP evidence;
- `SubagentStart` records child lifecycle start;
- `SubagentStop` records child lifecycle end with valid JSON hook output;
- `Stop` records the same bounded workflow-state decision used by the shared runtime.

Commands resolve the installed Aegis shim from the Git worktree/repository context, so starting Codex in a subdirectory remains stable. Passive recorders are fail-open and must not block tool or subagent lifecycle; PreToolUse and Stop retain the configured strict/advisory enforcement semantics.

Codex matcher aliases such as `Edit` and `Write` may select file-edit hooks, but hook stdin identifies the canonical tool as `tool_name: "apply_patch"` and carries the patch text in `tool_input.command`. Aegis therefore treats `apply_patch` as a first-class mutation surface instead of translating it into Claude tool names. The strict parser accepts only a bounded `*** Begin Patch` / `*** End Patch` envelope containing `*** Add File:`, `*** Update File:`, `*** Delete File:`, and update-scoped `*** Move to:` operations. It normalizes every source and destination path, evaluates the complete path set, and rejects malformed or ambiguous structures. One PostToolUse event records the handler `codex:apply_patch`, the primary path, all affected paths, operation metadata, and the deterministic patch digest.

Linked worktrees use one repository-owned out-of-worktree ledger keyed by the Git common directory. Every enriched row records repository identity, worktree root, branch, full observed HEAD, session, agent, and supported parent identifier. No duplicate mutable `.aegis/state` installation is maintained per worktree. Current Codex payloads support factual child-to-session-root attribution; deeper nested ancestry remains explicitly unsupported unless the client or launcher supplies `AEGIS_PARENT_AGENT_ID`. Witness and replay queries stay branch/worktree scoped, concurrent writers share the WAL-backed store, and removing a worktree does not remove its evidence.

Codex-specific acceptance requires:

- READY and BLOCKED readiness behavior for canonical `apply_patch`
- Add, Update, Delete, Move, and multi-file parsing, including safe-first/protected-later denial
- protected-path, workflow-owned-path, observation, strict/advisory, and degraded fail-closed coverage
- exactly one atomic PostToolUse pending event containing every affected path
- Codex-only and multi-agent install idempotence, source/package parity, and refusal to overwrite a semantically different existing `.codex/hooks.json`
- all managed lifecycle registrations verify mechanically and contain no unsupported asynchronous flag
- Claude and Codex reload markers clear independently in a multi-agent install
- two child worktrees record mutations, failures, lifecycle, branch, HEAD, and attribution into one store
- SQLite lock contention loses no events, worktree teardown loses no history, and sibling verification cannot satisfy the current branch
- replay defaults to the current repository/branch and exposes an explicit cross-branch corpus mode
- a live supported Codex CLI smoke proving canonical hook stdin and pre/post dispatch

Codex stores project-hook trust outside the repository against the exact command-definition hash. Installation or update never bypasses that trust boundary: after `.codex/hooks.json` or its dispatch runtime changes, the operator reconnects the project session, opens `/hooks`, reviews the exact definitions and hashes, and trusts them explicitly. Until then Codex skips the changed definitions and Aegis reports client reload/hook trust as incomplete. See the [official Codex hooks documentation](https://learn.chatgpt.com/docs/hooks#pretooluse).

## Future Adapter Promotion

An adapter moves from planned to implemented only when a task provides:

- entrypoint files and installation assets
- hookability taxonomy with verified, CI-detectable, and policy-only labels
- MCP registration proof
- protected path and workflow state mutation tests
- live acceptance row proving the full Aegis workflow in a fresh project
