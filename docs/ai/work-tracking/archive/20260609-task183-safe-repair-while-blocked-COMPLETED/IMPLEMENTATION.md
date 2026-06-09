# Task 183 Allow safe Aegis repair while readiness is blocked – Implementation Notes

## Implemented
- Added `bash_is_aegis_repair_apply()` for a strict single-segment Bash repair allowance. It accepts trusted project Aegis invocations with `repair --apply` and rejects compound commands such as `repair --apply && touch state.txt`.
- Added `payload_is_aegis_repair_apply()` for Bash and MCP payloads. MCP is limited to the direct `aegis_repair` tool with `apply: true`, so `handoff_repair` and other repair-adjacent tools do not inherit the BLOCKED-readiness exemption.
- Added the new predicate to the BLOCKED-readiness exception list after target-dir confinement and before pending-tracking enforcement.
- Mirrored `.claude/scripts/gate_lib.py` into `aegis_foundation/assets/.claude/scripts/gate_lib.py` so new installs receive the same gate behavior.

## Tests
- CLI repair apply while readiness is BLOCKED is allowed.
- MCP repair apply while readiness is BLOCKED is allowed.
- Repair apply with an outside target remains blocked before readiness.
- Compounded repair apply remains blocked.
- Pending tracking still blocks repair apply.
- Closeout, Taskmaster mutation, and file writes remain blocked while readiness is BLOCKED.
