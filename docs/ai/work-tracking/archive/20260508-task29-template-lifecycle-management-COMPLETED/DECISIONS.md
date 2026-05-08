# Decisions

- 2026-05-08 — Implement Task 29 as a portable lifecycle policy and audit helper instead of a broad template-file archival system.
- 2026-05-08 — Keep lifecycle behavior non-destructive: audits may recommend warnings or archival, but this task will not move template files automatically.
- 2026-05-08 — Preserve current compatibility statuses (`beta`, `experimental`) by mapping them to canonical lifecycle phases instead of declaring them invalid without a separate migration.
- 2026-05-08 — Treat full version history and rollback as out of scope for Task 29 because Task 58 owns robust template versioning later.
- 2026-05-08 — Treat `status: modular` as an ignored aggregate status in the lifecycle policy; it is not a template lifecycle state and should not appear in governed template files.
- 2026-05-08 — Close Taskmaster Task 29 after evidence passes; keep work-tracking active until the PR is merged, then archive it as a separate workflow closeout commit.
