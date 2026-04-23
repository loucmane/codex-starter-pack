# Task 92 Expand Workflow Guard Coverage – Implementation Notes

## Planned Workstreams
- Guard audit and prioritization:
  - [x] Compare Task 92 against the Task 91 portability roadmap and split broader foundation work into follow-on Tasks `98`–`102`.
  - [x] Prioritize the first concrete guard gaps to implement.
- Guard implementation:
  - [x] Add runtime-artifact validation for generated `__pycache__/`, `.pyc`/`.pyo`, and `.codex` sqlite files.
  - [x] Require Taskmaster evidence in the current session and active tracker when `.taskmaster` state changes.
  - [x] Validate `sessions/state.json` consistency with `sessions/current` and paused-session references.
  - [x] Enforce canonical GAC/commit-prep guidance in the core templates (`full-gac-command`, `message-payload-only`, and multiline `Summary:` blocks).
- Verification:
  - [x] Expand `tests/meta_workflow_guard/test_guard_rules.py` for the new guard rules.
  - [x] Re-run `plan sync`, targeted pytest, and `codex-guard`.
  - [x] Document the expanded guard coverage in `templates/TOOLS.md` and `designs/guard-coverage-audit.md`.
  - [x] Capture final Task 92 documentation/regression evidence for `92.4` and `92.5`.
  - [x] Remediate CI guard failures by removing tracked bytecode, adding workflow plan sync, and making branch detection PR-aware.
