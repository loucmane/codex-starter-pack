# Decisions

- 2026-04-22 — Keep Task 92 focused on real workflow-guard coverage rather than expanding it to absorb the entire cross-project foundation agenda.
- 2026-04-22 — Add explicit follow-on Tasks `98`–`102` for the portability roadmap so repo-structure config, foundation spec, bootstrap/adoption, cross-project fixtures, and migration guidance become visible backlog work.
- 2026-04-22 — Treat the kickoff scope comparison plus roadmap-to-backlog alignment as enough evidence to complete `plan-step-scope`; do not leave the scope step pending once guard-facing audit work is already finished.
- 2026-04-22 — Prioritize runtime-artifact protection and Taskmaster-evidence enforcement as the first Task 92 implementation slice because they address recent, repeated workflow failures with relatively contained guard changes.
- 2026-04-23 — Treat interrupted prior-day sessions as recovered sessions, not normal same-day endings. Record the interruption in the prior session, then start a new dated session for current-day work.
- 2026-04-23 — Keep Task 92 open after `92.3`; documentation closeout and final regression evidence remain separate subtasks (`92.4`, `92.5`) rather than being collapsed into implementation.
- 2026-04-23 — Mark Task 92 done once documentation and final regression evidence are stored; broader portability and foundation work belongs to follow-on Tasks `98` through `102`, not additional Task 92 scope.
- 2026-04-23 — Fix the failed PR check with a follow-up Task 92 commit rather than rerunning CI unchanged: remove tracked bytecode from git, ignore Python bytecode going forward, sync the active plan inside guard workflows, and read the PR branch from GitHub Actions environment variables.
