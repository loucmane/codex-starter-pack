# Task 251 advisory pending closeout

- Branch: `feat/task-251-aegis-advisory-pending-closeout` in isolated worktree `/tmp/codex-task251-advisory-closeout`.
- Purpose: fix the upstream Aegis contradiction exposed by Blog Task 40, where advisory-only pending events are passive evidence but strict delivery verification and closeout currently require an empty queue.
- Contract: one fail-closed provenance classifier shared by status, verify, closeout, closeout readiness, doctor, next guidance, and repair guidance.
- Advisory-only queues must be preserved, counted, sampled within output budgets, and allowed through delivery. Required, mixed, malformed, missing-provenance, and unknown-mode state must fail closed.
- Dry-run closeout must remain non-mutating. Neither generic repair nor manual pending-event draining is part of normal advisory delivery.
- Blog is a downstream fixture only. Do not inspect or mutate `/home/loucmane/dev/blog`; rollout waits for the upstream merge and a separate attended approval.
- Gas Town migration and Taskmaster retirement are explicitly deferred until the owner authorizes them at a sensible stopping point.
- Scope evidence: `docs/ai/work-tracking/active/20260714-task251-aegis-advisory-pending-closeout-ACTIVE/designs/wizard-flow.md`.
- Protected primary-worktree drift remains out of scope; implementation stays in the isolated Task 251 worktree.
