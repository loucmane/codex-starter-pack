# Task ID: 248

**Title:** Implement First-Class Codex Hook Adapter

**Status:** in-progress

**Dependencies:** 247 ✓

**Priority:** high

**Description:** Add first-class canonical apply_patch support to Aegis hooks and promote Codex hooks to a managed, verified installer adapter.

**Details:**

Implement canonical Codex apply_patch handling end to end. Runtime: strictly parse Begin Patch and End Patch plus Add File, Update File, Delete File, and Move to directives; reject malformed, empty, ambiguous, duplicate, or unsupported structures safely; normalize every source and destination path before policy evaluation so a safe first path cannot hide a protected later path. Policy: apply existing readiness, observation, protected-path, workflow-owned-path, strict/advisory, degraded fail-closed, pending-tracking, and post-tool evidence behavior. Evidence: emit one atomic event per patch with handler codex:apply_patch, a primary evidence path, all affected paths, operation metadata, and a deterministic patch digest. Parity: keep .claude/scripts/gate_lib.py byte-identical to aegis_foundation/assets/.claude/scripts/gate_lib.py. Installer: promote Codex from planned coverage to a first-class managed adapter; generate and manage .codex/hooks.json independently of Claude; add Codex gate, profile, manifest, verification, client-reload, and hook-trust guidance; preserve safe adoption and manual-review refusal; update the adapter contract only after acceptance passes. Tests: READY allow and BLOCKED readiness; Add, Update, Delete, Move; multi-file and safe-first/protected-later patches; protected and workflow-owned paths; malformed payloads; strict and advisory degraded behavior; exactly one PostToolUse event containing every affected path; installer idempotence; source/package parity; Codex-only and multi-agent installs; and a real Codex 0.144.3 hook smoke test. Delivery: use the full Taskmaster and source workflow, verification, protected CI, and evidence-gated delivery. Do not write local .aegis state directly. After upstream merge, Blog rollout is a separate guarded update and must stop at exact hook-hash trust approval.

**Test Strategy:**

No test strategy provided.
