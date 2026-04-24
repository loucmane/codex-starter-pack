# Task 95 Template Drift Detection Design

## Purpose

Translate the older drift-detection draft into a concrete implementation plan for the current repository. The original draft assumed a future `scripts/codex-guard drift-check` command; Task 95 makes that command real and defines what it should detect, how it reports drift, and where evidence should live.

## Current Baseline

- The live `scripts/codex-guard` surface currently exposes only `validate`.
- Template enforcement already depends on canonical template metadata, guard validation, and stored evidence.
- Taskmaster Task 95 expects stored drift reports under `reports/template-drift/` and automation/guard integration.

## Scope For First Implementation

Task 95 should implement deterministic drift detection around the repository's template and canonical-document contract, not speculative AST matching for arbitrary files.

### Detectable drift classes

1. **Canonical document drift**
   - Compare the set of canonical GAC/behavior/template docs referenced by guard rules against the docs that actually exist.
   - Flag deprecated docs that are still treated as canonical by configuration.

2. **Template metadata drift**
   - Validate that files covered by `templates/metadata/template-metadata-policy.json` still satisfy the expected frontmatter contract.
   - Report missing metadata keys and missing frontmatter as drift findings instead of only guard failures.

3. **Workflow surface drift**
   - Compare the command/help surface promised by docs or drafts against the live helper/guard command set where the mapping is explicit.
   - Use this narrowly for the Task 95 scope; do not infer broad repo semantics from free-form prose.

## Command Contract

Implement a new command:

```bash
python3 scripts/codex-guard drift-check
```

Expected behavior:

- scan the defined drift sources
- print a human-readable summary to stdout
- optionally emit JSON for automation
- return nonzero when configured blocking drift is present

Suggested flags:

- `--json-out <path>`
- `--report <path>`
- `--strict`

## Reporting

Store repo-level drift outputs under:

- `reports/template-drift/summary-<timestamp>.txt`
- `reports/template-drift/summary-<timestamp>.json`

Store task-local verification evidence under:

- `docs/ai/work-tracking/active/20260424-task95-template-drift-detection-ACTIVE/reports/template-drift-detection/`

## Integration Boundary

- Task 95 adds the drift-check command, report generation, and documentation for automation.
- Task 95 should not implement the future wizard or dashboard features; those belong to Tasks 96 and 97.
- Task 95 should reuse `scripts/codex-guard` and existing tests in `tests/meta_workflow_guard` rather than creating a second enforcement toolchain.

## Immediate Next Steps

1. Add the new `drift-check` parser entry and reporting structures to `scripts/codex-guard`.
2. Create focused tests covering empty drift, metadata drift, and canonical-doc drift.
3. Add `reports/template-drift/README.md` describing how stored reports are generated and consumed.
4. Document the expected automation path for CI or scheduled runs.
