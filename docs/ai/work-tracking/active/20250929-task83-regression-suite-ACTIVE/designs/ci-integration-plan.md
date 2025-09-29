# Task 83 – Meta Workflow Guard CI Integration Plan

## Objectives
- Guarantee the registration + integration regression suites (Task 83) execute automatically in CI.
- Block template merges when the guard or regression suites fail.
- Capture guard/test artefacts as CI artefacts for plan-step-verify evidence.

## Pipeline Overview
| Stage | Command | Purpose | Notes |
|-------|---------|---------|-------|
| Checkout | `actions/checkout@v4` | Pull repository | Pin to commit SHA for PRs |
| Python Setup | `actions/setup-python@v5` (`python-version: '3.11'`) | Align with local guard runtime | Optional cache via `pip cache` |
| Install | `pip install -r requirements-ci.txt` (fallback to `requirements.txt`) | Ensure pytest + guard deps available | Guard only needs stdlib, tests require `pytest` |
| Unit Suite | `python3 -m unittest tests.meta_workflow_guard.test_registration` | Enforce registration coverage | Fails on metadata drift |
| Integration Suite | `python3 -m unittest tests.meta_workflow_guard.test_guard_integration` | Exercise codex-guard behaviour | Uses temporary session file |
| Guard | `python3 scripts/codex-guard validate --include-untracked` | Verify plan compliance / tracker sync | Requires plan + tracker on branch |
| Artefacts | Upload `reports/meta-workflow-guard/` | Persist guard/test outputs | Use `actions/upload-artifact@v4` |

## Workflow Skeleton (`.github/workflows/meta-workflow-guard.yml`)
```yaml
name: Meta Workflow Guard

on:
  pull_request:
    paths:
      - 'templates/**'
      - 'scripts/codex-guard'
      - 'tests/meta_workflow_guard/**'
      - 'docs/ai/work-tracking/**'
      - 'plans/**'
  push:
    branches: [main]

jobs:
  guard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install test deps
        run: |
          if [ -f requirements-ci.txt ]; then pip install -r requirements-ci.txt; fi
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
      - name: Run registration suite
        run: python3 -m unittest tests.meta_workflow_guard.test_registration
      - name: Run integration suite
        run: python3 -m unittest tests.meta_workflow_guard.test_guard_integration
      - name: Run Codex Guard
        run: python3 scripts/codex-guard validate --include-untracked
      - name: Upload guard artefacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: meta-workflow-guard-logs
          path: reports/meta-workflow-guard/
```

## Failure Handling
1. Job failure comments link to `templates/engine/enforcement/meta-workflow-guard-remediation.md`.
2. Require PR authors to update plan/tracker (`python3 scripts/codex-task plan sync`) before rerunning.
3. Store artefacts even on success (for auditing).
4. If guard fails due to missing plan, instruct developer to create plan (`templates/workflows/processes/plan-template.md`).

## Local Automation
- Document `pre-commit` hook: `python3 scripts/codex-guard validate --include-untracked` (already defined in enforcement plan).
- Encourage `make guard` wrapper (future enhancement) to standardise local execution.

## Evidence & Storage
- CI job uploads artefacts; work-tracking snapshots guard/test outputs under `reports/meta-workflow-guard/guard/` + `tests/`.
- Plan evidence list updated to include this design document for Task 83.

## Rollout Steps
1. Add workflow file + optional `requirements-ci.txt` stub.
2. Update CODEX.md / README with CI instructions.
3. Add branch protection rule requiring `Meta Workflow Guard` job.
4. Monitor first week of runs; log findings in FINDINGS.md + tracker.

## Open Questions
- Do we need matrix builds for different Python versions? (TBD post Task 83).
- Should guard artefacts be pruned automatically to save CI storage? (Follow-up).

