# Targeted Taskmaster Generation Design

## Scope
Task 104 adds a targeted Taskmaster task-file generation helper so workflow commands can update the current task file without running broad in-place `task-master generate` and dirtying unrelated `.taskmaster/tasks/task_*` files.

Primary command:

```bash
python3 scripts/codex-task taskmaster generate-one --id <task-id>
```

## Current Behavior
- Taskmaster CLI version: `0.43.1`.
- `task-master set-status --id=104 --status=in-progress` updates `.taskmaster/tasks/tasks.json` but does not update `.taskmaster/tasks/task_104.txt`.
- `task-master generate --output /tmp/...` succeeds without touching the repo task-file directory.
- With Taskmaster `0.43.1`, `task-master generate --output /tmp/...` emits `task_*.md` files even though this repository currently tracks `task_*.txt` files.
- Broad in-place `task-master generate` is unsafe in this repo because it can create or dirty many generated files unrelated to the current task.
- `python3 scripts/codex-task wizard kickoff` currently calls broad `task-master generate`; Task 104 must replace that with targeted generation before the wizard is safe for future Taskmaster `0.43.1` workflows.

## Helper Contract
The helper should:

1. Validate the requested task ID.
2. Snapshot the current git status for `.taskmaster/tasks/task_*` files before generation.
3. Run `task-master generate --output <temporary-directory>` instead of in-place generation.
4. Locate the generated task file for the requested ID in the temporary directory.
5. Support Taskmaster output extensions:
   - Prefer `task_<id>.txt` when present.
   - Accept `task_<id>.md` when Taskmaster emits markdown.
   - Write to the existing repository task-file path when one exists, preserving the repo's current extension (`task_<id>.txt` in this project).
   - For a new task with no existing generated file, default to the extension produced by Taskmaster unless project policy later requires a configured extension.
6. Copy or convert only the requested generated task file into `.taskmaster/tasks/`.
7. Fail if unrelated `.taskmaster/tasks/task_*` paths changed during the command.
8. Leave the temporary generation directory cleaned up unless a debug flag is added later.
9. Print the updated task-file path so session/tracker entries can cite it.

## Compatibility Rule
For this repository, `task-master generate --output` currently produces markdown files with normal markdown headings and bold labels. The tracked `task_*.txt` files use comment-prefixed metadata headers. Task 104 should not assume the extension alone describes the content format.

Minimum viable behavior:
- Copy generated `task_<id>.md` content into the existing `.taskmaster/tasks/task_<id>.txt` only if tests and guard accept the generated markdown body in the `.txt` file, or add a deterministic markdown-to-current-text conversion layer.
- The safer default is a conversion layer for existing `.txt` files so Task 104 does not silently churn the entire generated-task format.

## Test Matrix
- Existing `.txt` repo task file + temp-generated `.md` source updates only the requested `.txt` path.
- Existing `.md` repo task file + temp-generated `.md` source updates the requested `.md` path.
- Existing `.txt` repo task file + temp-generated `.txt` source updates the requested `.txt` path.
- Missing generated requested task file fails with a clear error.
- Unrelated repo task files dirty before invocation cause a clear failure unless an explicit flag is added later.
- Unrelated repo task files remain unchanged after invocation.
- `codex-task wizard kickoff` uses the targeted helper instead of broad `task-master generate`.
- Work-tracking scaffold tolerates a clean between-session repo where `docs/ai/work-tracking/active/` is absent.

## Documentation Updates
- `templates/TOOLS.md` should advertise the targeted Taskmaster helper.
- `templates/workflows/taskmaster/work-tracking-enforcement.md` and `templates/workflows/taskmaster/alignment.md` should instruct agents to run targeted generation after status-only Taskmaster updates.
- `templates/engine/validation/foundation-adoption-guide.md` should avoid recommending broad generation as a default status-update step.

## Open Decisions
- Whether to keep generated task files as `.txt` long term or migrate the repository to Taskmaster `0.43.1` markdown output belongs in a separate migration decision. Task 104 should avoid a repository-wide generated-file format migration.
- Whether to add a persistent project config for task-file extension should be decided only if tests show existing-path detection is insufficient.
