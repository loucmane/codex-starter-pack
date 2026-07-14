# Decisions

- 2026-07-14 — Do not manually merge PR #276 or broaden `provisional`; repair the trusted executor through Task 250 and preserve the normal protected evidence path.
- 2026-07-14 — Keep evaluator and executor semantics distinct. Evaluator `blocked`/`unstable` remains non-authorizing; executor may return `allow` only after current-run self binding and complete green independent evidence.
- 2026-07-14 — Ignore only trusted GitHub Actions checks named `policy-authorized merge`; a matching current run must still be queued/in progress, so completed failures cannot impersonate live executor state.
- 2026-07-14 — Re-evaluate current PR, workflow, check, status, and review evidence immediately before merge rather than relying on the first executor snapshot.
- 2026-07-14 — Fold Task 249's already-reviewed terminal projection into Task 250 rather than bypassing the source guard. The exact files from signed closeout commit `9553859` are preserved byte-for-byte, Task 249 remains `done`, Task 250 remains the sole ACTIVE authority, and PR #276 will be superseded only after Task 250 proves the repaired autonomous path.
- 2026-07-14 — Do not manually merge canary PR #278 after its fail-closed denial. Treat the denial as Task 250 acceptance evidence and remediate the executor model through a separate attended governance PR.
- 2026-07-14 — Validate the current executor from the trusted Actions run/jobs APIs, not from candidate checks. Keep candidate checks/statuses as an independent complete-green requirement, and bind `pull_request_target` to candidate metadata while binding `workflow_run` to the current trusted default branch.
