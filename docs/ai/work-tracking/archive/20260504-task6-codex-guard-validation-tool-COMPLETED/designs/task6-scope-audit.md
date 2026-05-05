# Task 6 Scope Audit

## Purpose

Task 6 original wording describes creating `scripts/codex-guard` from scratch. The current repository already contains `scripts/codex-guard`, guard tests, guard reports, and workflow enforcement from later foundation tasks.

This audit exists to prove the current-state gap before implementation. It must be completed before `plan-step-implement` starts.

## Progress Log

- **2026-05-04 12:31** — [S:20260504|W:task6-codex-guard-validation-tool|H:shell:date|E:cmd`date '+%Y-%m-%d %H:%M:%S %Z %z'`] Confirmed current timestamp as `2026-05-04 12:31:08 CEST +0200` before creating the Task 6 scope-audit evidence anchor.
- **2026-05-04 12:31** — [S:20260504|W:task6-codex-guard-validation-tool|H:docs/ai/work-tracking/active/20260504-task6-codex-guard-validation-tool-ACTIVE/designs/task6-scope-audit.md|E:scripts/codex-guard] Created the Task 6 scope-audit document as a pending evidence anchor for current-state reconciliation.
- **2026-05-04 12:34** — [S:20260504|W:task6-codex-guard-validation-tool|H:shell:date|E:cmd`date '+%Y-%m-%d %H:%M:%S %Z %z'`] Confirmed current timestamp as `2026-05-04 12:34:46 CEST +0200` before implementing the proven Task 6 gap.
- **2026-05-04 12:34** — [S:20260504|W:task6-codex-guard-validation-tool|H:.pre-commit-config.yaml|E:templates/engine/enforcement/meta-workflow-guard-ci-plan.md] Identified local git hook wiring as the proven current-state gap: CI guard wiring exists, but the repository lacked the planned pre-commit configuration.
- **2026-05-04 12:45** — [S:20260504|W:task6-codex-guard-validation-tool|H:.pre-commit-config.yaml|E:tests/meta_workflow_guard/test_guard_rules.py] Updated the local drift hook to pass `--report-dir ""` so pre-commit validation does not mutate the working tree.

## Audit Checklist

- [x] Review `scripts/codex-guard` command surface.
- [x] Review existing guard tests under `tests/meta_workflow_guard/`.
- [x] Compare current implementation against Task 6 details.
- [x] Identify the smallest proven current-state gap.
- [x] Record implementation decision before changing guard behavior.

## Current Coverage

- `validate` enforces S:W:H:E entries, evidence placeholders, template handler references, session timestamps, tracker timestamps, plan sync, branch policy, active work-tracking folder rules, runtime artifact exclusions, Taskmaster evidence, session state consistency, GAC guidance, and template metadata policy.
- `drift-check` scans canonical docs, template metadata drift, and guard command surface drift.
- Template frontmatter validation exists through `templates/metadata/template-metadata-policy.json` and the guard metadata policy helpers.
- Exception support exists through metadata policy exemptions and `CODEX_GUARD_IGNORE_PATHS`.
- CI integration exists through `.github/workflows/codex-guard.yml` and `.github/workflows/meta-workflow-guard.yml`.

## Gap Decision

The useful Task 6 gap is local git hook integration support. `templates/engine/enforcement/meta-workflow-guard-ci-plan.md` already described a local pre-commit hook, but the repository had no `.pre-commit-config.yaml`.

Auto-fix is intentionally not implemented in this slice. The current workflow emphasizes explicit, logged fixes instead of guard-driven mutation, and `templates/TOOLS.md` keeps auto-fix as roadmap.

The local drift hook disables report output with `--report-dir ""`; CI and explicit report-generation commands still write artifacts.
