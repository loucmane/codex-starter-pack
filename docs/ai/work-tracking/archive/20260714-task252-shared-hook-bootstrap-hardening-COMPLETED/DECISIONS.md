# Decisions

- 2026-07-14 — Target-installed hook runtime is the availability boundary; the central source checkout remains an update source and non-hook CLI fallback, not a per-hook dependency.
- 2026-07-14 — Missing PreToolUse/readiness/protected-path policy fails closed; passive evidence and Stop phases degrade open only for session availability, with one diagnostic per phase.
- 2026-07-14 — Installation activation is transactional and dependency-ordered. A failed apply restores old modified bytes and removes only files the plan created.
- 2026-07-14 — Legacy adoption is finite and syntax-aware. A path merely containing “Aegis” is not sufficient authority to overwrite a project hook.
- 2026-07-14 — Duplicate SessionStart registration is removed because the single `session_start_hook` already records lifecycle evidence and injects the computed capsule.
- 2026-07-14 — Task 252 does not edit operator-local `.codex/hooks.json`; downstream projects receive the fix only through a reviewed managed update after upstream merge.
