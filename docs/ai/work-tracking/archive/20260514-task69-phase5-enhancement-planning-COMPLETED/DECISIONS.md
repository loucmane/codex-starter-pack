# Decisions

- 2026-05-14 — Static packet boundary — Task 69 implements an evidence-backed planning packet, not automatic compaction triggers, external semantic search, AI template generation, optional MCP enablement, measured optimization changes, or Taskmaster task creation from candidate rows.
- 2026-05-14 — Planned candidates remain non-mutating — AI-assisted template generation and optional MCP integration are represented as `planned` candidates even when evidence exists, because each requires its own Taskmaster task and scope reconciliation before implementation.
- 2026-05-14 — Aggregate status is explicit about mixed readiness — when the packet has ready and planned candidates with no missing evidence, it reports `ready-with-planned-candidates` instead of plain `ready` so the roadmap does not overclaim that speculative enhancements are complete.
