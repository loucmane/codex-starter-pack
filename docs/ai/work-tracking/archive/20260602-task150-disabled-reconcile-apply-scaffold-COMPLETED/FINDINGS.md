# Findings

- 2026-06-02 — The Task 149 contract intentionally left one load-bearing question open: future apply must not be invokable by the governed agent. The Task 150 implementation resolves that as a default-deny approved-context proof model, not an agent-channel denylist.
- 2026-06-02 — The disabled scaffold can be useful before any mutation path exists if it produces reusable safety primitives: positive context evaluation, fail-closed kill-switch evaluation, transaction audit record shape, and an orchestrator that always refuses.
- 2026-06-02 — The strongest disabled-ness proof is behavioral. The new scaffold tests run through the side-effect oracle/corpus and assert no tree deltas, not just that an enable flag is false.
- 2026-06-02 — The scaffold remains absent from governed-agent surfaces: no reconcile CLI mutation flags, no MCP apply tool, no mutation params in the reconcile MCP schema, and no `scripts/codex-task` path consumes it.
