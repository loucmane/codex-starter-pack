# Task 1 Codebase Analysis Scope

## Purpose
Task 1 unlocks the original dependency chain by producing a current repository analysis. The task text predates the portability work completed in Tasks 81-102, so the work must reconcile the original intent with the current foundation instead of replaying stale commands literally.

## Current-State Corrections
- Root `WORKFLOWS.md` and `PATTERNS.md` are no longer present; current monolith examples live at `templates/WORKFLOWS.md` and `templates/PATTERNS.md`.
- `package.json` is not present in this repository, so Node package analysis is out of scope unless a later task adds it intentionally.
- The task references helper scripts such as `scripts/segment_monoliths.py`, `scripts/scan_imports.py`, and `scripts/generate_analysis_report.py`; these do not exist in the current repo.
- The durable scanner surface is `scripts/template-ssot-scanner/`, plus the newer guard/task helpers and metadata scanner outputs.

## Evidence Targets
- `docs/ai/work-tracking/active/20260425-task1-codebase-structure-analysis-ACTIVE/reports/codebase-analysis/`
- `.taskmaster/reports/codebase-analysis.md`
- Taskmaster subtask status updates for `1.1` through `1.8`

## Workstreams
1. Generate a git-tracked template/workflow/script inventory.
2. Identify large markdown and legacy monolith candidates.
3. Map reference patterns and template/script dependencies.
4. Assess the current scanner suite capabilities.
5. Capture performance and reproducibility notes using existing commands.
6. Score migration/readiness based on current foundation state.
7. Publish a synthesized report for downstream tasks.

## Non-Goals
- Do not restore removed root monolith files.
- Do not create one-off analysis scripts unless the current analysis proves they should become durable foundation tooling.
- Do not mark downstream blocked tasks complete without evidence from the current repository.
