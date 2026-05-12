# Change Advisory Packet

- Label: task-44-change-advisory-helper-implementation
- Created at: 2026-05-12T18:56:01+02:00
- Mode: non-destructive-change-advisory-packet
- Executes actions: False
- Summary: Task 44 change advisory helper implementation
- Task ID: 44

## Change Scope

- `scripts/codex-task`
- `tests/meta_workflow_guard/test_codex_task.py`

## Governance Assessment

- Review class: coordinated
- Risk level: medium
- Priority: 20
- Required roles: template_owner, foundation_maintainer
- Approval guidance: Template-owner and foundation-maintainer acknowledgement recorded in work tracking.
- Escalation guidance: Escalate to breaking review if compatibility or migration risk is identified.
- Notification mode: evidence-only
- Notification audiences: active work-tracking folder, task handoff

Reasons:
- manual_review_class: coordinated -> coordinated: Review class explicitly supplied as coordinated

## Current State Snapshot

- Branch: feat/task-44-change-advisory-board-process
- HEAD: b9b3f7f8525f6b5a4c44da9979f6e577785d1850
- Dirty status entries: 11
- Current session: sessions/2026/05/2026-05-12-004-task44-change-advisory-board-process.md
- Current plan: plans/2026-05-12-task44-change-advisory-board-process.md
- Active work-tracking folders: ['docs/ai/work-tracking/active/20260512-task44-change-advisory-board-process-ACTIVE']

## Required Evidence

- FINDINGS.md impact note
- DECISIONS.md rationale
- IMPLEMENTATION.md summary
- guard and focused test evidence
- active session progress entry with S:W:H:E evidence
- active tracker progress entry with S:W:H:E evidence
- plan sync evidence
- work-tracking audit evidence
- Taskmaster health evidence
- guard evidence
- focused or full pytest evidence appropriate to the change
- git diff --check evidence
- communication payload or handoff note for listed notification audiences

## Advisory Controls

- Record the advisory packet path in the active tracker and session log.
- Record approval/rationale in DECISIONS.md or the active session before merge.
- Keep notification mode evidence-only; do not send external notifications from this helper.
- Reference final evidence from HANDOFF.md before closing the task.
- Record communication guidance for the active work-tracking folder and task handoff.

## Communication Guidance

- Use repository communication templates and active work-tracking evidence.
- Record communication payloads or summaries as evidence; do not send notifications from this helper.
- Include Taskmaster ID, branch, advisory packet path, guard/test evidence, and merge/rollback guidance when relevant.

## Recommended Verification Commands

- `python3 scripts/codex-task change advisory --summary <summary> --report-file <advisory.json> --runbook-file <advisory.md>`
- `python3 scripts/codex-task plan sync`
- `python3 scripts/codex-task work-tracking audit`
- `python3 scripts/codex-task taskmaster health`
- `python3 scripts/codex-guard validate --include-untracked`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest`
- `git diff --check`
- `Review Task 49 communication templates and record evidence-only communication guidance.`

## Post-Implementation Review

- What changed compared with the approved advisory packet?
- Which guard, test, audit, health, and validation evidence proves the change behaved as expected?
- Were any approval, communication, rollback, canary, emergency, or validation conditions missed?
- Did any policy-only or manual step need a follow-up task?
- What should be changed in the portable foundation before the next similar change?

## Non-Goals

- No CAB meeting is scheduled.
- No stakeholder vote is requested or recorded by this helper.
- No approval is granted automatically.
- No external notification is sent.
- No dashboard, ticket, or external tracking system is created.
- No deployment, promotion, rollback, reset, cleanup, or branch-protection change is executed.
- No duplicate governance policy is created.

No CAB meeting, approval, notification, dashboard update, deployment, rollback, reset, cleanup, or external tracking action was executed by this advisory packet.
