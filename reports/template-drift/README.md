# Template Drift Reports

This directory stores repo-level outputs from:

```bash
python3 scripts/codex-guard drift-check
```

## Output files

- `summary-<timestamp>.txt` — human-readable drift summary
- `summary-<timestamp>.json` — machine-readable drift payload for automation

## Scope

The current Task 95 implementation reports drift for:

- canonical guidance documents used by the guard's GAC validation
- template metadata policy coverage and missing required frontmatter keys
- required `codex-guard` command-surface availability

Task-local evidence for the feature rollout stays under the Task 95 active work-tracking folder. This directory is the reusable repo-level location for ongoing drift audits and future automation.
