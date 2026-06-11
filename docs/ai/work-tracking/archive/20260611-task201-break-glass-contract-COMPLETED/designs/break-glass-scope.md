# TM #201 scope — break-glass recovery contract

Task text: every BLOCKED state includes a copyable safe repair + reason + blast-radius
tier + audit destination + escalation; add aegis override --reason rate-limited
break-glass with attribution + immutable evidence; replay fixtures prove recovery
resolves historical deadlocks AND does not become a generic bypass for source edits /
destructive commands / external deployments.

## Implemented
- RECOVERY_CONTRACT in gate_lib maps each block reason -> {tier a/b/c, copyable repair,
  alt repair, audit destination, escalation, override_eligible}; recovery_block_suffix
  appends it to every block message (all gate_block_or_record callers inherit it).
- aegis override --reason mints a one-shot, TTL-bounded (15m), rate-limited (3/day)
  token (.aegis/state/override-token.json) with reason-class scoping; minted-by +
  note + timestamps recorded.
- The PreToolUse gate consumes the token ONLY for override-eligible reasons
  (readiness_blocked, pending_tracking = tier a/b); single use; every consumption
  recorded as a ledger `override` event. Tier-c blocks (observation boundary, protected
  paths, adversarial) ignore the token entirely.
- override is a sanctioned action allowed while BLOCKED (it only writes the token file).
- Replay corpus: must-allow override-mint-while-blocked; adversarial protected-path
  write still blocks. docs/aegis/RECOVERY_CONTRACT.md documents the contract.

## Out of scope
Human-token tier-c break-glass (spec P6 future; tier-c stays human-approval via GitHub
/ platform); per-row crypto on the audit log (chain was killed program-wide).
