# Task 11 Migration Roadmap Scope Reconciliation

## Purpose

Task 11 originally asks for a migration roadmap generator that reads scanner JSON outputs,
prioritizes findings, writes a markdown roadmap, estimates effort, includes a dependency
graph, adds a Gantt visualization, and exports Taskmaster-compatible data.

The current repository has already completed the portable foundation work that did not
exist when the original task was written. This scope gate reconciles the old wording
against the current scanner suite, Task 1 codebase analysis, Task 4 backlog-alignment
audit, and `templates/engine/core/portable-foundation-spec.md`.

## Evidence Reviewed

- `templates/engine/core/portable-foundation-spec.md`
- `docs/ai/work-tracking/archive/20260425-task1-codebase-structure-analysis-COMPLETED/designs/codebase-analysis-scope.md`
- `docs/ai/work-tracking/archive/20260425-task1-codebase-structure-analysis-COMPLETED/reports/codebase-analysis/scanner-suite-capabilities.md`
- `docs/ai/work-tracking/archive/20260425-task1-codebase-structure-analysis-COMPLETED/reports/codebase-analysis/migration-readiness-scores.md`
- `docs/ai/work-tracking/archive/20260430-task4-scanner-configuration-system-COMPLETED/designs/backlog-alignment-audit.md`
- Current scanner outputs under `scripts/template-ssot-scanner/output/data/`
- Current scanner helpers under `scripts/template-ssot-scanner/`

## Current-State Findings

Task 1 established that the scanner suite is useful diagnostic input, but raw outputs are
too noisy to become direct execution plans. Task 4 established the rule for old backlog
tasks: preserve the top-level task intent, but do not execute stale implementation details
literally.

The current scanner suite already has:

- metadata-wrapped scanner outputs
- `baseline_summary.py`, which aggregates scanner metrics into JSON
- `generate_fixes.py`, which emits fix recommendations and generated scripts
- `run_all_scanners.py`, which writes the current baseline summary

The current scanner suite does not have:

- a durable prioritized roadmap artifact that turns scanner outputs into an ordered plan
- a Taskmaster-compatible export describing actionable migration items
- deterministic effort, risk, and dependency fields for planning follow-up work

Current scanner data from 2026-05-07 shows:

- 333 scanned files
- 175 broken references
- 11 circular dependencies
- 80 orphaned files
- 4 duplicate files in 2 exact duplicate groups
- 7 pending migration files
- 5 content-update recommendations
- 1 security warning remaining from `templates/PROJECT-BLOG.md` in the checked-in scanner output

The security warning is stale relative to Task 108, which removed `templates/PROJECT-BLOG.md`.
The roadmap generator must report based on the scanner outputs it is given, but final Task 11
verification should regenerate or explicitly document scanner-output freshness before treating
that warning as current work.

## Decision

Implement a deterministic scanner-roadmap generator in the existing scanner suite rather than
adding a separate planning subsystem.

The current Task 11 implementation should add:

- a `migration_roadmap.py` scanner helper
- metadata-wrapped roadmap JSON output
- markdown roadmap output
- Taskmaster-compatible export data inside the JSON payload
- focused tests for priority ordering, effort/risk assignment, dependency hints, and output shape

The generator should read existing scanner outputs from a configurable data directory and
should not rerun scanners by default.

## Priority Model

The old priority wording is directionally useful, but it needs current scanner categories:

| Priority | Current input | Roadmap treatment |
|----------|---------------|-------------------|
| critical | security errors or broken references | fix before migration cleanup |
| high | monolith/content migration recommendations and circular dependencies | unblock modular foundation correctness |
| medium | duplicate removals and security warnings | reduce maintenance risk after critical/high work |
| low | orphan review and broad optimization recommendations | backlog follow-up only |

Items should be grouped by actionable category and source file where possible. The generator
must not blindly create one Taskmaster task per raw broken reference unless that is explicitly
requested later.

## Non-Goals

- Do not add a new runtime dependency such as `matplotlib` only to satisfy the historical
  Gantt wording. A markdown roadmap with deterministic phase/dependency data is enough for
  the current foundation.
- Do not modify Taskmaster tasks from scanner data automatically.
- Do not apply generated fixes.
- Do not duplicate `baseline_summary.py`; use it as input context where useful.
- Do not hardcode this repository layout beyond existing scanner defaults and CLI arguments.

## Implementation Boundary

Recommended file set:

- `scripts/template-ssot-scanner/migration_roadmap.py`
- `scripts/template-ssot-scanner/test_scanner_modules.py`
- `scripts/template-ssot-scanner/README.md`
- Task 11 work-tracking/session/plan evidence files

Recommended output paths:

- `scripts/template-ssot-scanner/output/data/migration_roadmap.json`
- `scripts/template-ssot-scanner/output/reports/migration_roadmap.md`

## Acceptance

- Unit tests prove roadmap priority ordering and output shape.
- CLI can write markdown and JSON roadmap outputs from scanner data.
- JSON output uses the established scanner metadata wrapper.
- Markdown output includes summary metrics, prioritized items, effort/risk fields, dependency
  hints, and Taskmaster import guidance.
- Task 11 final verification records pytest, live roadmap generation, plan sync, audit,
  guard, Taskmaster health, and diff-check evidence.
