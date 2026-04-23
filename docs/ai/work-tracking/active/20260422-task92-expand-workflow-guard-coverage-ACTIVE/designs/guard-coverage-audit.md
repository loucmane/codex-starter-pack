# Task 92 Guard Coverage Audit

## Audit Timestamp
- 2026-04-22 17:35 CEST

## Starting Questions
- Which workflow guard gaps remain after Tasks 89 and 91?
- Which gaps are repo-specific versus candidates for cross-project foundation work?
- Which gaps belong in Task 92 versus new follow-on backlog items?

## Initial Notes
- Task 92 remains the correct next implementation task because it directly extends the enforcement work completed in Tasks 89 and 91.
- The broader cross-project foundation work from Task 91 should not be folded into Task 92 itself; it now lives in follow-on Tasks `98`–`102`.
- The first audit pass should distinguish immediate repo guard gaps from portability items that belong in the new follow-on tasks.

## Prioritized Gaps
1. **Runtime artifact commits**
   - The guard did not prevent accidental commits of generated `__pycache__` files or Codex sqlite runtime artifacts.
   - This caused avoidable cleanup during Task 91 and is a good low-risk, high-value enforcement target.
2. **Taskmaster state changes without matching evidence**
   - `.taskmaster/tasks/tasks.json` and generated task files can change without guaranteed same-day tracker/session evidence.
   - This is directly related to earlier drift and interrupted status updates.
3. **Future candidate slices**
   - Session rollover consistency after same-day task switches.
   - Commit-prep consistency around GAC-related workflow expectations.

## Initial Implementation Slice
- Add runtime-artifact validation for `__pycache__/`, `.pyc`/`.pyo`, and `.codex` sqlite runtime files.
- Require Taskmaster activity evidence in the current session and active tracker when `.taskmaster/tasks/tasks.json` or `task_<id>.txt` files change.

## Implemented Guard Coverage
- Runtime-artifact validation now blocks generated Python bytecode/cache files and Codex sqlite runtime artifacts from being committed.
- Taskmaster activity validation now requires same-day evidence in the current session and active tracker whenever `.taskmaster/tasks/tasks.json` or generated `task_<id>.txt` files change.
- Session-state validation now keeps `sessions/current`, `sessions/state.json`, and paused-session references aligned whenever session files/state are touched.
- GAC/commit-prep validation now enforces the canonical response-mode distinction in core commit-prep docs:
  - `full-gac-command` for requests that ask for the complete `gac "..."` command.
  - `message-payload-only` for requests that ask for a commit message or validation only.
- GAC/commit-prep validation now requires canonical multiline examples to include a `Summary:` block before bullets and `Work tracking:`.
- Recovery validation now permits multiple completed session files from the latest prior date, closing the interrupted-session carryover case without allowing arbitrary historical session edits.

## Regression Coverage
- `tests/meta_workflow_guard/test_guard_rules.py` covers runtime-artifact detection.
- The same suite covers Taskmaster evidence enforcement for session/tracker logging.
- The same suite covers `sessions/state.json` mismatch, current-in-paused, and missing paused-session references.
- The same suite covers GAC response-mode markers and canonical multiline `Summary:` enforcement.
- The same suite covers multiple completed sessions from the latest prior date.
