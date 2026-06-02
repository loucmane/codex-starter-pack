# Findings

- 2026-06-02 — Tasks 145-148 already cover precision, side-effect proof,
  rollback/blast-radius, and inert candidate preview. The remaining safety gap
  is invocation and confirmation: who can invoke future apply, and how the
  confirmer is provably not the governed agent.
- 2026-06-02 — A confirmation prompt inside an agent runtime is not a safety
  control. If the governed agent can call apply and satisfy confirmation, the
  confirmation step only becomes another agent action.
- 2026-06-02 — Task 149 therefore needs to make an agent-excluded invocation
  decision: future apply must be operator- or post-merge-CI-invoked, never
  exposed as `aegis reconcile --apply`, an MCP tool for the governed agent, or
  an agent-facing Codex helper path.
