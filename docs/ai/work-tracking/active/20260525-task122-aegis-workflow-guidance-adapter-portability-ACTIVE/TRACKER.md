# Task 122 Advance Aegis Workflow Guidance and Adapter Portability Tracker

**Started**: 2026-05-25
**Status**: ACTIVE
**Last Updated**: 2026-05-25

## Goals
- [x] Add a read-only Aegis next-action guidance surface for CLI and MCP
- [x] Make plan-step logging deterministic with plan-step auto and clear inference metadata
- [x] Add closeout-ready or dry-run repair guidance before strict closeout
- [x] Document live acceptance matrix, adapter contract, and release readiness boundaries

## Progress Log
- **2026-05-25 13:15** — [S:20260525|W:task122-aegis-workflow-guidance-adapter-portability|H:shell:date|E:cmd`date "+%Y-%m-%d %H:%M %Z"`] Confirmed current timestamp as `2026-05-25 13:15 CEST`
- **2026-05-25 13:15** — [S:20260525|W:task122-aegis-workflow-guidance-adapter-portability|H:scripts/codex-task|E:docs/ai/work-tracking/active/20260525-task122-aegis-workflow-guidance-adapter-portability-ACTIVE/TRACKER.md] Scaffolded the Task 122 ACTIVE work-tracking folder through the guided kickoff flow
- **2026-05-25 13:15** — [S:20260525|W:task122-aegis-workflow-guidance-adapter-portability|H:task-master:set-status|E:.taskmaster/tasks/tasks.json] Marked Taskmaster Task 122 in progress and updated only its generated task file
- **2026-05-25 13:15** — [S:20260525|W:task122-aegis-workflow-guidance-adapter-portability|H:sessions/current|E:sessions/current] Repointed `sessions/current`, `plans/current`, and `sessions/state.json` to the new Task 122 kickoff
- **2026-05-25 13:18** — [S:20260525|W:task122-aegis-workflow-guidance-adapter-portability|H:serena/memory|E:.serena/memories/2026-05-25_task122_aegis_workflow_guidance_kickoff.md] Captured Task 122 kickoff context and architectural boundaries
- **2026-05-25 13:18** — [S:20260525|W:task122-aegis-workflow-guidance-adapter-portability|H:codex:design|E:docs/ai/work-tracking/active/20260525-task122-aegis-workflow-guidance-adapter-portability-ACTIVE/designs/wizard-flow.md] Defined Task 122 scope baseline for Aegis next-action guidance, deterministic plan-step logging, closeout readiness, prompts, live matrix, and adapter portability
- **2026-05-25 13:23** — [S:20260525|W:task122-aegis-workflow-guidance-adapter-portability|H:shell:date|E:cmd`date "+%Y-%m-%d %H:%M:%S %Z %z"`] Confirmed current timestamp as `2026-05-25 13:23:50 CEST +0200`
- **2026-05-25 13:24** — [S:20260525|W:task122-aegis-workflow-guidance-adapter-portability|H:codex:implement|E:scripts/_aegis_installer.py] Added the shared read-only `next_action` guidance evaluator and embedded its workflow guidance into Aegis status
- **2026-05-25 13:24** — [S:20260525|W:task122-aegis-workflow-guidance-adapter-portability|H:codex:implement|E:aegis_mcp/server.py] Exposed `aegis.next` as a read-only MCP tool and updated status descriptions to advertise embedded next guidance
- **2026-05-25 13:24** — [S:20260525|W:task122-aegis-workflow-guidance-adapter-portability|H:codex:verify|E:cmd`PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_installer.py -k "next_action"`] Ran focused installer guidance tests with 2 passed
- **2026-05-25 13:24** — [S:20260525|W:task122-aegis-workflow-guidance-adapter-portability|H:codex:verify|E:cmd`PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_mcp_server.py -k "expected_tools or workflow_tools_describe_required_next_actions or status_reports_current_install_without_mutation or next_reports_guidance"`] Ran focused MCP guidance tests with 3 passed
- **2026-05-25 13:28** — [S:20260525|W:task122-aegis-workflow-guidance-adapter-portability|H:shell:date|E:cmd`date "+%Y-%m-%d %H:%M:%S %Z %z"`] Confirmed current timestamp as `2026-05-25 13:28:40 CEST +0200`
- **2026-05-25 13:28** — [S:20260525|W:task122-aegis-workflow-guidance-adapter-portability|H:codex:verify|E:cmd`PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_installer.py tests/meta_workflow_guard/test_aegis_mcp_server.py`] Ran the affected Aegis installer and MCP server suites with 60 passed and 1 opt-in certification smoke skipped
- **2026-05-25 13:33** — [S:20260525|W:task122-aegis-workflow-guidance-adapter-portability|H:shell:date|E:cmd`date "+%Y-%m-%d %H:%M:%S %Z %z"`] Confirmed current timestamp as `2026-05-25 13:33:08 CEST +0200`
- **2026-05-25 13:33** — [S:20260525|W:task122-aegis-workflow-guidance-adapter-portability|H:codex:implement|E:scripts/_aegis_installer.py] Added deterministic `plan_step=auto` inference for scope, implementation, and verification events, with ambiguous inference rejected
- **2026-05-25 13:33** — [S:20260525|W:task122-aegis-workflow-guidance-adapter-portability|H:codex:verify|E:cmd`PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_installer.py tests/meta_workflow_guard/test_aegis_mcp_server.py tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py -k "next_action or plan_step_auto or log_work_plan_step_auto or status_reports_current_install_without_mutation or next_reports_guidance or expected_tools or workflow_tools_describe_required_next_actions or pending_tracking or local_shim"`] Ran affected guidance and auto-plan tests with 7 passed
- **2026-05-25 13:55** — [S:20260525|W:task122-aegis-workflow-guidance-adapter-portability|H:codex:implement|E:scripts/_aegis_installer.py] Added dry-run closeout/readiness support, read-only MCP `aegis.closeout_ready`, and non-mutating verification dry-run plumbing
- **2026-05-25 13:55** — [S:20260525|W:task122-aegis-workflow-guidance-adapter-portability|H:codex:implement|E:docs/aegis/live-acceptance-matrix.md] Added live acceptance criteria for fresh/existing web, Python, backend, existing MCP config, local shim fallback, no-Taskmaster/no-Serena, and live Claude rows
- **2026-05-25 13:55** — [S:20260525|W:task122-aegis-workflow-guidance-adapter-portability|H:codex:implement|E:docs/aegis/agent-adapter-contract.md] Added the adapter contract documenting Claude as implemented and Codex/Gemini/future agents as planned
- **2026-05-25 13:55** — [S:20260525|W:task122-aegis-workflow-guidance-adapter-portability|H:codex:verify|E:cmd`PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_installer.py tests/meta_workflow_guard/test_aegis_mcp_server.py tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py tests/meta_workflow_guard/test_aegis_release_distribution.py tests/meta_workflow_guard/test_aegis_native_mcp_registration.py tests/meta_workflow_guard/test_aegis_invocation_contract.py tests/meta_workflow_guard/test_aegis_mcp_contract_docs.py`] Ran the broader affected Aegis suite with 122 passed and 4 opt-in smoke tests skipped
- **2026-05-25 13:56** — [S:20260525|W:task122-aegis-workflow-guidance-adapter-portability|H:codex:verify|E:cmd`PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_*.py`] Ran the full Aegis meta-workflow test group with 151 passed and 4 opt-in smoke tests skipped
- **2026-05-25 13:56** — [S:20260525|W:task122-aegis-workflow-guidance-adapter-portability|H:codex:verify|E:cmd`python3 scripts/codex-task plan sync && python3 scripts/codex-task taskmaster health && git diff --check && python3 scripts/codex-guard validate --include-untracked && python3 scripts/codex-task work-tracking audit`] Ran repository gates; plan sync recorded, Taskmaster health OK, diff check clean, guard passed, and work-tracking audit passed
- **2026-05-25 14:01** — [S:20260525|W:task122-aegis-workflow-guidance-adapter-portability|H:task-master:set-status|E:.taskmaster/tasks/tasks.json] Marked Taskmaster Task 122 done and refreshed only `.taskmaster/tasks/task_122.md`

## Plan Compliance Checklist
- [x] plan-step-scope — Define alignment prerequisites and scope
- [x] plan-step-implement — Update workflow/guard/docs and capture tests
- [x] plan-step-verify — Evidence stored, documentation updated
- [ ] plan-step-emergency (if applicable)

## Dependencies & Notes
- Session log: sessions/current
