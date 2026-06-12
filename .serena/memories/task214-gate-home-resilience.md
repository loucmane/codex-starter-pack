# Task 214 — Gate resilience when home dir is unresolvable (2026-06-12)

HP-Coach dogfood incident: PreToolUse hooks executed in Claude Code's sandboxed bash
environment (HOME stripped, no passwd entry for the uid) made `Path.home()` raise
`RuntimeError: Could not determine home directory`, and the gate failed closed — a
hard block on a tasks.json write even though enforcement was ADVISORY, with no
traceback to diagnose from.

## Fixes
- `ledger_lib._state_base`: fallback chain XDG_STATE_HOME > HOME env > Path.home()
  (wrapped) > `$TMPDIR/aegis-state-<uid>`; ledger path resolution can no longer raise
  RuntimeError.
- `gate_lib.safe_expanduser`: survives unexpandable `~` (returns the literal, which
  never matches repo-relative protected paths); applied at normalize_path,
  target_dir_confinement_violation, _path_for_evidence, and the settings-hook check.
- `degraded_pretooluse_fallback`: ADVISORY mode now records a
  `degraded_advisory_allow` event (action_class mutation_or_unsafe, with traceback)
  and allows loudly (DEGRADED-ADVISORY stderr) — advisory never hard-blocks, even on
  infra failure. STRICT keeps failing closed but now prints the full traceback and
  the degraded event carries `traceback`.

## Repro technique (kept in tests)
`tests/claude_adapter/test_gate_home_resilience.py` — in-process monkeypatch of
`pathlib.Path.home`/`expanduser`, plus an end-to-end subprocess run with a
`sitecustomize.py` on PYTHONPATH that makes Path.home() raise (simulates the sandbox;
env -u HOME alone does NOT reproduce because pwd-database fallback resolves home).

## Note
The exact unwrapped call site in HP-Coach's stack was never pinpointed locally; the
hardening covers the whole class, and the traceback capture means any recurrence
self-diagnoses. If a DEGRADED-ADVISORY event appears in a ledger/degraded-events.json,
read its `traceback` field.
