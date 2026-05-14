# Feedback Collection Planning Packet

- Label: feedback-collection
- Created at: 2026-05-14T16:26:51+02:00
- Mode: static-feedback-collection-planning-packet
- Executes actions: False
- Aggregate status: ready

## Current State Snapshot

- Branch: `feat/task-59-feedback-collection-system`
- HEAD: `3e36df7683b5d10b75d7468704fa8461115dba72`
- Dirty status entries: 14
- Current session: `sessions/2026/05/2026-05-14-006-task59-feedback-collection-system.md`
- Current plan: `plans/2026-05-14-task59-feedback-collection-system.md`
- Active work-tracking folders: ['docs/ai/work-tracking/active/20260514-task59-feedback-collection-system-ACTIVE']

## Summary

- Total domains: 5
- Ready: 5
- Needs evidence: 0
- Blocked: 0

## Evidence Domains

| Domain | Purpose | Status | Missing Evidence |
| --- | --- | --- | --- |
| Taskmaster follow-up health | Confirm feedback can become scoped follow-up work without dependency corruption. | `ready` | None |
| Communication feedback template | Provide repository-native wording for feedback and follow-up capture. | `ready` | None |
| Onboarding feedback guidance | Confirm training guidance tells operators where feedback belongs. | `ready` | None |
| Phase 4 feedback guidance | Reuse documentation delivery guidance that treats feedback as repo evidence and follow-up prompts. | `ready` | None |
| Stakeholder response context | Ground response and routing guidance in stakeholder-safe status reporting. | `ready` | None |

## Intake Schema

| Field | Required | Purpose |
| --- | --- | --- |
| `source` | yes | Who or what produced the feedback, e.g. user, PR review, smoke test, CI run, session observation. |
| `observation` | yes | Specific behavior, gap, friction point, or request, quoted when possible. |
| `category` | yes | Repository-native feedback category used by the routing matrix. |
| `severity` | yes | Manual severity label: blocker, high, medium, low, or informational. |
| `sentiment` | yes | Manual sentiment label: positive, neutral, concern, or blocker. This is human-reviewed, not machine-inferred. |
| `evidence_path` | yes | Repository path containing supporting context, such as FINDINGS.md, HANDOFF.md, a report file, or a PR review link recorded in the tracker. |
| `desired_outcome` | no | What should change if the feedback is accepted. |
| `follow_up_task` | no | Existing or new Taskmaster task when the feedback requires scoped implementation. |
| `response_needed` | yes | Whether a human response is needed before closing the feedback item. |

## Categories

- **Documentation feedback** (`documentation`): Docs, guides, examples, onboarding, or wording gaps.
- **Workflow feedback** (`workflow`): Session, plan, work-tracking, Taskmaster, or GitHub process friction.
- **Guard and enforcement feedback** (`guard`): False positives, false negatives, bypasses, or missing tests.
- **Template feedback** (`template`): Template metadata, registry, portability, or reusable content gaps.
- **Agent compatibility feedback** (`agent`): Codex, Claude, Serena, MCP, or cross-agent runtime behavior.
- **Stakeholder and communication feedback** (`stakeholder`): Reporting, PR, announcement, milestone, or follow-up messaging.
- **Enhancement idea** (`enhancement`): Future improvement that needs prioritization before implementation.

## Manual Sentiment Labels

- `positive`: The feedback confirms a working behavior or useful outcome.
- `neutral`: The feedback is informational or requests clarification without risk.
- `concern`: The feedback identifies friction, uncertainty, or possible quality risk.
- `blocker`: The feedback identifies a workflow, safety, or correctness issue that should halt related work.

## Routing Matrix

| Category | Route To | Evidence Destination | Response Guidance |
| --- | --- | --- | --- |
| `documentation` | FINDINGS.md or a documentation Taskmaster follow-up | active work-tracking FINDINGS.md and affected docs path | Confirm whether the docs can be fixed inside the active task or need a follow-up task. |
| `workflow` | HANDOFF.md, DECISIONS.md, or Taskmaster workflow follow-up | session log, plan, tracker, and workflow evidence files | Document the workflow decision before changing process files. |
| `guard` | guard test issue or scoped guard task | guard output, pytest evidence, and reproducer command | Require a failing test or explicit non-enforceable limitation before implementation. |
| `template` | template metadata/registry follow-up | template path, registry path, and scanner output | Keep the change portable and registry-first. |
| `agent` | agent compatibility or runtime adapter follow-up | runtime contract, smoke-test report, MCP status, or agent-specific findings | Separate Codex-owned and Claude-owned surfaces before mutating files. |
| `stakeholder` | communication template or stakeholder report update | communication payload, stakeholder packet, or PR comment reference | Draft response text only; do not send external messages from this command. |
| `enhancement` | Phase 5 enhancement review or new Taskmaster task | Taskmaster task, enhancement packet, or DECISIONS.md | Prioritize before implementation and record non-goals. |

## Metrics Checklist

- `total_feedback_items`: How many feedback items were captured in repository evidence?
- `open_follow_ups`: How many items still need a scoped task, response, or decision?
- `severity_mix`: How many blocker/high/medium/low/informational items exist?
- `category_mix`: Which categories are generating the most friction or value?
- `task_coverage`: Do accepted implementation items have Taskmaster task IDs?
- `response_state`: Which items need human response before closeout?
- `archive_completeness`: Are closed items linked from work-tracking archive or final handoff evidence?

## Response Workflow

- `captured`: Feedback is recorded with source, observation, category, severity, sentiment, and evidence path.
- `triaged`: A human has reviewed routing, severity, and whether a response or task is needed.
- `accepted`: The feedback will be handled in the active task or a named follow-up task.
- `deferred`: The feedback is valid but intentionally parked with rationale and revisit trigger.
- `declined`: The feedback will not be acted on and the reason is recorded.
- `closed`: The response/action/evidence is complete and linked from final handoff or archive.

## Archive Guidance

- Store task-local feedback summaries in the active work-tracking FINDINGS.md, DECISIONS.md, HANDOFF.md, or reports directory.
- Link accepted implementation feedback to an existing or new Taskmaster task before editing product or workflow surfaces.
- Archive closed feedback with the work-tracking folder after the task PR merges.
- Keep private memory and external chats out of the evidence chain unless summarized into repository artifacts.

## Manual Next Steps

- Review the intake schema and routing matrix before collecting feedback.
- Capture feedback as repository evidence tied to an active task.
- Create or update Taskmaster tasks for accepted implementation feedback.
- Use communication templates for any human-facing response draft.
- Re-run this packet after major workflow, documentation, or stakeholder reporting changes.

## Planning Guidance

- Treat this packet as the review contract for capturing feedback as repository evidence, not as a live collection system.
- Record actual feedback in the active task's FINDINGS.md, HANDOFF.md, DECISIONS.md, report files, or a follow-up Taskmaster task.
- Use manual severity, sentiment, and routing review; do not infer intent or owner automatically.
- Refresh supporting communication, onboarding, documentation, stakeholder, and Taskmaster evidence before claiming feedback readiness.

## Recommended Refresh Commands

- `python3 scripts/codex-task taskmaster health`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/meta_workflow_guard/test_communication_templates.py`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/meta_workflow_guard/test_training_materials.py`
- `python3 scripts/codex-task documentation phase4-review --report-file reports/phase4-documentation-delivery/latest.json --runbook-file reports/phase4-documentation-delivery/latest.md`
- `python3 scripts/codex-task stakeholder report --report-file reports/stakeholder-reporting/latest.json --runbook-file reports/stakeholder-reporting/latest.md`
- `python3 scripts/codex-task feedback collection-plan --report-file reports/feedback-collection/latest.json --runbook-file reports/feedback-collection/latest.md`
- `python3 scripts/codex-task work-tracking audit`
- `python3 scripts/codex-guard validate --include-untracked`

## Non-Goals

- No hosted form, survey platform, API endpoint, database, queue, dashboard, analytics service, or long-running feedback application is created.
- No automatic sentiment analysis, NLP classification, scoring model, or external AI call is executed.
- No owner assignment, notification, email, chat reply, webhook, ticket, or external response workflow is sent or created.
- No Taskmaster task, documentation page, session, plan, work-tracking artifact, or Git state is mutated from feedback rows.
- No external archive import/export, scraping, contact database update, PII processing, or retention policy automation is performed.
- No source report, template, Taskmaster, session, plan, work-tracking, Git, or external state is mutated beyond requested feedback collection artifacts.

This packet is a static feedback collection planning artifact. It composes existing repository evidence and requested output files only; it does not create hosted forms, API endpoints, dashboards, sentiment automation, notifications, tickets, external archives, or response delivery systems.
