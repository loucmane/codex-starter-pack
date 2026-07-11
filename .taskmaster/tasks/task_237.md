# Task ID: 237

**Title:** Make Managed Agent Guidance Truthful And Mode-Aware

**Status:** pending

**Dependencies:** 236 ✓

**Priority:** high

**Description:** Replace strict-only managed Claude, Codex, and multi-agent startup guidance with a compact contract that accurately distinguishes advisory and strict enforcement without changing gate behavior.

**Details:**

Implement roadmap workstream C1. Render mode-aware managed blocks for CLAUDE.md, AGENTS.md, and CODEX.md. Advisory guidance must state that passive recording is automatic, forbid manual pending-event draining, use aegis brief for orientation, and use aegis witness at delivery. Strict guidance must retain the detailed kickoff/log/verify/closeout contract by reference. Preserve project-owned text byte-for-byte and cap each managed startup block at 25 nonblank lines. Add clean-install, update, local-divergence, Claude-only, Codex-only, and multi-agent fixtures. Negative tests must prove advisory guidance does not command logging, handoff repair, pending draining, or required closeout. Capture Blog dogfood showing child agents no longer apologize for correctly skipping strict ceremony. Record output size, governance-call, and rollback metrics.

**Test Strategy:**

No test strategy provided.
