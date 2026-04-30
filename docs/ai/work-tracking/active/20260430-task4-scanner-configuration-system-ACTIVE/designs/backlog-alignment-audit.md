# Taskmaster Backlog Alignment Audit

## Purpose

The remaining Taskmaster backlog contains two different eras of work:

- original migration tasks from the older monolith-to-modular plan
- newer completed foundation tasks that established the current portable foundation contract

The current authority is `templates/engine/core/portable-foundation-spec.md`. Pending tasks must be interpreted through that contract instead of executed literally when their wording or subtasks conflict with the current repository.

## Current Foundation Contract

Future tasks must preserve:

- config-driven repo structure through `.codex/config.toml`
- portable metadata policy through `templates/metadata/template-metadata-policy.json`
- deterministic session, plan, work-tracking, and archive lifecycle
- S:W:H:E evidence and same-day timestamp enforcement
- scanner, guard, and `codex-task` helpers as reusable core logic
- repo-specific behavior in adapters/configuration rather than hardcoded script branches

## Findings

1. Tasks 81-102 are the current foundation baseline and are complete.
2. Tasks 4-80 are not safe to execute literally without a scope gate.
3. Many pending task titles still contain useful intent, but their details or subtasks are stale, overbuilt, or unrelated to this repository.
4. Several subtask sets are clearly corrupted by unrelated domains such as ML pipelines, Kubernetes manifests, GraphQL APIs, dashboards, feature flag systems, edge nodes, and PWA work.
5. Task 4 itself is directionally aligned, but Task 3 already implemented part of the scanner configuration baseline; Task 4 must now formalize configuration rather than create it from scratch.
6. The Taskmaster AI update path failed on 2026-04-30, so deterministic Taskmaster commands are required for this alignment pass.

## Alignment Policy

Pending tasks keep their top-level IDs and intent for continuity, but their stale subtask layer must not drive future implementation.

For pending tasks after Task 4:

- clear stale pending subtasks
- add a mandatory scope-reconciliation subtask
- add a mandatory implementation/verification subtask
- require future task kickoff to update or expand the task against current repository evidence before coding

Task 4 keeps its existing scanner-configuration subtasks because they match the current direction closely enough, but its scope is corrected by this plan and audit.

## Task Categories

### Current technical foundation tasks

These remain useful after reconciliation:

- 4 Scanner configuration system
- 5 Codex-task helper consolidation
- 6 Codex-guard validation consolidation
- 7 Baseline scanner outputs
- 8 Template registry/discovery system
- 10 Reference fix scripts
- 11 Migration roadmap generator
- 13 Compatibility mapping table
- 16 Performance testing harness
- 18 Security validation framework
- 20 CI/CD validation pipeline
- 21 Template frontmatter/metadata schema
- 22 Template discovery API
- 25 Phase 0 scanner validation
- 29 Template lifecycle management
- 39 Guard auto-fix mode
- 43 Template testing framework
- 45 Scanner optimization
- 46 Template import/export
- 52 CI/CD gates
- 58 Template versioning
- 61 Template discovery optimization
- 62 Agent compatibility layer
- 68 Final validation suite
- 79 Production verification
- 80 Production deployment

### Superseded or partially implemented tasks

These must begin as audits of current behavior, not greenfield implementation:

- 5 Codex-task CLI
- 6 Codex-guard validation
- 8 Template registry system
- 12 Taskmaster integration
- 21 Template frontmatter schema
- 31 Compaction protocol
- 42 Session management system

### Migration-phase tasks requiring evidence-driven reframing

These should be driven by scanner output and real remaining drift, not by old phase wording:

- 26 Critical handler templates
- 27 Pattern templates
- 28 Dual-path discovery
- 30 Cross-repository sync
- 32 Documentation suite
- 33 Training materials
- 38 Reference remediation
- 48 Remaining templates
- 56 Automation integration
- 63 Documentation delivery
- 74 Cleanup
- 78 Final documentation

### Optional operational layer

These should remain lower priority unless the foundation is intentionally productized further:

- 17 Monitoring infrastructure
- 24 Cost tracking
- 34 A/B testing
- 35 Emergency response
- 36 Governance board
- 37 Telemetry pipeline
- 40 Canary deployment
- 41 Health dashboard
- 44 Change advisory process
- 49 Communication templates
- 50 Security audit process
- 51 Usage analytics
- 53 Caching layer
- 54 Knowledge transfer
- 55 Migration metrics
- 57 Operational runbook
- 59 Feedback collection
- 60 Post-migration monitoring
- 64 Cleanup automation
- 65 Quality scoring
- 66 Deprecation management
- 67 Success metrics dashboard
- 69 Enhancement planning
- 70 Long-term maintenance
- 71 Migration archive
- 72 Post-mortem process
- 73 Stakeholder reporting
- 75 Knowledge base
- 76 Celebration planning
- 77 Continuous improvement

## Execution Rule For Future Sessions

Before implementing any pending task from the old backlog:

1. Read this audit and the portable foundation spec.
2. Read the current task file.
3. Treat old details and old subtasks as suspect unless they match current repo evidence.
4. Complete the mandatory scope-reconciliation subtask first.
5. Update/expand the task with current implementation subtasks only after the scope gate is complete.

## Progress Log

- **2026-04-30 13:18** — [S:20260430|W:task4-scanner-configuration-system|H:scripts/codex-task|E:docs/ai/work-tracking/active/20260430-task4-scanner-configuration-system-ACTIVE/designs/backlog-alignment-audit.md] Started Task 4 as backlog alignment plus scanner configuration reconciliation after the Task 3 merge.
