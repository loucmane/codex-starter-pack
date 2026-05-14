# Task 76 Celebration Planning Scope Reconciliation

## Decision

Task 76 will implement a deterministic, file-backed celebration planning packet, not a real event, publication workflow, notification system, or hosted presentation site.

The historical Taskmaster wording asks to plan a celebration event, create a success announcement, prepare team recognition, document achievements, create a success blog post, prepare demos, organize a retrospective, and plan a future roadmap presentation. Those are useful communication concepts, but the current portable foundation should not schedule meetings, publish content, send announcements, create external assets, or contact collaboration tools from this task.

The current repository already has static evidence that can support a celebration/readout packet:

- Task 67 success metrics packet
- Task 73 stakeholder reporting packet
- Task 69 Phase 5 enhancement planning packet
- Taskmaster full-graph health
- archived work-tracking evidence and verification logs
- communication guidance templates

The current gap is one deterministic celebration/readout packet that composes those inputs into review-ready materials while keeping all human-facing publication, scheduling, and distribution steps manual.

## Current Evidence

| Historical Area | Current Evidence | Task 76 Treatment |
| --- | --- | --- |
| Celebration event | Task 73 stakeholder messages, Task 67 success metrics | Create an event/readout agenda and prep checklist; do not schedule a meeting. |
| Success announcement | Stakeholder report and communication templates | Draft repository-native announcement copy; do not publish or send it. |
| Team recognition | Taskmaster/task evidence and work-tracking archive | Generate recognition prompts/categories; do not assign awards or contact people. |
| Achievements | Taskmaster health, success metrics, stakeholder report | Summarize achieved foundation milestones with evidence paths. |
| Blog post | Static docs and report evidence | Draft an outline only; do not create hosted/blog content. |
| Demos | Existing CLI/report commands | List demo candidates and refresh commands; do not run demos automatically. |
| Retrospective | Existing handoff/findings/decisions records | Provide retrospective prompts; do not schedule or collect responses. |
| Future roadmap presentation | Task 69 enhancement plan | Summarize roadmap talking points and next-action candidates. |

## Proven Gap

The project now has delivery, success, stakeholder, and enhancement planning evidence, but no single static packet that answers:

- What should be celebrated or communicated after the migration/foundation work?
- Which evidence paths support those claims?
- What draft announcement, agenda, demo list, recognition prompts, retrospective prompts, and roadmap talking points can be reviewed?
- Which human actions remain manual and out of scope?

## Implementation Boundary

Implement:

- `python3 scripts/codex-task celebration plan`
- JSON output with label, mode, action boundary, current state, summary, evidence domains, announcement draft, agenda, demo candidates, recognition prompts, retrospective prompts, roadmap talking points, manual next steps, refresh commands, and non-goals
- Markdown output suitable for human review before any external sharing
- focused parser, builder, renderer, and handler tests
- `reports/celebration-planning/README.md`

Do not implement:

- calendar scheduling, meeting creation, reminders, invitations, or event logistics automation
- email, chat, social, blog, website, or external publishing
- award decisions, compensation, HR records, or personal attribution beyond generic prompts
- live dashboards, generated slide decks, hosted demos, or media assets
- response collection, survey distribution, analytics tracking, or sentiment analysis
- Taskmaster mutation from celebration packet rows
- repository mutations outside requested report files

## Packet Model

The celebration planning packet should expose:

- evidence domains with status and evidence paths
- achievement highlights grounded in existing reports
- announcement draft sections
- event/readout agenda items
- demo candidates with commands and evidence
- recognition prompts/categories
- retrospective prompts
- roadmap talking points from Task 69
- manual next steps and refresh commands
- explicit non-goal boundaries

## Acceptance

Task 76 is done when:

- the static celebration planning packet can be generated locally
- missing source inputs are visible as `needs-evidence`, not fabricated as complete
- focused tests prove parser, builder, renderer, and handler behavior
- final Task 76 evidence includes the sample JSON/Markdown packet, tests, plan sync, work-tracking audit, guard, Taskmaster health, and diff-check
- Taskmaster Task 76 and subtasks are marked done after verification
