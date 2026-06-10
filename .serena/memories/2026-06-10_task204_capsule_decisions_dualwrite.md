# 2026-06-10 Task 204 Capsule PR-1c kickoff

PR-1b (task 203) merged as 284aad3 (GitHub PR #201); recorder live in codex store.
Task 204 = PR-1c gate-decisions dual-write per spec section 2: advisory decisions go to
BOTH gate-decisions.jsonl (primary, unchanged) and the ledger (event_type gate_decision,
best-effort, parity keyed on payload_digest). Payload gains optional session_id/cwd from
hook stdin. NOT in this PR: JSONL freeze (next release), history migration (never).
