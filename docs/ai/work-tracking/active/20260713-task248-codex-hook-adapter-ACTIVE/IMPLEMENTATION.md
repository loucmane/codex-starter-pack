# Task 248 Implement First-Class Codex Hook Adapter – Implementation Notes

## Runtime

- Added canonical `apply_patch` to the hookable and mutation tool sets in both live and
  packaged `gate_lib.py`.
- Added a strict parser for `*** Begin Patch` / `*** End Patch` and Add, Update, Delete,
  and Move headers. The parser rejects duplicate, empty, malformed, ambiguous, unsupported,
  absolute, escaping, and symlink-escaping paths.
- Evaluates every normalized source and destination path for readiness, observation,
  protected-path, workflow-owned-path, strict/advisory, and degraded fail-closed behavior.
  A safe first path cannot mask a guarded later path.
- Emits one atomic `codex:apply_patch` pending event with the primary evidence path, every
  affected path, ordered operation metadata, and a deterministic SHA-256 patch digest.
- Emits matching passive-ledger PostToolUse evidence and diagnostic evidence for malformed
  successful payloads.

## Managed Codex adapter

- Added installer-owned `.codex/hooks.json` with PreToolUse, two PostToolUse hooks,
  SessionStart, and Stop. Dispatch resolves the Git root and sets
  `AEGIS_INVOKING_AGENT=codex` independently of whether Claude is enabled.
- Codex-only installs receive the shared runtime without `CLAUDE.md` or
  `.claude/settings.json`; multi-agent installs reuse one shared runtime without duplicate
  manifest entries.
- Added exact-byte semantic adoption for equivalent unowned hook files. Any semantic
  difference remains a manual-review refusal for install/update.
- Added per-agent reload markers and Codex-specific `/hooks` exact-definition/hash trust
  guidance. The installer never bypasses hook trust.
- Generalized post-init guidance so Claude-only, Codex-only, and multi-client installs name
  the correct restart/reconnect action.

## Contracts and distribution

- Promoted Codex from planned to implemented in the adapter contract.
- Expanded profile and foundation-manifest schemas with Codex files, hook registrations,
  gate IDs, entrypoint, and managed verification records.
- Kept runtime, installer, schemas, and adapter contract byte-identical to their packaged
  assets.

## Verification implemented

- Added parser, policy, degraded-mode, protected/workflow-path, all-path, pending-event,
  digest, and malformed-payload regressions.
- Added installer idempotence, adoption/refusal, schema, source/package parity, Codex-only,
  and multi-agent regressions.
- Ran a real Codex 0.144.3 smoke after reviewing and trusting the exact hook hashes through
  `/hooks`; evidence is in
  `reports/codex-hook-adapter/live-codex-0.144.3-smoke.md`.
