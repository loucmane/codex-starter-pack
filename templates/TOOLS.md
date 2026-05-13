
> **Codex Equivalent:** References to Claude's TodoWrite/TodoRead should be handled in Codex by updating the plan tool (Plan update ≈ TodoWrite, Plan display ≈ TodoRead) alongside the work-tracking checklists.
# Codex Tooling & Command Router

This document defines the allowed tools inside the Codex CLI, how to choose between them, and the evidence you must produce when using each one.

## 🚦 Decision Router
Follow this checklist before every tool invocation:

1. **State the intent** – "I need to inspect tests for feature X".
2. **Pick the matching tool** using the table below.
3. **Echo the command** (or MCP call) you will run.
4. **Capture output** and cite file paths / line numbers as evidence.

### Action → Tool Mapping

| I need to… | Preferred tool | Notes |
|------------|----------------|-------|
| Search text/code | `shell` `rg`, `ripgrep`, or project MCP search | Show command + snippet; prefer `rg -n` for line numbers |
| List files | `shell` `ls`, `fd`, or `find` | Use `ls -A` / `fd` for filtered views |
| Inspect files | `shell` `sed`, `cat`, `python3 - <<'PY'` | Provide line numbers when possible |
| Edit files | Editor integration outside Codex or scripted edit + review | Codex CLI is read/write; confirm edits via diff |
| Run tests | `shell` (pytest, npm, etc.) | Capture command + pass/fail summary |
| Open docs/web | `web_search` or MCP HTTP tool (if enabled) | Note when network approvals were required |
| Delegate to agent | Configured MCP specialist (e.g., TaskMaster) | Show request payload and returned summary |

### When MCP Servers Are Available
- Registered under `[mcp_servers]` in `.codex/config.toml`.
- Invoke via the `mcp` commands (e.g., `/mcp call taskmaster-ai plan`).
- Document server name, method, and key response fields.

#### Serena (Semantic Toolkit)
- **Purpose**: Symbol-aware inspection/editing when the active MCP exposes those tools, plus mandatory workflow memory continuity when guard/work-tracking requires Serena evidence.
- **Command pattern**: `/mcp call serena <tool> ...` (see `templates/shared/tools/tool-selection-matrix.md` for full router).
- **Status check**: Run `python3 scripts/codex-task serena status --strict` when a workflow depends on Serena, and confirm runtime tools with `mcp__serena__.get_current_config` inside an active agent session.
- **When to use**: Use Serena for semantic code/template structure and memory handoff; use deterministic registry/scanner/`rg` evidence for exact template lookup and text search. Record any fallback when Serena is unavailable or lacks a required tool.

#### Taskmaster AI
- **Purpose**: Task planning, dependency tracking, TodoRead/Write integration.
- **Command pattern**: `/mcp call taskmaster-ai <method>`.
- **Evidence**: Paste the request payload and returned task summaries.

#### Context7
- **Purpose**: Live documentation lookup.
- **Command pattern**: `/mcp call context7-mcp get-library-docs --topic "..."`.
- **Notes**: Keep queries scoped (single topic/file) to control token use.

#### Sequential Thinking
- **Purpose**: Guided multi-thought analysis.
- **Command pattern**: `/mcp call sequential-thinking think --total_thoughts 10` (returns structured thought log).
- **Use**: When problems need deliberate reasoning beyond default planning.

## Built-in Tools

### `shell`
Primary interface for filesystem and process commands. Always:
- Show the exact command (prefixed with `$`).
- Provide the working directory if it differs from `~/codex`.
- Capture stderr when the command fails and explain the next step.

### `update_plan`
Lightweight structured plan tracker. Use it to:
- Declare multi-step work before making changes.
- Update after each completed step.
- Close the plan at the end (status `completed`).

### `scripts/codex-task`
Local CLI for S:W:H:E scaffolding. Subcommands:
- `bootstrap init` – scaffold starter portable-foundation assets into a target repo without overwriting existing config/policy files unless `--force` is passed.
- `sessions continue` – create a fresh daily session for an existing active task while reusing the task-scoped ACTIVE work-tracking folder and plan.
- `sessions update` – append to active session progress log.
- `work-tracking update` – append to ACTIVE docs (default `TRACKER`).
- `taskmaster generate-one --id <task-id>` – run Taskmaster generation in a temporary directory and update only the requested generated task file.
- `wizard kickoff` – guided task startup that scaffolds work tracking, creates a compliant session + plan, updates `sessions/current` / `plans/current` / `sessions/state.json`, seeds plan sync, marks the Taskmaster task `in-progress`, and refreshes only that task’s generated file.
- `scanner run <tool>` – execute SSOT scanners and optionally log results (`--log-note`).
- `serena status --strict [--report-file <path>]` – verify Codex and project-level Serena MCP configuration plus `.serena/memories/` readiness before relying on Serena evidence.
- `compaction checkpoint --task <id> --slug <slug> --summary <state> --next-step <next>` – create a continuation checkpoint before context compaction, including manifest, resume message, Serena memory file, session/tracker entries, handoff note, and `.plan_state/compaction-history.jsonl`.
Always pass `--work`, `--handler`, and `--evidence`; use single quotes to preserve backticks.

Repo-structure note:
- `scripts/codex-task` now derives its operational roots from `[repo_structure]` in `.codex/config.toml`.
- Defaults still map to this repo’s current layout (`sessions/`, `plans/`, `.taskmaster/`, `docs/ai/work-tracking/`, `reports/`), but alternate repositories can override those roots without editing the script.

Bootstrap guidance:
- Use `python3 scripts/codex-task bootstrap init --target-dir <repo>` to seed `.codex/config.toml`, the starter metadata policy, bootstrap setup notes, and the missing workflow roots in a new or existing repository.
- Existing `.codex/config.toml` and metadata policy files are preserved by default so adoption stays migration-safe; pass `--force` only when you explicitly want to refresh starter files.
- Override repo roots with `--templates-root`, `--sessions-root`, `--plans-root`, `--plan-state-dir`, `--taskmaster-root`, `--work-tracking-root`, or `--reports-root` when the target repository should not use the defaults.

Wizard guidance:
- Use `python3 scripts/codex-task wizard kickoff --task <id>` when starting a new task on a feature branch that already matches `feat/task-<id>...`.
- Use `python3 scripts/codex-task sessions continue --task <id> --slug <slug>` when continuing the same active task on a new day. Do not archive task work tracking or run kickoff again just to get a fresh daily session.
- The wizard is intentionally narrow: it handles kickoff safely, but it does not replace Serena memory capture or later implementation logging.
- After direct Taskmaster status/update commands, run `python3 scripts/codex-task taskmaster generate-one --id <id>` instead of broad in-place `task-master generate`.
- After kickoff, continue using `sessions update`, `work-tracking update`, and `plan sync` for same-day progress.

### `scripts/codex-guard`
Run `scripts/codex-guard validate [--include-untracked]` before handoff/compaction. Confirms:
- S:W:H:E fields populated (no placeholders).
- Handler paths resolve into `templates/` (when referenced).
- Evidence fields not left `pending`.
- Runtime artifacts stay out of commits (`__pycache__/`, `.pyc`/`.pyo`, `.codex/*.sqlite*`).
- Taskmaster status/file changes include same-day session and tracker evidence.
- Session state stays coherent (`sessions/current`, `sessions/state.json`, paused session references).
- Canonical commit guidance distinguishes `direct-git-execution`, `full-gac-command`, `message-payload-only`, and `auth-refresh-required`, while keeping the multi-line `Summary:` block for substantive task commits.
Roadmap: `--auto-fix` skeletons (document TODOs in work-tracking).

Local hook support:
- `.pre-commit-config.yaml` provides local hooks for `python3 scripts/codex-guard validate --include-untracked` and `python3 scripts/codex-guard drift-check --strict --report-dir ""`.
- The local drift hook disables report output so pre-commit validation does not mutate the working tree; CI still writes drift artifacts.
- Install with `pre-commit install` when the local environment has pre-commit available; CI remains the authoritative merge gate.

GitHub auth/signing support:
- GitHub fetch, push, branch cleanup, PR, and signed commit operations depend on the local SSH/GPG agent state.
- This environment may keep SSH/GPG auth cached for 24 hours after the user refreshes it; if auth starts failing after the cache expires, refresh the agent cache and retry the same operation.
- When the user confirms the SSH/GPG cache is active and asks Codex to commit/push/PR/merge, Codex should run regular `git add`, `git commit`, `git push`, branch cleanup, and PR/merge commands directly after workflow gates pass instead of handing commands back to the user.
- Do not bypass workflow gates, disable signing, change remotes, or use `--no-verify` to work around expired auth unless the user explicitly authorizes and the bypass is recorded in work tracking.

Repo-structure note:
- `scripts/codex-guard` reads `[repo_structure]` from `.codex/config.toml` to resolve session roots, plan roots, Taskmaster roots, work-tracking roots, report directories, and the template metadata policy path.
- Keep the configured roots repo-local and relative unless there is a deliberate reason to point at an absolute path.

Task 92 expanded this guard coverage to turn recurring workflow mistakes into enforceable checks. When adding new guard rules, update the relevant template/convention docs and add targeted regression coverage in `tests/meta_workflow_guard/test_guard_rules.py`.

### `scripts/template-metrics-dashboard`
Repo-level metrics generator for workflow/template health. Use it to refresh:
- `reports/template-metrics/latest.md`
- `reports/template-metrics/latest.json`

Inputs come from Taskmaster state, template-drift reports, plan-sync history, work-tracking folders, session logs, and the existing `codex-guard` metadata helpers. Run it locally before closeout when Task 97-style metrics changes are in scope, and keep CI artifact upload aligned with the output directory.

Repo-structure note:
- The metrics generator also reads `[repo_structure]` from `.codex/config.toml`, so alternate repos can relocate Taskmaster, reports, sessions, and work-tracking without patching the script.

### Static Telemetry Pipeline
Use the static telemetry pipeline when you need a complete local/CI snapshot of workflow health:

```bash
python3 scripts/codex-task report generate --kind telemetry \
  --strict-drift \
  --strict-monitoring \
  --strict-phase0 \
  --strict-performance \
  --strict-cost \
  --strict-migration-health
```

`--kind telemetry` runs the same ordered chain as the legacy `--kind all` report mode:

1. `scripts/codex-guard drift-check` -> `reports/template-drift/`
2. `scripts/template-metrics-dashboard` -> `reports/template-metrics/`
3. `scripts/template-monitoring` -> `reports/template-monitoring/`
4. `scripts/template-phase0-validation` -> `reports/phase0-scanner-validation/`
5. `scripts/template-performance-harness` -> `reports/template-performance/`
6. `scripts/template-cost-report` -> `reports/cost-tracking/`
7. `scripts/template-migration-health-dashboard` -> `reports/migration-health/`

This repository uses file-based telemetry artifacts, not a live observability service. Do not add Prometheus, Grafana, Elasticsearch, StatsD, OpenTelemetry SDK wiring, databases, or background daemons unless a future task proves an actual runtime service needs them.

### `scripts/template-monitoring`
Static monitoring evaluator over the metrics dashboard payload. It reads:
- `reports/template-metrics/latest.json`
- `templates/metadata/template-monitoring-policy.json`

It writes `reports/template-monitoring/latest.md` and `latest.json`. Use `--strict` when error-level monitoring findings should fail the command.

### `scripts/template-phase0-validation`
Static Phase 0 scanner validation evaluator. It reads scanner outputs plus monitoring status and writes `reports/phase0-scanner-validation/latest.md` and `latest.json`. Use it after the scanner suite, metrics dashboard, and monitoring stages are current.

### `scripts/template-performance-harness`
Static performance telemetry for portable foundation operations. It reads `templates/metadata/template-performance-policy.json`, writes `reports/template-performance/latest.md` and `latest.json`, and supports `--baseline-file` plus `--strict` for regression classification.

### `scripts/template-cost-report`
Static cost-governance telemetry. It reads `templates/metadata/template-cost-policy.json`, accepts an optional usage JSON file, writes `reports/cost-tracking/latest.md` and `latest.json`, and reports missing usage data as `not-measured` rather than inventing live billing data.

### `scripts/template-migration-health-dashboard`
Static aggregate migration-health dashboard/report. It reads the latest metrics, monitoring, Phase 0, performance, and cost JSON artifacts, writes `reports/migration-health/latest.md` and `latest.json`, and classifies missing telemetry as visible warnings instead of inventing live data. Use `--strict` when fail-level aggregate migration health should fail the command.

### `scripts/codex-task migration metrics`
Scanner-backed migration KPI packet generator. It reads a metadata-wrapped scanner `baseline_summary.json`, optional migration roadmap JSON, and optional `security_validation.json`, then writes deterministic JSON/Markdown metrics artifacts. It does not start metric agents, write time-series data, create dashboards, send alerts, regenerate scanners, or mutate remediation files.

### `scripts/codex-task migration monitoring`
Static post-migration monitoring packet generator. It reads a migration metrics JSON packet plus `reports/migration-health/latest.json`, classifies aggregate post-migration status, and renders required actions plus weekly/monthly/quarterly/yearly review cadences. It is the portable replacement for live production-monitoring wording in legacy Taskmaster tasks. It does not install schedulers, daemons, live dashboards, alert delivery, external service calls, scanner regeneration, or remediation mutation.

### `scripts/template_governance.py`
Non-mutating template governance assessor. It reads `templates/metadata/template-governance-policy.json` and maps proposed template changes to a required review class.

Use it when a template change needs a review path:

```bash
python3 scripts/template_governance.py assess \
  --path templates/example.md \
  --previous-version 1.2.3 \
  --current-version 2.0.0 \
  --format json
```

The helper reports required roles, approval guidance, escalation guidance, notification audiences, and required evidence. It never sends notifications, schedules meetings, creates votes, or mutates repository files.

### `view_image`
Limited to image previews. Document file path and purpose.

### `web_search` (optional)
Enabled when `.codex/config.toml` sets `tools.web_search = true` and network access is granted. Cite the search query and summarize sources with links.

## Evidence Expectations
- **Searches**: Include command + 1-2 matching lines with context.
- **Edits**: Reference the file and lines modified; run a diff when possible.
- **Tests/Builds**: Provide the command and final status (pass/fail, exit code).
- **MCP Calls**: Log the request + salient parts of the response.

## Anti-Patterns
- Running `grep`/`find` without showing output.
- Modifying files without noting the diff or follow-up plan.
- Invoking network-dependent commands when `network_access=false` and failing to acknowledge the restriction.
- Delegating to MCP servers that are not configured in `.codex/config.toml`.

## Quick Reference
- `rg <pattern> templates/registry` – discover handlers.
- `python3 - <<'PY'` blocks – for JSON/Markdown inspection and summarisation.
- `codex --dry-run -- <command>` – verify wrapper configuration outside the session.

Tools are part of the protocol. Use them deliberately and leave a clear evidence trail every time.

## Progress Log

- **2026-05-12 16:08** — [S:20260512|W:task36-template-governance-board|H:templates/TOOLS.md|E:docs/ai/work-tracking/active/20260512-task36-template-governance-board-ACTIVE/designs/template-governance-scope-reconciliation.md] Added `scripts/template_governance.py` to the tool inventory as a non-mutating template governance assessor.
- **2026-05-08 14:25** — [S:20260508|W:task15-serena-integration-template-system|H:templates/TOOLS.md|E:docs/ai/work-tracking/active/20260508-task15-serena-integration-template-system-ACTIVE/designs/serena-integration-scope-reconciliation.md] Added `codex-task serena status` to the command inventory and clarified Serena as semantic/memory evidence rather than an ad hoc replacement for deterministic registry discovery.
- **2026-05-08 13:52** — [S:20260508|W:task42-session-management-system|H:templates/TOOLS.md|E:docs/ai/work-tracking/active/20260508-task42-session-management-system-ACTIVE/designs/session-management-scope-reconciliation.md] Added `sessions continue` to the codex-task command inventory and documented it as the correct fresh-session path for existing active tasks.
- **2026-04-23 13:15** — [S:20260423|W:task92-expand-workflow-guard-coverage|H:templates/TOOLS.md|E:docs/ai/work-tracking/active/20260422-task92-expand-workflow-guard-coverage-ACTIVE/designs/guard-coverage-audit.md] Documented the expanded `scripts/codex-guard` coverage for runtime artifacts, Taskmaster evidence, session-state consistency, and canonical GAC guidance
