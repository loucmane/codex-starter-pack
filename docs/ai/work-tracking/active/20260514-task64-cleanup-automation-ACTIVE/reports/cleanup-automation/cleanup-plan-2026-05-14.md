# Cleanup Automation Planning Packet

- Label: cleanup-automation
- Created at: 2026-05-14T17:04:04+02:00
- Mode: static-non-destructive-cleanup-planning-packet
- Executes actions: False
- Aggregate status: ready

## Current State Snapshot

- Branch: `feat/task-64-cleanup-automation`
- HEAD: `7902a1012c3e9522489078360cd5800a899207fc`
- Dirty status entries: 13
- Current session: `sessions/2026/05/2026-05-14-007-task64-cleanup-automation.md`
- Current plan: `plans/2026-05-14-task64-cleanup-automation.md`
- Active work-tracking folders: ['docs/ai/work-tracking/active/20260514-task64-cleanup-automation-ACTIVE']

## Summary

- Total domains: 6
- Ready: 6
- Needs evidence: 0
- Blocked: 0

## Evidence Domains

| Domain | Purpose | Status | Missing Evidence |
| --- | --- | --- | --- |
| Taskmaster cleanup health | Confirm cleanup follow-up work can be tracked without dependency corruption. | `ready` | None |
| Scanner cleanup evidence | Use generated scanner/duplicate/reference data as cleanup candidate evidence. | `ready` | None |
| Reference-fix safety tools | Confirm dry-run, backup, and rollback tooling exists for reference cleanup. | `ready` | None |
| Deprecation lifecycle review | Use lifecycle/deprecation evidence before deciding archive or removal candidates. | `ready` | None |
| Rollback and emergency policy | Require recovery context before risky cleanup work. | `ready` | None |
| Legacy cleanup example | Ground cleanup planning in the scoped Task 108 legacy PROJECT-BLOG cleanup precedent. | `ready` | None |

## Cleanup Candidates

| Candidate | Risk | Evidence Domain | Manual Action | Approval Required |
| --- | --- | --- | --- | --- |
| Scanner-generated cleanup artifacts | `medium` | `scanner-cleanup-evidence` | Review generated duplicate/reference outputs and archive only explicitly approved stale artifacts. | True |
| Reference-fix backup directories | `medium` | `reference-fix-safety` | Review backup age and restore value before pruning or archiving backup directories. | True |
| Deprecated template candidates | `high` | `deprecation-lifecycle` | Use deprecation review status before archive/removal decisions; create a scoped cleanup task for each accepted change. | True |
| Legacy PROJECT-BLOG cleanup precedent | `low` | `legacy-cleanup-example` | Reuse the Task 108 pattern: isolate one legacy finding, apply the smallest change, and verify scanners/guard. | True |
| Active workflow state cleanup | `high` | `taskmaster-cleanup-health` | Never clear active session, plan, or work-tracking pointers except during post-merge archive closeout. | True |

## Approval Gates

- `scope`: A Taskmaster task and work-tracking folder explicitly name the cleanup target and allowed operation.
- `dry_run`: Scanner, duplicate, reference-fix, or command dry-run evidence exists before any mutation is proposed.
- `backup`: A backup, archive, or restore path is documented before deleting or rewriting generated artifacts.
- `rollback`: A rollback checkpoint or recovery plan exists for any multi-file cleanup.
- `review`: The user approves the exact cleanup command or patch after reviewing evidence.
- `verification`: Guard, tests, audit, Taskmaster health, and diff-check pass after cleanup.

## Dry-Run Checks

- **scanner-output-review**: `python3 scripts/template-ssot-scanner/run_all_scanners.py --help` - Confirm scanner command surface before using generated cleanup data.
- **reference-fix-preview**: `python3 scripts/template-ssot-scanner/apply_reference_fixes.py --dry-run --fixes scripts/template-ssot-scanner/output/data/fix_recommendations.json` - Preview reference-fix candidates without writing files.
- **work-tracking-audit**: `python3 scripts/codex-task work-tracking audit` - Confirm active/archive state before moving work-tracking folders.
- **guard-validation**: `python3 scripts/codex-guard validate --include-untracked` - Confirm cleanup planning does not break workflow evidence.

## Backup And Rollback Guidance

- Capture `python3 scripts/codex-task rollback checkpoint` before risky multi-file cleanup.
- Use `python3 scripts/codex-task rollback plan` to render recovery guidance from the checkpoint.
- Prefer targeted `git restore -- <path>` only after review; never use `git reset --hard` as a default cleanup path.
- Keep scanner backup directories until the related PR is merged and the archive commit is pushed.

## Metrics Checklist

- `candidate_count`: How many cleanup candidates are proposed by scanner, lifecycle, or historical evidence?
- `missing_evidence_count`: How many candidates lack source evidence or dry-run output?
- `risk_mix`: How many candidates are low, medium, high, or destructive-risk?
- `approval_coverage`: Do all candidates have scope, dry-run, backup, rollback, review, and verification gates?
- `rollback_coverage`: Which candidates have rollback checkpoint or restore guidance?
- `post_cleanup_health`: Will guard, tests, audit, Taskmaster health, and diff-check be captured after cleanup?

## Manual Notification Guidance

- Use communication templates to draft cleanup notices when stakeholders need review.
- Do not send notifications from this command; record draft or decision in work tracking.
- Mention exact candidate IDs, evidence paths, and verification commands in any PR description.

## Planning Guidance

- Treat this packet as a cleanup review contract; a human must approve every cleanup action separately.
- Run dry-run scanners and capture rollback context before any cleanup implementation task.
- Keep candidate rows advisory until an explicit Taskmaster task scopes the exact file operation.
- Prefer archive or rewrite decisions over deletion when historical evidence may still be useful.

## Recommended Refresh Commands

- `python3 scripts/codex-task taskmaster health`
- `python3 scripts/template-ssot-scanner/run_all_scanners.py`
- `python3 scripts/template-ssot-scanner/apply_reference_fixes.py --help`
- `python3 scripts/codex-task deprecation review --report-file reports/deprecation-management/latest.json --runbook-file reports/deprecation-management/latest.md`
- `python3 scripts/codex-task rollback checkpoint --label cleanup-review --report-file reports/cleanup-automation/rollback-checkpoint.json`
- `python3 scripts/codex-guard validate --include-untracked`
- `python3 scripts/codex-task cleanup plan --report-file reports/cleanup-automation/latest.json --runbook-file reports/cleanup-automation/latest.md`
- `python3 scripts/codex-task work-tracking audit`

## Non-Goals

- No cron job, scheduler, daemon, GitHub scheduled workflow, background cleanup service, or long-running process is installed.
- No file is deleted, moved, archived, restored, rolled back, cleaned, reset, or modified by this command.
- No `git clean`, `git reset`, destructive restore, branch deletion, retention enforcement, or automatic cleanup approval is executed.
- No backup is created or restored; backup and rollback guidance is advisory only.
- No email, chat, webhook, ticket, stakeholder notification, or external service call is sent.
- No source report, scanner output, template, Taskmaster, session, plan, work-tracking, Git, or external state is mutated beyond requested cleanup planning artifacts.

This packet is a static cleanup planning artifact. It composes existing repository evidence and requested output files only; it does not install schedulers, delete files, move files, create backups, run rollback, send notifications, or contact external systems.
