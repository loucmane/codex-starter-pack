# Task 71 Migration Archive Scope Reconciliation

## Context

- **Taskmaster task**: 71 - Create Migration Archive
- **Session**: 2026-05-15-004
- **Work context**: task71-create-migration-archive
- **Decision driver**: The portable foundation already preserves task-local migration evidence in `docs/ai/work-tracking/archive/`, repository reports in `reports/`, scanner tooling and generated scanner outputs in `scripts/template-ssot-scanner/`, and migration-support plans in `plans/`.

## Current Evidence Shape

The repo already has a durable archive structure:

- `docs/ai/work-tracking/archive/*-COMPLETED/` contains completed task folders with `TRACKER.md`, `FINDINGS.md`, `DECISIONS.md`, `IMPLEMENTATION.md`, `HANDOFF.md`, designs, reports, and test evidence.
- `scripts/template-ssot-scanner/` contains scanner, migration detector, migration roadmap, reference-fix, duplicate, security, and baseline-summary tooling.
- `scripts/template-ssot-scanner/output/data/` contains scanner output JSON used by migration metrics.
- `reports/` contains repository-level report families such as migration health, post-migration monitoring, production deployment, template metrics, performance, and guard reports.
- `plans/` and `.taskmaster/tasks/` preserve task-level planning and Taskmaster status.
- `.serena/memories/` preserves compact task/session continuity notes.

## Scope Boundary

Task 71 should not copy all historical artifacts into another archive directory. Duplicating evidence would make later updates ambiguous and could drift from the canonical work-tracking archive. The current-state gap is discoverability: users need a static index and search surface that points to the canonical artifacts already preserved in place.

## Selected Implementation

Implement `python3 scripts/codex-task migration archive` as a static, non-mutating-by-default archive packet generator.

The command will:

- inventory completed migration-related work-tracking folders;
- inventory relevant migration reports and report README files;
- inventory scanner/fix/tooling scripts and key scanner outputs;
- include Taskmaster task file references for migration/archive-related tasks;
- render a timeline from completed folder prefixes;
- collect decision-record pointers from `DECISIONS.md`;
- collect lessons-learned candidates from `FINDINGS.md`, `HANDOFF.md`, and Serena memories;
- support `--query` filtering so the packet doubles as a lightweight search capability;
- write JSON and Markdown outputs only when explicit output paths are supplied.

## Non-Goals

- Do not move or duplicate archived task folders.
- Do not zip, upload, publish, or export an archive bundle.
- Do not delete or reorganize scanner outputs.
- Do not contact external storage, issue trackers, dashboards, or hosted search systems.
- Do not infer retention policy or legal archive requirements.

## Acceptance

- Generated archive JSON/Markdown lists canonical source paths and counts.
- Query-filtered output returns only matching entries.
- Focused tests cover inventory, query filtering, rendering, and output writes.
- Guard, audit, Taskmaster health, and diff-check evidence are stored before completion.

## Work Tracking

- **2026-05-15 16:00 CEST** - [S:20260515|W:task71-create-migration-archive|H:scope-reconciliation|E:docs/ai/work-tracking/active/20260515-task71-create-migration-archive-ACTIVE/designs/migration-archive-scope-reconciliation.md] Selected a searchable archive index over canonical evidence locations instead of duplicating or moving historical artifacts.
