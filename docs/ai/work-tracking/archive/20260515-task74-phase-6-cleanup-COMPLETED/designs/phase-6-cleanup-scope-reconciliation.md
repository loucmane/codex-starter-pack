# Task 74 Scope Reconciliation - Phase 6 Cleanup

## Taskmaster Source

Task 74 asks to complete final cleanup and maintenance setup:

- remove all monolithic files;
- archive legacy artifacts;
- clean temporary files;
- update documentation;
- verify zero legacy references;
- establish maintenance cadence;
- create a final report;
- schedule a celebration event.

That wording comes from the historical Phase 6 migration plan. It is not safe to execute literally because the repository has already moved to a portable, evidence-backed foundation and many old assumptions are obsolete.

## Current Authority

| Source | Current Signal | Task 74 Implication |
| --- | --- | --- |
| `templates/engine/core/portable-foundation-spec.md` | Cleanup must preserve configured roots, session/plan/work-tracking lifecycle, S:W:H:E evidence, and core-vs-adapter boundaries. | Do not add live cleanup automation or hardcoded repo-specific behavior. |
| `.taskmaster/reports/codebase-analysis.md` | Root monoliths are gone; current risk is stale backlog wording, scanner defaults, and reference-cycle cleanup. | Treat "remove all monolithic files" as historical unless current evidence identifies an actual tracked artifact. |
| `docs/ai/work-tracking/archive/20260430-task4-scanner-configuration-system-COMPLETED/designs/backlog-alignment-audit.md` | Tasks 4-80 must start with scope reconciliation and should not execute stale subtasks literally. | Task 74 is a gate task, not a broad cleanup bundle. |
| `docs/ai/work-tracking/archive/20260510-task48-remaining-template-alignment-COMPLETED/designs/remaining-backlog-alignment-audit.md` | Task 74 should run only when a concrete cleanup list exists. | The implementation boundary must name exact paths before any cleanup. |
| `docs/ai/work-tracking/archive/20260514-task64-cleanup-automation-COMPLETED/designs/wizard-flow.md` | Cleanup planning is static and non-destructive; every cleanup action needs scope, dry-run, backup/rollback, review, and verification gates. | Task 74 may execute only a small, reviewed cleanup with stored evidence. |
| `docs/ai/work-tracking/archive/20260514-task70-long-term-maintenance-COMPLETED/designs/wizard-flow.md` | Maintenance cadence is already represented by a static maintenance packet. | Do not duplicate long-term maintenance setup or install schedulers. |

## Current Evidence Checks

| Check | Result | Interpretation |
| --- | --- | --- |
| `find docs/ai/work-tracking/active -mindepth 1 -maxdepth 1 -type d` | Only `20260515-task74-phase-6-cleanup-ACTIVE` is active. | No stale active work-tracking folder needs cleanup. |
| `git ls-files '*.md' \| xargs -r wc -c \| sort -nr` | Largest live template files are below 100KB; root monoliths are absent. | No current monolith-sized markdown cleanup is proven. |
| `git ls-files output` | Seven tracked files under root `output/`. | Root generated scanner artifacts are the concrete cleanup candidate. |
| `rg "PROJECT-BLOG\|WORKFLOWS.md\|PATTERNS.md\|monolith" --glob '!docs/ai/work-tracking/archive/**' --glob '!sessions/**' --glob '!plans/**'` | Root `output/` data and scripts contain stale references to removed `templates/PROJECT-BLOG.md` and old monolith paths. | The tracked root scanner outputs are stale historical artifacts, not durable foundation docs. |
| `.gitignore` | Ignores `scripts/template-ssot-scanner/output/{data,scripts,...}` but not root `output/`. | Old scanner defaults can create root generated artifacts that are not ignored. |
| `python3 scripts/codex-task cleanup plan --label task74-scope --dry-run` | Cleanup packet reports ready evidence domains and explicitly requires scoped approval before cleanup. | Task 74 can use this as its cleanup review contract, but should not add automation. |

## Proven Gap

The proven current-state cleanup gap is narrow:

1. The repository still tracks generated scanner artifacts under root `output/`.
2. Those artifacts are stale; they include historical `PROJECT-BLOG`, `WORKFLOWS.md`, and `PATTERNS.md` findings that no longer represent the current portable foundation.
3. The root `output/` directory is not ignored, so old scanner defaults can recreate untracked runtime artifacts in a commit-visible path.
4. Durable scanner evidence already has better homes:
   - static reports under `reports/`;
   - task-local evidence under `docs/ai/work-tracking/.../reports/`;
   - generated scanner runtime output under ignored `scripts/template-ssot-scanner/output/`.

## Selected Implementation Boundary

Task 74 should implement only this cleanup:

- remove tracked root `output/` generated artifacts from the repository;
- add root `output/` to `.gitignore` as scanner-generated runtime output;
- update `scripts/template-ssot-scanner/README.md` so it states that root `output/` is generated/ignored runtime output and durable evidence belongs in reports or task-local work tracking;
- capture verification evidence that `git ls-files output` returns no tracked files after the cleanup;
- keep cleanup planning static and manual; do not create deletion automation, schedulers, retention jobs, or broad scanners.

## Explicit Non-Goals

- Do not delete or archive work-tracking history.
- Do not clear active session or plan pointers except during post-merge archive closeout.
- Do not modify scanner algorithms or change scanner default output paths in this task.
- Do not apply reference-fix scripts or generated cleanup recommendations.
- Do not remove `templates/WORKFLOWS.md`, `templates/PATTERNS.md`, registry files, reports, task files, memories, or archived evidence.
- Do not implement celebration planning, notifications, dashboards, schedules, tickets, or external maintenance automation.

## Acceptance Criteria

- This scope artifact is recorded and referenced from tracker/session updates.
- Taskmaster subtask `74.1` is marked done after plan sync.
- Tracked root `output/` files are removed and root `output/` is ignored.
- Scanner README explains the generated-output boundary.
- Verification captures:
  - `git ls-files output`;
  - focused tests or static checks relevant to the changed files;
  - plan sync;
  - work-tracking audit;
  - Taskmaster health;
  - guard;
  - diff-check.
