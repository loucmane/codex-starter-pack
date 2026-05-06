# Task 103 Claude Runtime Adapter and Multimodal Workflow Enforcement – Implementation Notes

## Planned Workstreams
- Subtask 103.1: reconcile the bootstrap branch, ownership boundary, hookability taxonomy, and runtime file contract.
- Subtask 103.2: implement readiness as a hard gate.
- Subtask 103.3: implement Claude PreToolUse mutation gates.
- Subtask 103.4: port or rewrite approved Claude adapter files.
- Subtask 103.5: prove behavior with tests, guard evidence, handoff, and Serena memory.

## Non-Negotiable Acceptance Standard
- Documentation and memory are not sufficient. The deliverable is a gated runtime that mechanically prevents invalid Claude actions where the tool surface is hookable.
- Every enforcement claim must be backed by a passing test or explicitly labeled policy-only with limitations documented in `DECISIONS.md` and `HANDOFF.md`.
- The system must be multimodal/multi-agent: it must account for Codex, Claude, shell, MCP, memory stores, GitHub flows, and future agent/tool surfaces without assuming one text-only execution path.
