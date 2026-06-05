# Task 163 Update GitHub Actions for Node 24 runner transition – Implementation Notes

## Planned Workstreams
- Added `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: "true"` as top-level workflow env in:
  - `.github/workflows/ci.yml`
  - `.github/workflows/codex-guard.yml`
  - `.github/workflows/meta-workflow-guard.yml`
- Preserved action versions for the low-behavior-change transition:
  - `actions/checkout@v4`
  - `actions/setup-node@v4`
  - `actions/setup-python@v4` / `actions/setup-python@v5`
  - `actions/upload-artifact@v4`
- Preserved Taskmaster CLI runtime identity with `node-version: "22"`.
- Added workflow contract tests requiring the Node 24 JavaScript-action opt-in and preventing accidental `upload-artifact@v5` migration in this task.
