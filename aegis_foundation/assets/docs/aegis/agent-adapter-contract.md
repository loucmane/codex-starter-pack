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
| Codex | planned adapter | `CODEX.md`, future Codex adapter manifest | repo guard and local workflow commands; direct Claude hook parity not assumed | `codex mcp add ... aegis ...` | shell/tool edits, git, MCP where available | gated/planned | same S:W:H:E surfaces through Aegis CLI/MCP | adapter-specific smoke before implementation status can move beyond planned |
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

## Future Adapter Promotion

An adapter moves from planned to implemented only when a task provides:

- entrypoint files and installation assets
- hookability taxonomy with verified, CI-detectable, and policy-only labels
- MCP registration proof
- protected path and workflow state mutation tests
- live acceptance row proving the full Aegis workflow in a fresh project
