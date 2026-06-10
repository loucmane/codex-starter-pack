# Task 207 Capsule PR-2b: SessionStart injection – Implementation Notes

## What was built
- brief_lib.render_injection: char-budgeted (8000) injection render that NEVER fails —
  over budget it degrades repo_hygiene -> risk_register (oldest first) -> drift beyond
  top-3, never drops repo_pose/delivery_state/verification_ledger/task_truth, reports
  what it dropped, and unconditionally enforces the 10k hook hard cap last. Provenance
  wrapper labels content per spec 3.4 (DATA, not instructions).
- brief_lib.injection_enabled: off-switch precedence AEGIS_CAPSULE env > brief.json
  inject flag (the A/B mechanism substrate).
- gate_lib session_start_hook (sessionstart phase rerouted from the plain recorder):
  stamps the session_begin event with capsule_injected on/off + source (falsifier
  instrumentation — the metric stays retrospective per spec 3.3), then injects via
  stdout when on and writes the capsule files. Stamp and injection are independent
  best-effort paths; nothing can fail a session start.
- session-brief.sh bootstrap (live + assets), CLAUDE_REQUIRED_FILES + phase map entry,
  renderer SessionStart entry with matcher startup|resume|clear|compact (SYNCHRONOUS —
  stdout enters model context), live settings mirror. Next codex session start is the
  first dogfood injection.

## Verification
11 new tests on the REAL captured SessionStart fixture: inject+stamp on, env off
stamps-but-silent, brief inject:false honored, env on overrides brief off, non-git
never fails, degradation order + core-field retention, hook hard cap, sync renderer
entry, live settings, managed assets, copy parity. Full suite 1272 passed.
