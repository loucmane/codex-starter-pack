# Task 201 break-glass recovery contract – Implementation Notes

- RECOVERY_CONTRACT (gate_lib): per-reason {tier, repair, alt_repair, audit, escalation,
  override_eligible}; recovery_block_suffix() appends it to every block message, so all
  gate_block_or_record callers gain the contract inline.
- aegis override --reason: one-shot token at .aegis/state/override-token.json, TTL 15m,
  rate-limited 3/day (override-rate.json), reason-class scoped; minter/note/timestamps.
- gate consumes the token only for readiness_blocked / pending_tracking (tier a/b),
  single use, recording a ledger `override` event; tier-c blocks ignore it. override
  sanctioned while BLOCKED (writes token only). docs/aegis/RECOVERY_CONTRACT.md.
- Tests: 10 break-glass tests (contract coverage, message suffix, one-shot unblock,
  audit event, observation/protected-path no-bypass, reason-class scoping, rate limit,
  mint-while-blocked, classification, copy parity) + 2 replay corpus entries. Full
  suite green.
