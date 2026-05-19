# Findings

- 2026-05-18 — _Pending_ — document new findings here.
- 2026-05-19 — [S:20260519|W:task115-aegis-mcp-e2e-target-validation|H:codex-guard|E:docs/ai/work-tracking/active/20260518-task115-aegis-mcp-e2e-target-validation-ACTIVE/reports/aegis-mcp-e2e-target-validation/guard-2026-05-19-final.txt] Current-day guard remediation confirmed that multi-day work requires a fresh daily session and today-dated tracking entries while reusing the active task folder.

## 2026-05-18 14:19 CEST - Real target-project validation gap

[S:20260518|W:task115-aegis-mcp-e2e-target-validation|H:review-gap|E:tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py]

The first Task 115 implementation created useful generated pytest target shapes, but it did not fully match the intended "try the MCP in real local projects" standard. It generated Python, web, backend, docs-heavy, partial, and conflict fixtures under pytest temp directories and called the MCP in-process, but it did not create concrete new and already-started Python/web/backend project trees and drive the packaged MCP flow against them as a user-facing install smoke.

Impact: keep the generated fixture layer, but add a second layer that proves the real local target-project workflow before Task 115 is considered complete.

## 2026-05-18 15:25 CEST - Manual Claude cold-session enforcement smoke passed

[S:20260518|W:task115-aegis-mcp-e2e-target-validation|H:manual-claude-smoke|E:/tmp/aegis-manual-targets-ZUa76T/targets/python-started]

After installing Aegis into copied Python/web/backend target projects, a real Claude session launched inside `python-started` picked up the installed `.claude/settings.json` hook. In cold-session state on `main`, readiness returned `BLOCKED`; Claude reported that mutation was not allowed; a `Write` attempt, a Bash redirect attempt, and an `Edit` attempt against `CLAUDE.md` were all refused by `.claude/scripts/pretooluse-gate.sh`.

Remaining gap: this proves installed cold-session enforcement, but it does not prove an installed target project has a complete project-local path from `BLOCKED` to `READY`. That kickoff/READY path must be handled before treating Aegis as fully usable by new downstream projects.

## 2026-05-18 15:28 CEST - Positive READY path missing in installed target

[S:20260518|W:task115-aegis-mcp-e2e-target-validation|H:manual-positive-path-check|E:/tmp/aegis-manual-targets-ZUa76T/targets/python-started]

The installed target project contains Aegis gate files and Claude hooks, but it does not contain `plans/`, `sessions/`, `docs/ai/work-tracking/`, `.taskmaster/`, or a project-local kickoff command. The installed `aegis` CLI exposes inspect, plan-install, status, install, verify, list-profiles, and explain-profile only. Therefore the current installed project can block unsafe Claude mutations, but it does not yet provide the expected positive path that creates workflow scaffolding and transitions Claude readiness from `BLOCKED` to `READY`.

Impact: Task 115 remains in progress. A release-readiness claim must include the positive installed-project workflow path, not just cold-session refusal.

## 2026-05-18 16:12 CEST - Taskmaster and Serena must be optional, not readiness dependencies

[S:20260518|W:task115-aegis-mcp-e2e-target-validation|H:architecture-gap|E:aegis_foundation/assets/.claude/scripts/readiness.sh]

The installed runtime was still carrying this source repo's workflow assumption: readiness expected a Taskmaster task file, current session, current plan, and active tracker. That makes sense inside this repository, but it prevents Aegis from being a portable foundation for a new Python app, web app, backend service, game, or any project that has not adopted Taskmaster or Serena.

Impact: Aegis now needs an internal portable task/work state. Taskmaster can be validated when explicitly required, and Serena can be used for continuity when available, but neither can be required for an installed project to reach `READY`.

## 2026-05-18 16:12 CEST - Aegis-native kickoff closes the positive READY path

[S:20260518|W:task115-aegis-mcp-e2e-target-validation|H:pytest:aegis-native-ready|E:docs/ai/work-tracking/active/20260518-task115-aegis-mcp-e2e-target-validation-ACTIVE/reports/aegis-mcp-e2e-target-validation/tests-2026-05-18-aegis-native-ready.txt]

`aegis kickoff` now creates a task branch, `.aegis/state/current-work.json`, `sessions/current`, `plans/current`, and an active work-tracking folder with plan/tracker alignment. Installed readiness accepts that Aegis-native state when `.taskmaster/` is absent. The focused regression proves the installed project can move from cold-session `BLOCKED` to `READY` without `.taskmaster/` or `.serena/`.

Impact: Task 115 now tests both sides of usability: cold-session mutation refusal and positive workflow bootstrap.

## 2026-05-18 16:35 CEST - Presence is not the same as dependency

[S:20260518|W:task115-aegis-mcp-e2e-target-validation|H:claude:readiness|E:tests/claude_adapter/test_readiness_gate.py]

The first Aegis-native readiness fallback still had a portability edge case: if `.taskmaster/tasks/tasks.json` existed, readiness preferred Taskmaster and required the matching task to be in progress. That works for this source repository, but it means an installed project with stale or unused Taskmaster files could be blocked even though Aegis current-work is valid.

Impact: readiness now prefers Aegis current-work when present. Taskmaster strictness is opt-in through `integrations.taskmaster.required: true`, so Aegis can be consistent across projects that have Taskmaster, used to have Taskmaster, or never installed it.

## 2026-05-18 17:19 CEST - Negative-only installed tests were insufficient

[S:20260518|W:task115-aegis-mcp-e2e-target-validation|H:pytest:installed-target-runtime-matrix|E:docs/ai/work-tracking/active/20260518-task115-aegis-mcp-e2e-target-validation-ACTIVE/reports/aegis-mcp-e2e-target-validation/tests-2026-05-18-installed-target-runtime-matrix.txt]

The manual Claude smoke and earlier focused tests proved that the installed hook blocks invalid mutation, but they did not fully prove the normal user path across representative projects. A complete target-project test must prove both halves: cold-session refusal and a valid bootstrap path to READY with allowed task-scoped mutation.

Impact: the MCP target test suite now runs a default, non-env-gated matrix across `python-new`, `python-started`, `web-new`, `web-started`, `backend-new`, and `backend-started`. Each copied project is installed through MCP, verified to contain the generated Aegis/Claude runtime files, blocked on `main`, allowed to bootstrap only through `aegis kickoff`, scaffolded through the actual CLI kickoff path, moved to `READY`, allowed to write task output, blocked from protected Codex paths, and checked for original file preservation.

## 2026-05-18 20:59 CEST - Thin scaffold still did not reproduce the workflow

[S:20260518|W:task115-aegis-mcp-e2e-target-validation|H:user-review|E:templates/aegis/workflow/]

The Aegis kickoff path created the expected paths, but its document bodies were still thin and hardcoded. That meant a target project could technically become `READY`, but it did not receive the same practical workflow model this repository uses: a structured session with validation and progress log, a plan with frontmatter/plan table/evidence checklist, tracker with plan compliance, and separate findings/decisions/implementation/changelog/handoff surfaces.

Impact: file existence is not enough. The MCP must create a usable workflow system in the target project. Task 115 now includes subtask `115.9`, and the installed-target tests assert content sections and packaged workflow templates rather than only checking that files exist.

## 2026-05-19 12:11 CEST - Multi-day continuation must use a fresh session while preserving task scope

[S:20260519|W:task115-aegis-mcp-e2e-target-validation|H:codex-guard|E:docs/ai/work-tracking/active/20260518-task115-aegis-mcp-e2e-target-validation-ACTIVE/reports/aegis-mcp-e2e-target-validation/guard-2026-05-19-final.txt]

The workflow scaffold work crossed a date boundary. The correct model is a new daily session (`sessions/2026/05/2026-05-19-001-task115-aegis-mcp-e2e-target-validation.md`) with the existing Task 115 plan and active work-tracking folder reused. Editing the previous May 18 session after the date rollover caused guard to fail, which is the intended protection.

Impact: current-day progress belongs in the May 19 session and the existing task-scoped tracker. Historical session files should only contain their own day’s entries.

## 2026-05-19 14:00 CEST - READY task output still needed mechanical tracking

[S:20260519|W:task115-aegis-mcp-e2e-target-validation|H:manual-smoke-gap|E:docs/ai/work-tracking/active/20260518-task115-aegis-mcp-e2e-target-validation-ACTIVE/reports/aegis-mcp-e2e-target-validation/manual-mcp-workflow-smoke-2026-05-19.txt]

The manual Claude smoke in an Aegis-installed target project proved that install, kickoff, readiness, allowed task output, and protected-path refusal worked. It also exposed that a successful READY write could happen without a mandatory update to `sessions/current` or the active `TRACKER.md`. That repeated the original reliability problem in a smaller form: the system depended on the agent remembering to log work after the gate allowed a mutation.

Impact: Aegis now needs a post-mutation tracking gate, not just a pre-mutation readiness gate. Successful hookable mutations must create pending tracking state, and the runtime must block the next mutation and Stop until the agent records an S:W:H:E entry.

## 2026-05-19 14:55 CEST - Live Claude confirmed tracking enforcement and exposed CLI discoverability gap

[S:20260519|W:task115-aegis-mcp-e2e-target-validation|H:live-claude-smoke|E:docs/ai/work-tracking/active/20260518-task115-aegis-mcp-e2e-target-validation-ACTIVE/reports/aegis-mcp-e2e-target-validation/live-claude-post-mutation-tracking-smoke-2026-05-19.txt]

The live Claude session in `/tmp/aegis-live-workflow-test-eqo84Nr6/shop-webapp` followed the intended runtime loop. Claude reached `READY`, wrote a task-scoped report file, observed pending tracking, was blocked from a second write, logged the first write, verified session/tracker entries, wrote a second file, and was then blocked by Stop until the second write was logged. This proves the actual Claude hook path uses the PostToolUse/PreToolUse/Stop enforcement as intended.

The same run exposed a portability gap: `aegis` was not on PATH inside the installed target project. Claude had to find and use `/home/loucmane/codex/.venv/bin/aegis`, which is source-checkout-specific and not acceptable as the default downstream user experience.

Impact: tracking enforcement works, but Aegis install should make `aegis log` discoverable in target projects through a project-local wrapper, manifest-backed command, or documented package invocation that does not require source checkout knowledge.

## 2026-05-19 15:24 CEST - Session/tracker-only logging is still not the full workflow

[S:20260519|W:task115-aegis-mcp-e2e-target-validation|H:live-claude-smoke-review|E:docs/ai/work-tracking/active/20260518-task115-aegis-mcp-e2e-target-validation-ACTIVE/reports/aegis-mcp-e2e-target-validation/live-claude-post-mutation-tracking-smoke-2026-05-19.txt]

The live Claude smoke proved that pending tracking forced Claude to run `aegis log`, and the command correctly updated `sessions/current` and `TRACKER.md`. User review caught the next gap: this repository's workflow does not stop at those two files. Meaningful work is also reflected in implementation notes, changelog, handoff, and plan evidence, with findings/decisions updated when applicable.

Impact: Aegis needs full workflow-surface accountability. Installed projects should not end up with a fresh session/tracker entry while `IMPLEMENTATION.md`, `CHANGELOG.md`, `HANDOFF.md`, and the active plan remain stale.

## 2026-05-19 16:07 CEST - Read-only Bash verification must not become pending tracking

[S:20260519|W:task115-aegis-mcp-e2e-target-validation|H:live-claude-smoke-review|E:/tmp/aegis-full-workflow-live-test-CK1vZR/shop-webapp]

The full workflow-surface retest passed the core behavior, but the read-only verification loop used by Claude included a harmless stderr redirect to `/dev/null`. The Bash classifier treated any `>` target as a persistent mutation, so the PostToolUse hook recorded a pending event with evidence `/dev/null` and a handler derived from the shell variable assignment.

Impact: read-only verification must be safe after logging. Otherwise the act of checking session/tracker/plan surfaces can create a new pending event and mask the protected-path guard in the next test.

## 2026-05-19 16:07 CEST - Non-matching log evidence should fail before writing workflow surfaces

[S:20260519|W:task115-aegis-mcp-e2e-target-validation|H:aegis:log-hardening|E:scripts/_aegis_installer.py]

The same live retest showed that `aegis log` accepted a log entry whose evidence did not match the pending event. The command wrote all workflow surfaces but left pending tracking uncleared, which can make an agent think it did the required thing while the Stop hook still blocks.

Impact: when pending tracking exists, `aegis log` must be strict. If the evidence does not match a pending event, the command now fails before writing session, tracker, implementation, changelog, handoff, or plan evidence.



## Progress Log

- **2026-05-18 13:38** — [S:20260518|W:task115-aegis-mcp-e2e-target-validation|H:pytest:mcp-e2e-targets|E:docs/ai/work-tracking/active/20260518-task115-aegis-mcp-e2e-target-validation-ACTIVE/reports/aegis-mcp-e2e-target-validation/tests-2026-05-18-mcp-e2e-targets.txt] Local MCP E2E tests now prove generated project installs and safety refusal before GitHub release artifact work.
- **2026-05-18 13:47** — Local target validation closes the main gap after Task 114: the MCP can install and verify Aegis in representative generated target projects, while conflict and partial states remain structured and non-destructive.
