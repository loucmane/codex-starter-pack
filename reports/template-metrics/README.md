# Template Metrics Dashboard Reports

This directory stores the repo-level dashboard outputs from:

```bash
python3 scripts/template-metrics-dashboard
```

## Output files

- `latest.md` - human-readable metrics snapshot
- `latest.json` - machine-readable metrics payload for automation

## Scope

The current Task 97 implementation reports:

- Taskmaster task counts and focus-chain status for Tasks 94-102
- template metadata compliance coverage using the existing `codex-guard` helpers
- latest drift summary information from `reports/template-drift/`
- work-tracking active/archive turnover
- plan-sync activity from `.plan_state/sync.log`
- wizard kickoff adoption inferred from session logs

Task-local evidence for the Task 97 rollout stays under the Task 97 active work-tracking folder. This directory is the reusable repo-level location for ongoing dashboard refreshes and CI artifacts.
