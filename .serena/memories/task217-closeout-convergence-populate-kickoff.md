# Task 217 — closeout convergence populate-step kickoff

Date: 2026-07-06
Branch: feat/task-217-closeout-convergence-populate

Context:
- PR #240 merged the capsule resume-drift gate docs/backlog update into main at 327a5a5.
- Stale Task 190 work-tracking folder was archived via `python3 scripts/codex-task work-tracking archive --folder 20260616-task190-prd-bootstrap-flow-ACTIVE` to `docs/ai/work-tracking/archive/20260616-task190-prd-bootstrap-flow-COMPLETED`.
- New Task 217 kickoff succeeded via `python3 scripts/codex-task wizard kickoff --task 217 --slug closeout-convergence-populate ...`.
- Readiness now reports `READY | task=217`.

Task 217 scope:
- Optional enhancement for one-shot closeout convergence in non-canonical usage.
- Must preserve adversarial constraints: populate only from logged implement/verify rows, never synthesize strict verify without green report, surgical handoff repair, pending-drain evidence normalization guard, and strict read-only dry-run.

Immediate next step:
- Inspect Task 216 decisions/tests and current closeout/handoff implementation before editing code.