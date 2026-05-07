# Task 104 Targeted Taskmaster Task-File Generation Helper – Implementation Notes

## Planned Workstreams
- `scripts/codex-task`
  - Added `taskmaster generate-one --id <task-id>`.
  - Runs `task-master generate --output <temporary-directory>` and copies only the requested task file back into `.taskmaster/tasks/`.
  - Preserves an existing repository task-file extension (`.txt` in this repo) while accepting Taskmaster `0.43.1` generated `.md` output.
  - Converts Taskmaster markdown metadata into the existing comment-prefixed `.txt` task-file format for existing `.txt` files.
  - Fails before and after generation when unrelated generated task files are dirty.
  - Updated `wizard kickoff` to call the targeted helper instead of broad in-place `task-master generate`.
  - Hardened `work-tracking scaffold` so a clean between-session repo can recreate the missing `active/` parent directory.
- Tests
  - Added parser coverage for `taskmaster generate-one`.
  - Added targeted generation tests covering existing `.txt` destination with generated `.md` source, unrelated dirty task-file failure, missing generated task-file failure, and clean-state scaffold parent creation.
  - Updated wizard kickoff tests to assert targeted generation with `--output`, not broad generation.
- Documentation/templates
  - Updated Codex/Taskmaster workflow docs and Claude command docs to prefer `python3 scripts/codex-task taskmaster generate-one --id <id>` after status/update commands.
  - Documented broad `task-master generate` as an explicitly scoped repository-wide refresh, not the default follow-up to ordinary status changes.
