# Agent Compatibility Report

- Created at: 2026-05-12T12:54:25+02:00
- Matrix file: `templates/registry/agent-compatibility-matrix.json`
- Matrix version: 1.0.0
- Contract version: portable-agent-runtime.v1
- Valid: True

## Metrics

- Agents: 3
- Features: 10
- Feature slots: 30
- Mechanical feature coverage: 56.67%
- Policy-only feature slots: 0
- Planned feature slots: 9
- Validation issues: 0

## Agents

### Codex Deep Work Agent

- Agent ID: `codex`
- Status: supported
- Entry point: `CODEX.md`
- Mechanical features: 7
- Planned features: 0
- Policy-only features: 0
- Required gates: 5
- Fallbacks: 2
- Transformations: 1

### Claude Runtime Adapter

- Agent ID: `claude`
- Status: supported
- Entry point: `CLAUDE.md`
- Mechanical features: 9
- Planned features: 0
- Policy-only features: 0
- Required gates: 6
- Fallbacks: 3
- Transformations: 2

### Future Agent/Profile Adapter

- Agent ID: `generic-agent`
- Status: planned
- Entry point: `templates/integration/guides/adding-agents.md`
- Mechanical features: 1
- Planned features: 9
- Policy-only features: 0
- Required gates: 3
- Fallbacks: 2
- Transformations: 1

## Features

- `task_scoped_workflow` — Task-scoped workflow lifecycle (claude: gated; codex: native; generic-agent: planned)
- `guard_validation` — Guard and audit validation (claude: gated; codex: native; generic-agent: planned)
- `pre_mutation_gate` — Pre-mutation gate (claude: gated; codex: documented; generic-agent: planned)
- `protected_path_boundaries` — Protected path ownership boundaries (claude: gated; codex: documented; generic-agent: planned)
- `bash_write_surface_control` — Bash write-surface control (claude: gated; codex: documented; generic-agent: planned)
- `mcp_tool_routing` — MCP tool routing and mutation classification (claude: gated; codex: native; generic-agent: planned)
- `git_github_execution` — Git and GitHub execution (claude: gated; codex: native; generic-agent: planned)
- `memory_continuity` — Memory as continuity, not evidence (claude: gated; codex: native; generic-agent: planned)
- `portable_project_adoption` — Portable project adoption (claude: documented; codex: native; generic-agent: planned)
- `compatibility_metrics` — Compatibility metrics (claude: native; codex: native; generic-agent: native)

## Validation Issues

- None

## Validation Commands

- `python3 scripts/codex-task agent compatibility-report --strict`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/meta_workflow_guard/test_codex_task.py`
- `python3 scripts/codex-guard validate --include-untracked`

## Non-Goals

- No MCP installer is implemented by the matrix.
- No live negotiation service is started.
- No agent-specific file transformation is executed by validation.
- No template path compatibility mapping is duplicated.
