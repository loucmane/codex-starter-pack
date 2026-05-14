# Task 69 Phase 5 Enhancement Planning Scope Reconciliation

## Decision

Task 69 will implement a deterministic, file-backed Phase 5 enhancement planning packet, not speculative post-MVP automation, live enhancement services, or unverified MCP integrations.

The historical Taskmaster wording asks to identify enhancement opportunities, create an enhancement roadmap, implement auto-compaction triggers, add semantic search enhancements, create AI-assisted template generation, implement advanced optimizations, plan additional MCP integrations, and create enhancement metrics. Most of those items are broad roadmap candidates rather than safe implementation work for a single task. The current portable foundation already has concrete primitives for several of them:

- compaction checkpoints through `python3 scripts/codex-task compaction checkpoint`
- Serena status/memory verification through `python3 scripts/codex-task serena status`
- deterministic template registry/search via `scripts/template_registry.py`
- migration roadmap generation via `scripts/template-ssot-scanner/migration_roadmap.py`
- template usage/performance/metrics reports under `reports/`
- final validation and stakeholder reporting packets

The current gap is one deterministic planning artifact that prioritizes Phase 5 candidates using current repo evidence and explicitly separates "ready next actions" from speculative integrations.

## Current Evidence

| Historical Area | Current Evidence | Task 69 Treatment |
| --- | --- | --- |
| Enhancement roadmap | Task 11 migration roadmap, Task 67 success metrics, Task 73 stakeholder report | Compose a Phase 5 planning packet with prioritized candidates and refresh commands. |
| Auto-compaction triggers | Task 31 compaction checkpoint helper and compaction history | Treat as "review trigger policy" candidate; do not install automatic triggers or background monitoring. |
| Semantic search | Task 15 Serena contract, Task 61 discovery optimization, TemplateRegistry search | Surface capability-aware search enhancement candidates; do not replace registry/`rg` deterministic discovery. |
| AI-assisted template generation | Template registry, metadata policy, import/export, bundle planning | Record as future candidate requiring guardrails; do not generate templates via an external model in this task. |
| Advanced optimizations | Task 45/53/61 performance and cache work | Surface optimization candidates only when evidence reports warn/fail/missing. |
| Additional MCP integrations | Task 89/15 MCP baseline and Serena status helper | Plan optional integrations as gated candidates with startup verification; do not enable unverified MCPs. |
| Enhancement metrics | Task 67 success metrics and Task 73 stakeholder report | Add enhancement-readiness scoring and candidate metrics to the static planning packet. |

## Proven Gap

The project has many static evidence packets, but no single artifact that answers:

- Which Phase 5 enhancement candidates are evidence-backed now?
- Which candidates are speculative and should remain planned only?
- Which existing commands refresh the evidence behind each candidate?
- Which candidates require new Taskmaster tasks before implementation?
- Which historical Phase 5 requirements remain intentionally out of scope for this task?

## Implementation Boundary

Implement:

- `python3 scripts/codex-task enhancement phase5-plan`
- JSON output with label, mode, action boundary, current state, summary, candidate rows, recommended next actions, refresh commands, and non-goals
- Markdown output suitable for planning review
- focused parser, builder, renderer, and handler tests
- `reports/enhancement-planning/README.md`

Do not implement:

- automatic compaction triggers, daemons, schedulers, or background monitors
- external semantic search services or replacement of registry/`rg` discovery
- AI template generation using an external model
- optional MCP installation or config mutation
- performance optimization changes without measured bottleneck evidence
- Taskmaster task creation from candidate rows
- repository mutations outside requested report files

## Candidate Model

Each enhancement candidate should expose:

- candidate ID and title
- area (`continuity`, `search`, `template-generation`, `optimization`, `mcp`, `metrics`, `roadmap`)
- readiness (`ready`, `needs-evidence`, `planned`, `blocked`)
- priority (`high`, `medium`, `low`)
- evidence paths and refresh commands
- required next step
- non-goal boundary

Initial candidates:

1. Compaction trigger policy review
2. Serena/semantic discovery verification
3. AI-assisted template generation guardrail plan
4. Registry/performance optimization follow-up
5. Optional MCP integration evaluation
6. Enhancement metrics and stakeholder reporting refresh
7. Scanner roadmap backlog refresh

## Acceptance

Task 69 is done when:

- the static Phase 5 enhancement planning packet can be generated locally
- missing inputs are visible as `needs-evidence` or `planned`, not fabricated as complete
- focused tests prove parser, builder, renderer, and handler behavior
- final Task 69 evidence includes the sample JSON/Markdown packet, tests, plan sync, work-tracking audit, guard, Taskmaster health, and diff-check
- Taskmaster Task 69 and subtasks are marked done after verification
