# 2026-06-11 Task 201 break-glass recovery contract (Phase 0 finale)

gate_lib RECOVERY_CONTRACT maps block reason -> tier/repair/audit/escalation/eligibility;
recovery_block_suffix appends to every block. aegis override --reason mints a one-shot,
TTL 15m, 3/day rate-limited, reason-class-scoped token; gate consumes only for
readiness_blocked/pending_tracking (tier a/b), single use, ledger override event;
tier-c (observation/protected/adversarial) never eligible. override sanctioned while
BLOCKED. docs/aegis/RECOVERY_CONTRACT.md. Phase 0 (#195/#197/#200/#201) done; only
falsifier-gated capsule PR-3/PR-4 remain.
