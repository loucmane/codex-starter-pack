# Decisions

- 2026-05-18 — Use generated throwaway target projects for local MCP E2E validation instead of committing full demo apps. This gives coverage for project shapes without creating permanent example applications that need independent maintenance.
- 2026-05-18 — Validate local MCP behavior before GitHub release-candidate artifact publication. Task 115 must prove new/existing/partial/conflict target behavior first; public artifacts and PyPI remain follow-up release work.
- 2026-05-19 — [S:20260519|W:task115-aegis-mcp-e2e-target-validation|H:sessions:continue|E:sessions/2026/05/2026-05-19-001-task115-aegis-mcp-e2e-target-validation.md] Preserve the existing task-scoped active folder across days and rotate only the daily session pointer.
- 2026-05-19 — [S:20260519|W:task115-aegis-mcp-e2e-target-validation|H:scripts/codex-task:generate-one|E:tests/meta_workflow_guard/test_codex_task.py] Normalize targeted Taskmaster generated files in `generate-one` so diff-check failures are fixed at the generator boundary.

## 2026-05-18 14:19 CEST - Add a second real-project validation layer

[S:20260518|W:task115-aegis-mcp-e2e-target-validation|H:review-gap|E:.taskmaster/tasks/task_115.md]

Decision: reopen Task 115 before merge and add subtask `115.7` for real local target-project validation.

Rationale: generated pytest fixtures are the right CI-friendly regression layer, but they do not fully prove the MCP behaves as expected when installed into representative projects from a user perspective. The missing layer should create concrete temporary target projects for new and already-started Python, web, and backend apps, run the packaged MCP inspect/plan/install/verify flow, and assert existing project files remain unchanged.

## 2026-05-18 15:25 CEST - Separate cold-session enforcement from READY-state usability

[S:20260518|W:task115-aegis-mcp-e2e-target-validation|H:manual-claude-smoke|E:/tmp/aegis-manual-targets-ZUa76T/targets/python-started]

Decision: record the manual Claude smoke as proof that installed cold-session gates work, and treat the missing project-local kickoff/READY path as a distinct follow-up concern rather than silently folding it into the existing proof.

Rationale: the current Task 115 evidence proves install, verify, MCP tool flow, and Claude hook pickup/refusal in real target folders. It does not yet prove that a newly installed project can initialize local Taskmaster/session/plan/work-tracking state and become `READY` without this source repository's mature workflow scaffolding. That is a larger usability/install-completeness concern and must be scoped deliberately before release readiness.

## 2026-05-18 15:28 CEST - Task 115 cannot close on negative-path evidence only

[S:20260518|W:task115-aegis-mcp-e2e-target-validation|H:manual-positive-path-check|E:.taskmaster/tasks/task_115.md]

Decision: reopen Task 115 and add subtask `115.8` for the installed-project positive path.

Rationale: a useful Aegis install must both block invalid cold-session mutation and provide a clear local way to start valid work. The user correctly identified that only proving refusal is a bad test for usability. Task 115 must now prove or implement the path from installed target project to `READY` state, including task branch, task state, session/current, plan/current, active work-tracking folder, and plan/tracker alignment.

## 2026-05-18 16:12 CEST - Make Aegis workflow state native and keep Taskmaster/Serena optional

[S:20260518|W:task115-aegis-mcp-e2e-target-validation|H:aegis:workflow-design|E:docs/ai/work-tracking/active/20260518-task115-aegis-mcp-e2e-target-validation-ACTIVE/designs/local-mcp-e2e-target-matrix.md]

Decision: implement the portable minimum as Aegis-native state plus generated session/plan/work-tracking files. `.aegis/state/current-work.json` is the portable READY authority. Taskmaster is enforced only when no Aegis current-work state exists or when current-work explicitly marks Taskmaster required. Serena is not a readiness dependency.

Options considered:

| Option | Outcome |
| --- | --- |
| Require Taskmaster everywhere | Rejected because it makes Aegis a Taskmaster installer instead of a portable agent foundation. |
| Require Serena everywhere | Rejected because memory is continuity only and should never be evidence or a READY prerequisite. |
| Make MCP the only bootstrap path | Rejected as the only path because projects may not have MCP configured yet. |
| Provide CLI and MCP kickoff over Aegis-native state | Chosen because it works in any git project and lets MCP clients use the same behavior. |

Rationale: the system should be consistent across projects. A downstream project can use Taskmaster and Serena if it wants richer task/memory workflows, but the gate must still work with just Git, Aegis CLI/MCP, sessions, plans, and work-tracking files.

## 2026-05-18 16:35 CEST - Do not let stale optional Taskmaster block Aegis-native work

[S:20260518|W:task115-aegis-mcp-e2e-target-validation|H:claude:readiness|E:tests/claude_adapter/test_readiness_gate.py]

Decision: when `.aegis/state/current-work.json` exists, readiness treats that Aegis-native state as authoritative. Taskmaster is checked as required only if current-work marks `integrations.taskmaster.required: true`; otherwise stale, missing, or non-in-progress Taskmaster state is reported as optional and does not block.

Rationale: a project can have a leftover or partially adopted `.taskmaster/` folder without wanting Taskmaster to govern Aegis. Making mere presence of `.taskmaster/` strict would make Taskmaster a hidden dependency. The opt-in `required` flag preserves integration for projects that want Taskmaster strictness while keeping Aegis portable by default.

## 2026-05-18 17:19 CEST - Make the installed-target runtime matrix a default regression

[S:20260518|W:task115-aegis-mcp-e2e-target-validation|H:pytest:installed-target-runtime-matrix|E:tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py]

Decision: keep the local-wheel MCP smoke env-gated, but add a non-env-gated installed-target runtime matrix that runs in normal CI.

Rationale: wheel smoke is useful for packaging realism but too expensive and environment-dependent for every normal run. The default matrix gives the behavior proof the user needs: Aegis installed into representative concrete projects behaves correctly before and after kickoff, and the installed Claude gate/CLI path can actually create scaffolding and permit normal task output. This catches regressions in project usability even when the release-package smoke is skipped.

## 2026-05-18 16:12 CEST - Allow only Aegis kickoff as the blocked-state bootstrap mutation

[S:20260518|W:task115-aegis-mcp-e2e-target-validation|H:claude:pretooluse|E:aegis_foundation/assets/.claude/scripts/gate_lib.py]

Decision: classify `aegis kickoff` as a deliberate bootstrap mutation that is allowed while readiness is `BLOCKED`; keep other hookable mutations blocked until readiness is `READY`.

Rationale: if every mutation is blocked, Claude cannot use the system to create the state that makes it READY. The exception is narrow: kickoff creates the state the gate requires. Other Aegis mutations such as `aegis verify` remain blocked in cold-session state.

## 2026-05-18 20:59 CEST - Package workflow templates and make kickoff render them

[S:20260518|W:task115-aegis-mcp-e2e-target-validation|H:aegis:workflow-templates|E:templates/aegis/workflow/]

Decision: store the portable workflow document bodies under `templates/aegis/workflow/`, package the same files under `aegis_foundation/assets/templates/aegis/workflow/`, install them into target projects under `.aegis/templates/workflow/`, and make `aegis kickoff`/MCP kickoff render those templates into sessions, plans, and work-tracking files.

Options considered:

| Option | Outcome |
| --- | --- |
| Keep hardcoded document bodies in Python | Rejected because the workflow shape would be hidden in code and would drift from the source project model. |
| Only install template reference docs but keep kickoff hardcoded | Rejected because documentation alone does not make the scaffold reproducible. |
| Render packaged templates during kickoff | Chosen because the target project receives both the generated workflow files and the template contract that produced them. |

Rationale: Aegis should reproduce this repository's operating model in downstream projects. The source and packaged templates make the workflow auditable, and the tests prove the generated scaffold contains the required sections instead of placeholder files.

## 2026-05-19 12:11 CEST - Keep the task-scoped work folder across days, but rotate sessions daily

[S:20260519|W:task115-aegis-mcp-e2e-target-validation|H:sessions:continue|E:sessions/2026/05/2026-05-19-001-task115-aegis-mcp-e2e-target-validation.md]

Decision: keep `docs/ai/work-tracking/active/20260518-task115-aegis-mcp-e2e-target-validation-ACTIVE/` as the active Task 115 work folder, keep the existing Task 115 plan, and use a fresh May 19 session for today’s work.

Rationale: work-tracking folders are task-scoped, not day-scoped. Sessions are day-scoped. This preserves continuity without archiving incomplete task work or backfilling stale session logs.

## 2026-05-19 12:11 CEST - Normalize targeted Taskmaster generated files instead of manually cleaning whitespace

[S:20260519|W:task115-aegis-mcp-e2e-target-validation|H:scripts/codex-task:generate-one|E:tests/meta_workflow_guard/test_codex_task.py]

Decision: make `python3 scripts/codex-task taskmaster generate-one --id <id>` strip trailing whitespace in the targeted generated task file.

Rationale: the final `git diff --check` failure came from Taskmaster-generated markdown, not hand-written implementation content. Fixing the targeted generation path makes the behavior systematic and avoids repeated manual cleanup after status updates.

## 2026-05-19 14:00 CEST - Enforce post-mutation S:W:H:E tracking with pending state

[S:20260519|W:task115-aegis-mcp-e2e-target-validation|H:aegis:post-mutation-tracking|E:.claude/scripts/posttooluse-tracking.sh]

Decision: add a portable post-mutation tracking gate. PostToolUse records successful hookable mutations in `.aegis/state/pending-tracking.json`; PreToolUse blocks the next mutating tool call while pending events exist except for `aegis log`; Stop blocks handoff while pending events exist; `aegis log` appends a single S:W:H:E entry to the active session and tracker, then clears matching pending events.

Options considered:

| Option | Outcome |
| --- | --- |
| Tell Claude to update session/tracker after each write | Rejected because the manual smoke showed documentation alone is not enough. |
| Make the original mutation tool update tracking automatically | Rejected because the tool payload often lacks the human-readable note/handler needed for useful S:W:H:E entries. |
| Block all mutation until a separate log command records the previous mutation | Chosen because it makes the missing tracking visible and forces an explicit, auditable note before more work continues. |

Rationale: the Aegis workflow must be a runtime system, not a reminder. The gate now enforces both sides of the loop: readiness before mutation and S:W:H:E accountability after mutation.

## 2026-05-19 15:24 CEST - Make `aegis log` update the full workflow surface set

[S:20260519|W:task115-aegis-mcp-e2e-target-validation|H:aegis:workflow-surfaces|E:scripts/_aegis_installer.py]

Decision: extend `aegis log` so the default successful log updates `sessions/current`, the active `TRACKER.md`, `IMPLEMENTATION.md`, `CHANGELOG.md`, `HANDOFF.md`, and the current plan evidence row for `plan-step-implement`. Add repeated `--surface` options for `findings` and `decisions`, and add `--plan-step` / `--plan-status` so final verification can explicitly update `plan-step-verify`. Install a project-local `./.aegis/bin/aegis` shim so downstream Claude sessions have a stable invocation path even when the global console script is not on PATH.

Options considered:

| Option | Outcome |
| --- | --- |
| Keep `aegis log` limited to session/tracker | Rejected because target projects would still drift from this repository's workflow model. |
| Force agents to manually edit every workflow document after logging | Rejected because the point of Aegis is mechanical behavior, not reminders. |
| Make the log command update the core workflow surfaces and allow explicit findings/decisions surfaces | Chosen because it gives every mutation a consistent implementation/changelog/handoff/plan trail while preserving intentional finding/decision entries. |

Rationale: installed projects should behave like this project. A single enforced logging command should move the workflow forward across the same surfaces, not leave follow-up document edits to agent memory.

## 2026-05-19 16:07 CEST - Treat `/dev/null` redirects as non-persistent and make pending logs strict

[S:20260519|W:task115-aegis-mcp-e2e-target-validation|H:aegis:tracking-hardening|E:.claude/scripts/gate_lib.py]

Decision: refine Bash mutation detection so redirects to `/dev/null` are not classified as persistent mutations by themselves, and skip shell variable assignments when deriving the pending-event handler. Also make `aegis log` refuse non-matching evidence whenever pending tracking exists, before it writes any workflow surfaces.

Rationale: the runtime needs to distinguish real persistent mutations from read-only verification commands with stderr suppression. The log command also needs to be transactional from the agent's perspective: either it clears the pending event it is meant to clear, or it fails loudly without creating misleading workflow entries.
