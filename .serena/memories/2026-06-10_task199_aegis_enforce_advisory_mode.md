# Task 199 Aegis enforce advisory mode

Implemented the upstream sanctioned advisory enforcement mode for Aegis.

Key changes:
- Added `.aegis/state/enforcement.json` as the mode state surface. Missing file means strict.
- Added `aegis enforce status` and `aegis enforce --mode advisory|strict --reason ...` in `aegis_foundation/cli.py`, `scripts/_aegis_installer.py`, and the `scripts/codex-task aegis` wrapper.
- Updated `.claude/scripts/gate_lib.py` so advisory mode records PreToolUse/Stop `would_block` decisions to `.aegis/reports/gate-decisions.jsonl` and exits 0, while strict mode behavior is unchanged.
- Tagged PostToolUse pending tracking events with `mode`.
- Surfaced enforcement mode in `aegis status`, `doctor`, and `verify`; doctor reports advisory as degraded/warning, not green-and-silent.
- Mirrored hook/installer changes into `aegis_foundation/assets/...`.

Verification:
- `python3 -m py_compile` on touched Python files passed.
- `PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/claude_adapter/test_pretooluse_gates.py -q` passed: 131 passed.
- `PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_installer.py -q` passed: 97 passed, 1 skipped.
- `uv run ruff check --extend-ignore E402 ...` on touched files passed; E402 is existing intentional `scripts/codex-task` sys.path bootstrap.
- Asset parity checks passed.
- Live CLI smoke on `/tmp/aegis-enforce-smoke.*`: default strict, set advisory, `aegis status` reports advisory.

HP-Coach acceptance after merge:
`./.aegis/bin/aegis enforce --mode advisory --reason "product work; program Phase 0"`
Re-enable:
`./.aegis/bin/aegis enforce --mode strict --reason "resume strict enforcement"`

Unrelated local drift not part of task: `.codex/config.toml`, `.agents/`, `.codex/agents/`, `.codex/hooks.json`, and `docs/aegis/AEGIS_VNEXT_PROGRAM.md`.