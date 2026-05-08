# Serena Integration Scope Reconciliation

## Context

Task 15 was created before the portable foundation stabilized. Its original wording says template discovery, analysis, and evidence gathering should always be routed through Serena MCP. Current repository evidence shows that a literal interpretation would regress the system:

- Tasks 8, 13, and 28 established deterministic template discovery through `TemplateRegistry`, compatibility maps, scanner outputs, and local registry metadata.
- `TemplateRegistry.resolve(..., allow_serena=True)` already preserves Serena as a structured fallback action for misses (`source=serena`, `fallback_action=serena_search`, `trace` containing `serena:fallback`).
- `scripts/codex-guard` and `python3 scripts/codex-task work-tracking audit` already expect same-day Serena memory references in active task trackers.
- `.codex/config.toml` exposes Serena for Codex, but project `.mcp.json` did not expose Serena for project/Claude clients before this task.
- Several template docs still describe older project names or assume Serena tool availability without requiring a configuration/status check.

## Decision

Task 15 implements a capability-aware Serena contract instead of forcing every template operation through Serena.

The current contract is:

1. Deterministic template lookup remains registry/scanner first.
2. Serena is mandatory for memory continuity and handoff evidence when guard/work-tracking requires a Serena memory reference.
3. Serena semantic tools are used for semantic code/template inspection when the active MCP session exposes them.
4. Local `rg`/registry/scanner evidence remains correct for exact text, frontmatter, task files, generated reports, and deterministic template resolution.
5. Missing or unavailable Serena capability must be recorded as a limitation; the agent must not claim Serena evidence that was not produced.

## Proven Current-State Gap

The enforceable gap is system configuration and verification:

- Project-level `.mcp.json` lacked a `serena` server entry, so a Claude/project session could be asked to produce Serena evidence without the project MCP config exposing Serena.
- There was no local helper to verify Codex config, project MCP config, and `.serena/memories/` readiness before relying on Serena evidence.
- Serena guidance docs needed to distinguish deterministic template discovery from semantic/memory evidence.

## Implementation Surfaces

- `.mcp.json` — add project-level Serena MCP entry using the same pinned `uvx ... serena start-mcp-server --project-from-cwd` command as `.codex/config.toml`.
- `scripts/codex-task` — add `serena status --strict [--report-file <path>]` for configuration/evidence checks.
- `tests/meta_workflow_guard/test_codex_task.py` — add parser/status coverage for the helper and strict missing-config failure.
- `templates/tools/search/serena-guide.md` — replace stale project/tool assumptions with the runtime contract.
- `templates/shared/tools/tool-selection-matrix.md` — clarify Serena vs `rg` routing.
- `templates/TOOLS.md` and `templates/workflows/taskmaster/work-tracking-enforcement.md` — document the helper in the command inventory and standard workflow.
- `templates/workflows/memory/serena-patterns.md` — align memory naming and verification with current task-scoped practice.

## Out of Scope

- Replacing `TemplateRegistry` deterministic discovery with live Serena calls.
- Treating Serena memory as a substitute for session, plan, tracker, findings, decisions, implementation, handoff, or test evidence.
- Enabling optional non-core MCPs.
- Broad `task-master generate`; Taskmaster generated-file updates stay targeted.

## Verification Plan

- `python3 scripts/codex-task serena status --strict --report-file ...`
- `python3 -m pytest tests/meta_workflow_guard/test_codex_task.py`
- `python3 scripts/codex-task plan sync`
- `python3 scripts/codex-task work-tracking audit`
- `python3 scripts/codex-guard validate --include-untracked`
- `git diff --check`
