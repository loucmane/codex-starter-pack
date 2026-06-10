# Aegis Recovery Contract (TM #201)

Every BLOCKED state Aegis emits carries, inline, a recovery contract: a copyable safe
repair, a blast-radius tier, an audit destination, and an escalation path. The mapping
lives in `gate_lib.py` (`RECOVERY_CONTRACT` / `recovery_contract()`); the block message
appends it via `recovery_block_suffix()`.

## Blast-radius tiers
- **a** — interior workflow bookkeeping (pending tracking). Break-glass eligible.
- **b** — workflow-state surfaces (readiness BLOCKED on branch/session/plan/folder).
  Break-glass eligible.
- **c** — boundaries: observation mode, protected paths, adversarial/destructive,
  outward actions. **Never** break-glass eligible.

## Break-glass: `aegis override --reason "<why>"`
Mints a **one-shot, TTL-bounded, rate-limited** token honored by the PreToolUse gate
**only** for tier-a/b reasons (`readiness_blocked`, `pending_tracking`):
- single use — consumed on the next matching mutation, then gone;
- TTL (default 15 min) and a daily rate limit (default 3) — see `--ttl-minutes`,
  `--max-per-day`;
- `--reason-class` scopes the token to one reason; default `any` eligible class;
- every consumption is recorded as an `override` event in the ledger
  (reason class, note, minter, mint time) — bypasses are loud, not silent;
- minting itself is a sanctioned action that runs while BLOCKED (it only writes the
  token file; it does not perform the user's mutation).

It is **not** a generic bypass: tier-c blocks ignore the token entirely (proven by the
observation-boundary and protected-path tests, and the replay adversarial corpus).

## Why this shape
Generalizes the proven #190 carve-out (safe repair while BLOCKED) without making every
gate advisory: the recovery valve is bounded to the exact class of false positives the
HP-Coach deployment hit (E04/E05/E08/E10/E17 — workflow-state blocks), while the teeth
that caught real issues (observation dirty-tree, protected paths) stay un-bypassable.
