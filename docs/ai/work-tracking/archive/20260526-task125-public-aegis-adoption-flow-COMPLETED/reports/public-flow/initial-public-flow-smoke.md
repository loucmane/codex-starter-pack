# Initial Public Flow Smoke

Date: 2026-05-26
Branch: `feat/task-125-public-aegis-adoption-flow`

## Automated Regression

Command:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_installer.py tests/meta_workflow_guard/test_aegis_mcp_server.py tests/meta_workflow_guard/test_aegis_native_mcp_registration.py tests/meta_workflow_guard/test_aegis_invocation_contract.py tests/meta_workflow_guard/test_aegis_release_distribution.py
```

Result:

```text
109 passed, 3 skipped in 23.91s
```

## Fresh Project Smoke

Target:

```text
/tmp/aegis-task125-fresh-jcBagV
```

Commands:

```bash
git init -b main
/home/loucmane/codex/.venv/bin/aegis init
/home/loucmane/codex/.venv/bin/aegis start "Improve BrandMark accessibility"
bash .claude/scripts/readiness.sh --quick
/home/loucmane/codex/.venv/bin/aegis next
```

Observed:

- `aegis init` returned `status: initialized`.
- `aegis start "Improve BrandMark accessibility"` returned `status: started`.
- Local task allocated: `.aegis/state/local-tasks.json`, id `1`.
- Branch created: `feat/task-1-improve-brandmark-accessibility`.
- Readiness returned `READY | task=1`.
- `aegis next` returned phase `scope`, state `scope_required`, and suggested scope logging before source edits.
- Taskmaster and Serena were absent and marked not required.

## Existing Project Smoke

Target:

```text
/tmp/aegis-task125-existing-PDDr2o
```

Commands:

```bash
git init -b main
printf '%s\n' '# Existing Project Instructions' '' '- Keep this exact instruction.' > CLAUDE.md
/home/loucmane/codex/.venv/bin/aegis init
rg -n "Keep this exact instruction|Existing Project Instructions|AEGIS:BEGIN claude-runtime" CLAUDE.md
find . -maxdepth 2 \( -name '*.bak' -o -name '*.orig' -o -name '*.backup' \) -print
bash .claude/scripts/readiness.sh --quick
```

Observed:

- `aegis init` returned `status: initialized`.
- Existing `CLAUDE.md` content was preserved under the Aegis managed block:
  - `<!-- AEGIS:BEGIN claude-runtime -->` at line 1.
  - `## Existing Project Instructions` at line 53.
  - `- Keep this exact instruction.` at line 57.
- No `.bak`, `.orig`, or `.backup` sidecar files were created.
- Readiness correctly returned `BLOCKED | blocked=1 | first=branch 'main' does not contain a task ID` before local work was started.

## Current Gap

The public CLI and MCP-control-plane wrappers are implemented and smoke-tested. The remaining acceptance proof is a fresh Claude no-large-prompt session in a target initialized by `aegis init`, where Claude receives only a normal task request and uses installed files/hooks to run `aegis start`, implementation, S:W:H:E logging, verification, closeout, and handoff.
