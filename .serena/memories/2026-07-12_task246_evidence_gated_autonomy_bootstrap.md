# Task 246 evidence-gated autonomy bootstrap

- Branch: `feat/task-246-evidence-gated-autonomy-bootstrap`.
- Purpose: restore completed-source validation on taskless `main` and replace repeated Aegis chat approvals with a persistent tracked evidence-gated authority policy.
- Main derivation: valid active policy plus contained `plans/current` and `sessions/current`, Taskmaster done state, and exactly one completed archive must agree.
- Routine authority: valid active evidence-gated mode explicitly enables supported Taskmaster transitions, deterministic safe repair, verified closeout, commit/push/PR, and CI remediation. Attended, invalid, revoked, disabled, or manual-review cases still require an owner.
- Delivery: trusted default-branch workflow gathers complete exact-head GitHub evidence, executes only protected policy code, and squash-merges only `allow`; authority/workflow/security/high-risk paths remain attended.
- Post-merge: CI, Codex Guard, and Meta Workflow Guard accept exact-merge-SHA `repository_dispatch` so a workflow-token merge still receives main validation.
- Compatibility: missing/invalid/revoked policy remains attended; advisory enforcement and legacy S:W:H:E scaffolding remain intact.
- Verification: final full repository suite passed 1,831 with four documented opt-in smoke skips; 455 targeted regressions and 88 post-extension focused tests passed; Ruff, Taskmaster health, plan sync, work-tracking audit, guard, policy validation, live policy status, and asset parity passed.
- Remaining: mark Task 246 done, archive through supported paths, commit/push/open draft PR, remediate hosted CI. The bootstrap PR remains the final attended merge boundary.