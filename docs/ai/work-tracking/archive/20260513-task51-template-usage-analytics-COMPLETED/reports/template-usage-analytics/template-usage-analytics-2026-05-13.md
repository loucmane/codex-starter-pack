# Template Usage Analytics

- Label: task51
- Created at: 2026-05-13T16:17:43+02:00
- Mode: non-destructive-template-usage-analytics
- Executes mutations: False
- Source: `.`
- Include archive: False

## Summary

- Registered templates: 261
- Workflow files scanned: 312
- Workflow files with template references: 158
- Total mentions: 735
- ID mentions: 276
- Path mentions: 450
- Alias mentions: 9
- Templates with observed usage: 106
- Templates without observed usage: 149

## Source Coverage

| Source type | Files scanned | Files with matches | Mentions |
| --- | ---: | ---: | ---: |
| plans | 91 | 33 | 244 |
| sessions | 109 | 44 | 290 |
| taskmaster | 104 | 78 | 159 |
| work_tracking_active | 8 | 3 | 42 |

## Top Templates

| Template | Category | Mentions | ID | Path | Alias |
| --- | --- | ---: | ---: | ---: | ---: |
| `portable-foundation-spec` | engine | 243 | 137 | 106 | 0 |
| `meta-workflow-authoring` | handlers | 49 | 40 | 9 | 0 |
| `templates-TOOLS` | TOOLS.md | 25 | 2 | 23 | 0 |
| `templates-metadata-template-overview` | metadata | 17 | 2 | 15 | 0 |
| `guide-index` | guides | 14 | 2 | 12 | 0 |
| `session-continuation-workflow` | session | 13 | 5 | 8 | 0 |
| `serena-guide` | search | 12 | 7 | 5 | 0 |
| `session-state-management` | session | 12 | 2 | 10 | 0 |
| `foundation-communication-templates` | guides | 11 | 6 | 5 | 0 |
| `plan-template` | processes | 11 | 7 | 4 | 0 |

## Category Mentions

- engine: 263
- handlers: 80
- session: 58
- guides: 49
- processes: 35
- TOOLS.md: 25
- git: 20
- registry: 18
- metadata: 17
- search: 12
- taskmaster: 12
- REGISTRY.md: 10
- ci: 10
- domain: 10
- helpers: 10
- patterns: 10
- USER-GUIDE.md: 8
- integration: 8
- planning: 6
- work-tracking: 6
- WORKFLOWS.md: 5
- analysis: 5
- HANDLERS.md: 4
- architecture: 4
- core: 4
- index: 4
- tools: 4
- BEHAVIORS.md: 3
- BUILDING-BETTER.md: 3
- code-style: 3
- selection: 3
- timestamps: 3
- CONVENTIONS.md: 2
- MATRICES.md: 2
- PATTERNS.md: 2
- behaviors: 2
- examples: 2
- mapping: 2
- routing: 2
- tools/external: 2
- workflows: 2
- cross-system: 1
- docs: 1
- memory: 1
- task: 1
- templates: 1

## Monthly Trend

- 2025-09: 116
- 2025-10: 125
- 2025-11: 1
- 2026-04: 143
- 2026-05: 189

## Review Queues

### Path-Only References

- `session-compaction`: 7 path mentions; prefer registry ID when practical.
- `engine-validation-foundation-adoption-guide`: 6 path mentions; prefer registry ID when practical.
- `git-commit-format`: 6 path mentions; prefer registry ID when practical.
- `handlers-index`: 6 path mentions; prefer registry ID when practical.
- `templates-behaviors-planning-plan-compliance`: 6 path mentions; prefer registry ID when practical.
- `templates-behaviors-session-compaction-detection`: 6 path mentions; prefer registry ID when practical.
- `foundation-onboarding-training`: 5 path mentions; prefer registry ID when practical.
- `meta-routing-patterns`: 5 path mentions; prefer registry ID when practical.
- `session-continuation-validation`: 5 path mentions; prefer registry ID when practical.
- `templates-WORKFLOWS`: 5 path mentions; prefer registry ID when practical.

### Alias References

- `handlers-triggers-session-prepare-compaction`: 1 alias mentions.
- `handlers-orchestrators-session-start`: 2 alias mentions.
- `handlers-orchestrators-work-activity`: 1 alias mentions.
- `handlers-triggers-session-end-session`: 1 alias mentions.
- `handlers-operators-workflow-resolve-work-void`: 1 alias mentions.
- `handlers-orchestrators-system-improvement`: 1 alias mentions.
- `handlers-triggers-debug-fix-bug`: 1 alias mentions.
- `handlers-triggers-development-start-new-work`: 1 alias mentions.

### Zero Observed References

- `cross-system-integration-patterns` (integration, stable)
- `directory-structure` (files, stable)
- `docs-standards` (docs, stable)
- `documentation-creation-patterns` (work-tracking, stable)
- `edit-strategies` (file, stable)
- `engine-MODULARIZATION-COMPLETE` (engine, status unknown)
- `engine-activation-context-aware` (engine, stable)
- `engine-core-enforcement-check` (engine, stable)
- `engine-core-pre-ultrathink` (engine, stable)
- `engine-core-ultrathink-protocol` (engine, stable)

## Recommended Actions

- Review path-only references and prefer registry IDs where workflow portability matters.
- Use zero-observed-reference templates as candidates for documentation, lifecycle, or deprecation review.
- Review the highest-mentioned templates before changing shared workflow behavior.
- Rerun this report after major template registry, Taskmaster, session, or work-tracking migrations.

## Non-Goals

- No runtime decorators, counters, instrumentation hooks, or tracking code are added to templates.
- No database, warehouse, event stream, time-series backend, or long-running aggregation service is created.
- No live dashboard, WebSocket, Grafana board, hosted analytics page, or external observability service is contacted.
- No alert, notification, ticket, issue, webhook, or anomaly service is sent or configured.
- No predictive capacity-planning model is trained or executed.
- No template, Taskmaster, session, plan, work-tracking, Git, or external state is mutated beyond requested report artifacts.

No runtime tracker, database, live dashboard, alert, predictive service, template mutation, or external analytics action was executed by this report.
