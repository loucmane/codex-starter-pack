# First-Pass Guidance Regression - 2026-05-24

## Scope
- Added explicit `next_action` guidance to Aegis kickoff, log, strict verify, and closeout responses so a fresh agent is steered through scope -> implement -> verify -> closeout without learning by failed closeout.
- Added best-effort `evidence_location` metadata to pending tracking events and `aegis log` responses. The canonical S:W:H:E token still uses stable evidence paths only; line/range details are side metadata for debugging.
- Mirrored runtime changes into packaged Aegis assets so MCP-installed projects receive the same hook and installer behavior.
- Updated MCP tool descriptions to name the required next action for kickoff/log/verify/closeout.

## Location Metadata Behavior
- `Write`: records the written file snapshot range, e.g. `path:1-14`.
- `Edit`: locates `tool_input.new_string` in the post-edit file and records a best-effort changed range.
- `MultiEdit`: records a combined best-effort range and individual ranges when `new_string` snippets can be located.
- `Bash` file writes and MCP path-bearing mutations: record a file snapshot range when the evidence resolves to a file.
- Command-only evidence, unreadable files, or non-deterministic surfaces do not fake line numbers.

## Verification
```text
python3 -m py_compile scripts/_aegis_installer.py aegis_foundation/assets/scripts/_aegis_installer.py .claude/scripts/gate_lib.py aegis_foundation/assets/.claude/scripts/gate_lib.py aegis_mcp/server.py aegis_foundation/cli.py
PASS
```

```text
git diff --check
PASS
```

```text
PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_mcp_server.py tests/meta_workflow_guard/test_aegis_schemas.py tests/meta_workflow_guard/test_aegis_installer.py
71 passed, 1 skipped
```

```text
PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py
16 passed, 1 skipped
```

```text
PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_installer.py tests/meta_workflow_guard/test_aegis_mcp_server.py tests/meta_workflow_guard/test_aegis_schemas.py tests/meta_workflow_guard/test_aegis_mcp_e2e_targets.py
88 passed, 2 skipped
```

## Result
Focused regression is green, including the MCP `aegis.verify` pending-evidence fix (`aegis:verify` -> `.aegis/reports/verification-report.json`). Task 121 still needs a fresh Claude-client acceptance retest to prove the new `next_action` guidance produces first-pass closeout without repair-loop logging.
