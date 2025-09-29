# codex-task + Guard Implementation Plan

## Overview
Implement helper + validator that enforces handler-driven workflow and evidence capture without wrapper hacks.

## Components
1. `scripts/codex-task`
   - Subcommands (initial target set):
     - `sessions/update`
     - `work-tracking/update`
     - `scanner/run <tool>`
   - Responsibilities:
     - Invoke Serena handler search (e.g., `find_symbol` / `search_for_pattern`).
     - Display the handler snippet (read via `read_file`).
     - Scaffold session/work-tracking entries (S:W:H:E placeholders) with timestamps from `date`.
     - Run validator after user completes the task.

2. `scripts/codex-guard`
   - Diff-aware validator:
     - Inspect `git diff --name-only` relative to target base (origin/main or fallback to HEAD~).
     - For each touched file, verify:
       - Session/work-tracking structure matches template conventions.
       - Latest S:W:H:E entry references valid handler (`serena find_symbol` confirms).
       - Evidence includes file:line or command output.
       - Timestamps and branch fields match `date` / `git branch --show-current`.
     - Optional `--auto-fix` to insert skeleton S:W:H:E blocks or correct headings when safe.
     - Human-readable remediation guidance on failure.

3. Optional integrations
   - Provide `codex-guard --validate` command for manual checks.
   - Optional git pre-commit + CI job (document but keep off by default).

## Success Criteria
- `codex-task` subcommands produce compliant session/work-tracking entries without manual editing.
- `codex-guard --validate` passes on a clean tree and blocks tasks that skip handler/evidence requirements.
- Documentation updated (`CODEX.md`, HANDOFF, CHANGELOG) with usage examples.
- Remaining SSOT remediation work uses this workflow.

## Status (2025-09-20 20:18)
- `scripts/codex-task` implemented with sessions/work-tracking/scanner commands; docs pending polish.
- `scripts/codex-guard validate` available; auto-fix + CI integration remain TODO.
