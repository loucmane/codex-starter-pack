# Task 199 Aegis enforce advisory mode – Implementation Notes

## Planned Workstreams
- Added `.aegis/state/enforcement.json` as the strict/advisory mode state surface. Missing file remains strict for backward compatibility.
- Added `aegis enforce status` plus `aegis enforce --mode advisory|strict --reason ...` to both the package CLI and `scripts/codex-task aegis` wrapper.
- Updated PreToolUse and Stop hook behavior so advisory mode evaluates the existing strict gate path but records `would_block` decisions to `.aegis/reports/gate-decisions.jsonl` and exits 0.
- Tagged PostToolUse pending tracking events with the active enforcement mode.
- Surfaced enforcement mode through `aegis status`, `aegis doctor`, and `aegis verify`; doctor reports advisory as a non-required warning/degraded state, not green-and-silent.
- Mirrored hook and installer changes into packaged Aegis assets.

## Verification
- `python3 -m py_compile .claude/scripts/gate_lib.py scripts/_aegis_installer.py aegis_foundation/cli.py scripts/codex-task tests/claude_adapter/test_pretooluse_gates.py tests/meta_workflow_guard/test_aegis_installer.py`
- `PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/claude_adapter/test_pretooluse_gates.py -q` → 131 passed.
- `PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_installer.py -q` → 97 passed, 1 skipped.
- `uv run ruff check --extend-ignore E402 ...` on touched files → passed. E402 is ignored because `scripts/codex-task` intentionally bootstraps `sys.path` before local imports.
- Asset parity: live and packaged `gate_lib.py` matched; source and packaged `_aegis_installer.py` matched.
- Live CLI smoke on `/tmp/aegis-enforce-smoke.*`: default status strict, set advisory, then `aegis status` reported advisory.
