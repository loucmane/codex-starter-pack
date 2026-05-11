# Task 62 Agent Compatibility Scope Reconciliation

## Purpose

Task 62 originally asked for capability detection, version negotiation, per-agent feature flags, compatibility validation, fallback strategies, agent-specific transformations, compatibility tests, and compatibility metrics.

That wording predates the portable foundation work and the Claude runtime adapter. The current implementation must therefore reconcile the old request against the repository as it exists now, not build a parallel runtime layer.

## Current Repository Evidence

Relevant completed or active foundation work:

- Task 13 already implemented template path compatibility through `templates/registry/compatibility-map.json` and `scripts/template_registry.py`. Task 62 must not duplicate legacy template path redirects.
- Tasks 103, 105, and 106 established and smoke-tested the Claude runtime adapter: readiness, PreToolUse gates, protected path enforcement, Bash write-surface blocking, and Claude-owned agent catalog files.
- Task 40 added a non-destructive canary rollout plan with explicit stages for `codex`, `claude`, and `other-agents`.
- `templates/engine/core/portable-foundation-spec.md` defines the portable foundation boundary: core behavior should be reusable across repositories, with repo-local adapter data controlling paths and rollout choices.
- Existing agent docs such as `templates/integration/guides/adding-agents.md` are historical and partly stale; they do not provide a machine-readable compatibility source that current scripts can validate.

## Confirmed Current Gap

The repository has agent-specific runtime pieces, but no canonical agent compatibility layer that answers these questions from tracked data:

- Which agents/profiles are recognized by the portable foundation?
- Which runtime contract version does each agent support?
- Which workflow capabilities are native, gated, planned, or unsupported for each agent?
- Which ownership boundaries, evidence requirements, and fallback paths apply per agent?
- Can CI or a local command validate that the matrix is internally consistent?
- Can we produce compatibility metrics without relying on memory or prose-only documentation?

## Chosen Implementation Shape

Task 62 will implement the smallest useful compatibility layer:

1. Add a machine-readable compatibility matrix at `templates/registry/agent-compatibility-matrix.json`.
2. Add a `python3 scripts/codex-task agent compatibility-report` helper that loads, validates, and renders the matrix.
3. Report compatibility metrics such as agent count, supported/planned agent states, feature support coverage, fallback coverage, and validation issue count.
4. Add focused tests in `tests/meta_workflow_guard/test_codex_task.py`.
5. Update registry/integration docs to point future agent additions at the matrix instead of stale prose-only assumptions.

This keeps Task 62 aligned with the portable foundation: static data plus validating/reporting logic, not a live service.

## Non-Goals

- Do not build an MCP server for installation or runtime negotiation in this task. A future installer/MCP can consume the compatibility matrix, but the matrix must exist first.
- Do not modify the Claude runtime gates unless validation proves a current gap.
- Do not duplicate Task 13 template path compatibility.
- Do not implement automatic agent transformations that mutate files. Transformations are recorded as compatibility metadata in this task.
- Do not introduce a new cross-agent state store.

## Planned Files

- `templates/registry/agent-compatibility-matrix.json`
- `scripts/codex-task`
- `tests/meta_workflow_guard/test_codex_task.py`
- `templates/registry/index.md`
- `templates/integration/guides/adding-agents.md`
- Task 62 work-tracking, plan, session, and Taskmaster artifacts

## Evidence Plan

- `python3 scripts/codex-task agent compatibility-report --report-file ... --runbook-file ...`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest tests/meta_workflow_guard/test_codex_task.py`
- `python3 scripts/codex-task plan sync`
- `python3 scripts/codex-task work-tracking audit`
- `python3 scripts/codex-guard validate --include-untracked`
- `git diff --check`

## Decision

Proceed with a file-backed compatibility matrix and report helper. This satisfies the historical Task 62 acceptance language by making capabilities, contract versions, feature flags, fallbacks, transformations, validation, tests, and metrics explicit and testable without overbuilding a runtime protocol.
