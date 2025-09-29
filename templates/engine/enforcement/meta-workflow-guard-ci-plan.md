---
id: meta-workflow-guard-ci-plan
type: enforcement-plan
category: ci
status: draft
version: 0.1.0
related:
  - templates/engine/enforcement/meta-workflow-guard-remediation.md
  - templates/workflows/processes/meta-workflow-authoring.md
  - templates/metadata/workflow-guards.json
---

# Meta Workflow Guard – CI & Pre-commit Wiring Plan

## 1. Goal
Ensure every workflow/template change executes the meta workflow guard automatically, both locally (pre-commit) and in continuous integration (CI), with clear remediation when checks fail.

## 2. Scope
- Applies to any change touching `templates/workflows/**`, `templates/handlers/**`, `templates/patterns/**`, or guard metadata.
- Enforces `python3 scripts/codex-guard validate --include-untracked` before commits and in CI.
- Integrates guard artefacts into `reports/meta-workflow-guard/`.

## 3. Pre-commit Strategy
### Required Hook
Add to `.pre-commit-config.yaml`:
```yaml
-   repo: local
    hooks:
      - id: codex-guard
        name: Codex Guard (meta workflow)
        entry: python3 scripts/codex-guard validate --include-untracked
        language: system
        types: [markdown, yaml, python]
        require_serial: true
        pass_filenames: false
```

### Local Workflow
1. Developer runs `pre-commit install`.
2. Hook triggers on staged changes; guard blocks if plan scope, branch policy, or remediation steps missing.
3. On failure, hook prints remediation URL:
   `templates/engine/enforcement/meta-workflow-guard-remediation.md`.
4. Allow emergency bypass via `SKIP_META_GUARD=1` environment flag, logged in tracker with justification.

## 4. CI Pipeline Plan (GitHub Actions example)
```yaml
jobs:
  meta-workflow-guard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install deps
        run: pip install -r requirements.txt || true
      - name: Run Codex Guard
        run: python3 scripts/codex-guard validate --include-untracked
      - name: Upload guard artefacts
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: meta-workflow-guard-logs
          path: reports/meta-workflow-guard/
```

### CI Behaviour
- Mandatory job for PRs touching templates/guard metadata.
- Job gates merges; failure comment links to remediation guide.
- Stores guard output under `reports/meta-workflow-guard/<timestamp>.txt` for audit.

## 5. Failure Handling
- Reference remediation guide (`meta-workflow-guard-remediation.md`).
- CI comment template:
  ```
  Meta Workflow Guard failed. Review plan scope, branch policy, and evidence.
  See templates/engine/enforcement/meta-workflow-guard-remediation.md.
  ```
- On repeated failures, escalate via Taskmaster task referencing guard failure.

## 6. Rollout Checklist
- [ ] Add pre-commit hook entry and document installation in README/plan.
- [ ] Update CI workflow (meta-workflow-guard job) and enforce branch protection rule.
- [ ] Announce change in changelog + handoff.
- [ ] Monitor first week of runs; collect feedback.

## 7. Open Questions
- Should guard skip on documentation-only changes? (Decision pending.)
- Combine with timestamp gate once Task 84 lands.

## 8. References
- Guard remediation: `templates/engine/enforcement/meta-workflow-guard-remediation.md`
- Plan compliance: `plans/2025-09-27-task82-meta-workflow.md`
- Taskmaster: Task 82 subtasks 82.5–82.7.
