# Task 59 Feedback Collection System Scope Reconciliation

## Decision

Task 59 will implement a deterministic, file-backed feedback collection planning packet, not a live feedback product, form service, API, sentiment pipeline, routing engine, response desk, dashboard, or external archive.

The historical Taskmaster wording asks for a feedback form with categorization, API endpoints, sentiment analysis, dashboard, owner routing, metrics tracking, response system, and feedback archive. That wording came from the old migration program framing. The current portable foundation has deliberately moved this class of operational workflow into repository-native static packets and manual review steps unless a live integration is explicitly scoped.

Current repository evidence already covers pieces of feedback capture:

- `templates/guides/communication/foundation-communication-templates.md` includes a feedback/follow-up capture payload.
- `templates/guides/training/foundation-onboarding.md` tells operators to store feedback as repository evidence tied to active tasks.
- `python3 scripts/codex-task documentation phase4-review` exposes feedback capture guidance and explicitly rejects external survey/communication claims.
- Task 49, Task 54, Task 63, Task 73, and Task 76 artifacts provide communication, knowledge transfer, documentation delivery, stakeholder reporting, and celebration/readout inputs.
- Taskmaster full-graph health and work-tracking archives provide a grounded destination for follow-up work.

The current gap is one deterministic feedback collection packet that turns those inputs into a reviewable intake model, routing matrix, metrics checklist, response workflow, archive/export guidance, and follow-up-task guidance while keeping live collection and external delivery manual.

## Current Evidence

| Historical Area | Current Evidence | Task 59 Treatment |
| --- | --- | --- |
| Feedback form with categorization | Communication feedback/follow-up template | Generate repo-native intake fields and categories; do not host a form. |
| Feedback API endpoints | No service/API layer exists in the portable foundation | Provide static schema guidance; do not implement endpoints. |
| Sentiment analysis | No NLP/sentiment model or external analytics service exists | Provide manual severity/sentiment review prompts; do not infer sentiment automatically. |
| Feedback dashboard | Static reports and work-tracking evidence model exist | Generate a static metrics/checklist packet; do not create a live dashboard. |
| Routing to owners | Taskmaster task ownership and work-tracking handoff model exist | Provide routing criteria and follow-up task guidance; do not assign people or notify owners. |
| Metrics tracking | Success metrics, stakeholder reporting, and Taskmaster health packets exist | Define feedback metrics to review; do not persist a database. |
| Response system | Communication templates and HANDOFF/FINDINGS/DECISIONS files exist | Provide response draft guidance; do not send replies. |
| Feedback archive | Work-tracking archive and report directories exist | Generate archive/export instructions; do not collect or move external feedback. |

## Proven Gap

The project has repository-native places to record feedback and follow-up decisions, but there is no single artifact that answers:

- What fields should be captured for feedback during foundation adoption?
- Which categories, severity/sentiment labels, routing rules, and response states should be used?
- Which evidence paths support feedback follow-up claims?
- Which metrics should an operator review before creating a follow-up task?
- How should feedback be archived as repository evidence without claiming a live system?
- Which actions remain manual and out of scope?

## Implementation Boundary

Implement:

- `python3 scripts/codex-task feedback collection-plan`
- JSON output with label, mode, action boundary, current state, summary, evidence domains, intake schema, categories, manual sentiment labels, routing matrix, metrics checklist, response workflow, archive guidance, manual next steps, refresh commands, and non-goals
- Markdown output suitable for human review before collecting or responding to feedback
- focused parser, builder, renderer, and handler tests
- `reports/feedback-collection/README.md`

Do not implement:

- hosted forms, survey tools, API endpoints, databases, queues, dashboards, or analytics services
- automatic sentiment analysis, NLP classification, scoring, or model calls
- owner assignment, notifications, email/chat replies, webhook delivery, or ticket creation
- automatic Taskmaster task creation, task mutation, or documentation updates from feedback rows
- external archive import/export, scraping, contact database updates, or PII processing
- repository mutations outside requested report files

## Packet Model

The feedback collection packet should expose:

- evidence domains with status, evidence paths, and refresh commands
- feedback intake schema fields and validation notes
- feedback categories and manual severity/sentiment labels
- routing matrix for documentation, workflow, guard, template, onboarding, stakeholder, and enhancement feedback
- metrics checklist for counts, open/closed status, severity mix, follow-up task coverage, and response state
- response workflow states and suggested repository-native evidence destinations
- archive guidance for work-tracking reports, FINDINGS, DECISIONS, HANDOFF, and follow-up Taskmaster tasks
- manual next steps and explicit non-goal boundaries

## Acceptance

Task 59 is done when:

- the static feedback collection planning packet can be generated locally
- missing source inputs are visible as `needs-evidence`, not fabricated as complete
- focused tests prove parser, builder, renderer, and handler behavior
- final Task 59 evidence includes the sample JSON/Markdown packet, tests, plan sync, work-tracking audit, guard, Taskmaster health, and diff-check
- Taskmaster Task 59 and subtasks are marked done after verification
