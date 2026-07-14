# Task ID: 252

**Title:** Harden Shared Codex Hook Bootstrap Against Mutable Runtime Outages

**Status:** in-progress

**Dependencies:** 242 ✓, 248 ✓, 249 ✓

**Priority:** high

**Description:** Eliminate cross-project Codex hook failures caused by hook commands resolving into mutable source-checkout scripts; make target-local dispatch stable, bounded, independently recoverable, and migration-safe.

**Details:**

Ground the fix in the observed incident where absolute Codex hook commands under /home/loucmane/codex invoked tracked shell wrappers while gate_lib.py was transiently unavailable, causing repeated Stop-hook failures across projects. Make generated and installed Codex hooks resolve exclusively through a target-local stable bootstrap and .aegis/bin/aegis hook dispatch, independent of mutable central source files at hook time. Preserve Git-root and linked-worktree behavior. Define bounded degraded behavior: mutation-capable PreToolUse must fail safely when policy cannot be evaluated; passive PostToolUse, lifecycle, and Stop hooks must emit concise non-recursive diagnostics without retry/spam loops. Preflight the complete runtime set before installer/update writes and prevent partial-runtime exposure; recognized legacy absolute Aegis hook definitions may be migrated only by exact semantic match, while unknown/custom definitions require manual review and remain untouched. Keep live/package assets and schemas/contracts consistent. Add regression tests for Codex-only and multi-agent installs, two independent target projects surviving central source gate_lib removal, missing wrapper/library/shim combinations, update ordering/refusal, worktrees, idempotence, exact hook trust/reload guidance, bounded output, and source/package parity. Document root cause, blast radius, rollback, and operator recovery. Do not edit the source checkout's untracked .codex/hooks.json directly.

**Test Strategy:**

No test strategy provided.
