# Task 250 — Evidence-gated autonomous delivery executor stability

## Current state

- Task 250 is active on `feat/task-250-autonomous-delivery-stability` in the isolated worktree `/tmp/codex-task250-autonomous-delivery-stability`.
- PR #275 merged normally as `d7ffce5eff8df92d08def1e4e2b7aeef2860a81d`; primary `main` is synchronized and its unrelated local `.codex`, `.agents`, and `.aegis` drift remains untouched.
- PR #276 is open and green but intentionally unmerged. Its trusted merge executor reproduced a self-gating loop twice: the running non-required `policy-authorized merge` check leaves GitHub mergeability `unstable`, so the old clean-only executor can never authorize itself.

## Selected design

- Keep default evaluator `blocked`/`unstable` results non-authorizing.
- Permit executor-phase `allow` only when complete exact-head check and legacy-status inventories prove every independent signal green and identify exactly the current trusted GitHub Actions executor run as the sole non-green check.
- Bind the exception to check name, GitHub App slug, repository Actions URL, current run ID, non-completed status, and exact head SHA.
- Recollect all volatile PR/workflow/check/status/review evidence and re-evaluate immediately before the normal protected SHA-pinned squash merge.
- Preserve attended-path, same-repository, exact-head, review-thread, complete-inventory, protected-path, and required-workflow gates.

## Evidence so far

- Sanitized PR #276 telemetry fixture added.
- Focused adversarial policy/workflow suite: 72 passed.
- Wider affected source/guard/Codex/policy suite: 388 passed.
- Ruff lint/format, source/package policy parity, Taskmaster health, dependency validation, plan sync, and template drift pass.
- Task 249 is `done`; its 12 terminal files match signed closeout commit `955385929fc0d96285c741bdfe2c6e5e0b97dea6` byte-for-byte and are included through supported archival so Task 250 is the sole ACTIVE work authority.

## Next steps

1. Rerun work-tracking audit and source guard after logging this memory in the tracker/session.
2. Run the broader and full repository verification matrix, action/workflow validation available locally, source/package parity, and diff checks.
3. Complete Task 250 evidence, sign and publish its governance PR, and validate hosted CI.
4. After the attended governance merge, prove an ordinary autonomous canary plus exact-merge-SHA dispatch.
5. Close PR #276 as superseded only after that proof and verify Task 249 terminal on synchronized `main`.
