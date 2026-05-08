# Task 23 Migration Rehearsal Scope Reconciliation

## Purpose

Task 23 predates the portable foundation work. Its original wording asks for git
worktrees, Docker containers, test API keys, data seeding, Claude/Codex simulators,
load testing, and a rehearsal runbook. That was written for an older migration plan
where the foundation did not yet have scanner roadmaps, rollback checkpoints, guard
enforcement, guided kickoff, or cross-project fixture coverage.

This scope gate reconciles the historical task against current repository evidence
before implementation. The result is a smaller and safer rehearsal surface: a
non-destructive rehearsal planner that composes current roadmap, rollback, workflow,
and guard evidence into an auditable runbook.

## Evidence Reviewed

- `templates/engine/core/portable-foundation-spec.md`
- `docs/ai/work-tracking/archive/20260425-task1-codebase-structure-analysis-COMPLETED/designs/codebase-analysis-scope.md`
- `docs/ai/work-tracking/archive/20260425-task1-codebase-structure-analysis-COMPLETED/reports/codebase-analysis/scanner-suite-capabilities.md`
- `docs/ai/work-tracking/archive/20260425-task1-codebase-structure-analysis-COMPLETED/reports/codebase-analysis/migration-readiness-scores.md`
- `docs/ai/work-tracking/archive/20260430-task4-scanner-configuration-system-COMPLETED/designs/backlog-alignment-audit.md`
- `docs/ai/work-tracking/archive/20260507-task18-security-validation-framework-COMPLETED/designs/security-validation-scope-reconciliation.md`
- `docs/ai/work-tracking/archive/20260507-task19-rollback-mechanism-COMPLETED/designs/rollback-scope-reconciliation.md`
- `docs/ai/work-tracking/archive/20260508-task11-migration-roadmap-generator-COMPLETED/designs/migration-roadmap-scope-reconciliation.md`
- `docs/ai/work-tracking/archive/20260424-task101-cross-project-compatibility-fixtures-COMPLETED/designs/cross-project-fixture-matrix.md`
- `docs/ai/work-tracking/archive/20260424-task102-foundation-migration-adoption-COMPLETED/designs/foundation-migration-outline.md`
- Current `scripts/codex-task` rollback, taskmaster health, plan sync, work-tracking, and wizard helpers.

## Historical Requirement Assessment

| Historical Detail | Current Evidence | Task 23 Decision |
| --- | --- | --- |
| Create migration-rehearsal branches with git worktree | Claude runtime readiness now supports linked worktrees, and worktrees remain useful for isolation, but creating them automatically is a Git mutation that should not be hidden inside a generic rehearsal command. | Generate explicit worktree/run commands in a runbook; do not create worktrees automatically. |
| Set up Docker containers for isolated testing | No Docker runtime, service container, or app deployment surface is present in this repository. The foundation is template/workflow tooling, not a running service. | Defer Docker/container orchestration until a real product repo adoption task proves the need. |
| Configure test API keys with rate limits | Current scanners, guards, and helpers are local deterministic tools. No external API-key-backed rehearsal target exists. | Defer API-key handling; keep rehearsal local and deterministic. |
| Create data seeding scripts for templates | Task 101 already provides cross-project fixture shapes. Scanner outputs and roadmap JSON are the relevant test data for this repo. | Reuse roadmap/checkpoint inputs rather than inventing seed data. |
| Implement agent simulators for Claude/Codex | Task 103-106 created and tested the Claude runtime adapter gate. Simulators are not needed to rehearse template migration. | Defer agent simulators to agent-specific adapter tasks. |
| Add load testing harness with k6 or locust | There is no HTTP service or load-bearing runtime endpoint. The scanner suite has focused pytest and CLI evidence instead. | Defer load testing; use pytest/guard/audit evidence for this foundation. |
| Create rehearsal runbook with checkpoints | Task 11 provides prioritized roadmap data; Task 19 provides rollback checkpoints and recovery plans. The missing gap is tying them together into one rehearsal manifest/runbook. | Implement a `codex-task rehearsal plan` helper that composes roadmap and checkpoint inputs into JSON plus markdown runbook evidence without executing risky actions. |

## Selected Implementation Scope

Add a `python3 scripts/codex-task rehearsal plan` command that:

- accepts a migration roadmap JSON file from `scripts/template-ssot-scanner/migration_roadmap.py`;
- accepts a rollback checkpoint JSON file from `python3 scripts/codex-task rollback checkpoint`;
- captures the current Git, workflow, Taskmaster, and Serena snapshots through existing helper internals;
- writes a deterministic JSON rehearsal manifest;
- optionally writes a markdown rehearsal runbook;
- includes non-destructive preparation, execution, verification, and abort guidance;
- lists the migration roadmap priority counts, phase plan, first actionable items, checkpoint commit, active workflow pointers, and guard/test commands;
- states explicitly that it does not create worktrees, modify Taskmaster, apply fixes, create Docker containers, call external APIs, or run rollback commands.

## Recommended Command Shape

```bash
python3 scripts/codex-task rehearsal plan \
  --roadmap docs/ai/work-tracking/active/<folder>/reports/migration-rehearsal-environment/migration-roadmap-YYYY-MM-DD.json \
  --checkpoint docs/ai/work-tracking/active/<folder>/reports/migration-rehearsal-environment/checkpoint-YYYY-MM-DD.json \
  --report-file docs/ai/work-tracking/active/<folder>/reports/migration-rehearsal-environment/rehearsal-plan-YYYY-MM-DD.json \
  --runbook-file docs/ai/work-tracking/active/<folder>/reports/migration-rehearsal-environment/rehearsal-runbook-YYYY-MM-DD.md
```

## Acceptance

- Parser exposes `rehearsal plan`.
- Unit tests prove parser wiring, manifest generation, roadmap/checkpoint parsing, and markdown runbook rendering.
- Live evidence includes a current roadmap JSON/markdown, rollback checkpoint JSON, rehearsal plan JSON, and rehearsal runbook markdown under Task 23 reports.
- The runbook is explicit that rehearsal commands are guidance, not executed actions.
- Taskmaster Task 23.1 is completed after this scope gate; Task 23.2 is completed after implementation and verification evidence.

## Non-Goals

- No Docker or container setup in this repository.
- No external API keys or rate-limit configuration.
- No agent simulator implementation.
- No k6/locust dependency.
- No automatic git worktree creation.
- No automatic Taskmaster task import from roadmap JSON.
- No destructive rollback, reset, clean, or restore actions.

## Scope Result

Task 23 should be completed as a portable migration rehearsal planner integrated into
`scripts/codex-task`, not as an operational environment builder. This preserves the
historical intent of rehearsing migrations while matching the current foundation:
deterministic local evidence, explicit checkpoints, auditable runbooks, and no hidden
stateful operations.
