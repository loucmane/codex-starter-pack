# Findings

- 2026-08-31 — The managed delegation policy and generated Codex matcher are already merged and
  unit-tested, but Codex stores project-hook trust outside the repository. Source installation
  therefore does not prove that a future Codex session will execute the PreToolUse denial.
- 2026-08-31 — Existing evidence-root trust code correctly uses Codex's supported app-server API,
  but is intentionally hard-coded to four Gas City evidence hooks and cannot safely trust the
  seven generated Aegis project hooks.
- 2026-08-31 — The safe acceptance shape is two-stage: an isolated synthetic canary proves the
  entire install/list/trust/deny/allow/rollback path without persisting trust, while
  `trust-project` applies the same exact-hash transaction to a real installed project and retains
  it only after denial, non-interference, and idempotence all pass.

## Progress Log
- **2026-08-31 20:31 CEST** - [S:20260831|W:ga-ur1c.4.1-transactionally-prove-managed-codex-delegation-denial|H:pytest|E:cmd`TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 pytest -q -s -p no:cacheprovider -k 'not editable_package_aegis_cli_invocation and not editable_package_mcp_describe_config and not local_checkout_stdio_mcp_lists_aegis_surfaces'`] Validated the candidate with 2431 passing tests and 21 expected skips; excluded exactly two scope-prohibited network package-install tests and one independently reproduced 30-second MCP stdio hang.
- **2026-09-01 11:16** — [S:20260901|W:ga-ur1c.4.1-transactionally-prove-managed-codex-delegation-denial|H:github-actions:codex-guard|E:https://github.com/loucmane/gas-city-operations/actions/runs/33491113623] CI correctly refused when current-main completed ga-ob3l pointers were paired with the newly active ga-ur1c.4.1 tracker; the defect was workflow-state parity, not implementation behavior.
