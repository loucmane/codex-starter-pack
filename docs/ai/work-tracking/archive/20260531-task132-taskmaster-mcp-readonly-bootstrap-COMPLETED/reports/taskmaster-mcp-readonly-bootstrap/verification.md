# Task 132 Verification

## Scope

Task 132 hardens the installed Claude/Aegis PreToolUse gate so read-only Taskmaster MCP discovery can run before Aegis kickoff while readiness is `BLOCKED`, without opening Taskmaster mutation paths.

## Focused Verification

Command:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/claude_adapter/test_pretooluse_gates.py tests/meta_workflow_guard/test_aegis_installer.py tests/meta_workflow_guard/test_aegis_mcp_contract_docs.py -q
```

Result:

```text
89 passed, 1 skipped in 10.26s
```

Coverage included:

- Allowed Taskmaster MCP discovery while readiness is `BLOCKED`: `help`, `get_tasks`, `next_task`, `get_task`.
- Both server-name spellings: `mcp__taskmaster_ai__*` and `mcp__taskmaster-ai__*`.
- Blocked Taskmaster MCP mutations while readiness is `BLOCKED`: status updates, task updates, subtask updates, add, expand, parse PRD, generate, dependency changes, moves.
- Blocked unknown Taskmaster MCP actions while readiness is `BLOCKED`.
- Existing post-closeout matching Taskmaster completion allowance.

## Full Regression

Initial command:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest -q
```

Initial result:

```text
1 failed, 811 passed, 4 skipped
```

The single failure was environmental: `scripts/template-ssot-scanner/test_cli_behavior.py::test_reference_fix_runner_rolls_back_with_git_restore` creates a temporary git commit, and this machine's global git config forced GPG signing. The non-interactive test process failed with `gpg: cannot open '/dev/tty'`.

Rerun command:

```bash
GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=commit.gpgsign GIT_CONFIG_VALUE_0=false PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest -q
```

Rerun result:

```text
812 passed, 4 skipped in 71.99s
```

## Guard Checks

Before marking Task 132 done:

```text
python3 scripts/codex-guard validate --include-untracked -> passed
python3 scripts/codex-guard drift-check --strict --report-dir "" -> 0 findings
git diff --check -> passed
python3 scripts/codex-task taskmaster health -> OK
```

Task completion:

```text
task-master set-status --id=132 --status=done -> done
python3 scripts/codex-task taskmaster generate-one --id 132 -> refreshed task_132.md
```

Final post-completion pass:

```text
python3 scripts/codex-guard validate --include-untracked -> passed
python3 scripts/codex-guard drift-check --strict --report-dir "" -> 0 findings
git diff --check -> passed
python3 scripts/codex-task taskmaster health -> OK, statuses: done=132
```
