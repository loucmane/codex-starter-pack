# Task ID: 189

**Title:** Add agent-ready continuation brief to aegis next

**Status:** done

**Dependencies:** 188 ✓

**Priority:** high

**Description:** RESCOPED 2026-06-14 (reconciliation): the aegis next state machine shipped (next_action emits phase/state/next_required_action/suggested_cli/suggested_mcp_call/copyable_repairs) and TM 194/PR #197 added post-closeout next_safe_action + delivery states. RESIDUAL: (1) the named continuation-brief schema fields (continue_means, artifact_policy, stop_conditions, per-state confirmation-boundary) — present only in this task spec, not in source; (2) the 'safe-repair' vs 'manual-review-repair' states not surfaced by next_action (that classification lives in doctor/repair); (3) a concise agent-facing aegis next rendering (handle_next currently dumps full JSON). Re-anchor on the cross-agent continuation contract from TM 188.

**Details:**

Add a machine-readable continuation brief to aegis next output with current task authority, workflow phase, continue_means text, next_safe_action, suggested commands, protected confirmation boundaries, artifact policy, and stop conditions. Cover common states including no current work, active implementation, dirty scoped files, verified but uncommitted work, committed but not closed out, closeout passed with Taskmaster not done, pending tracking, safe repair available, manual-review repair, observation ready, and observation completed. Add tests for the state table and concise CLI output suitable for agent consumption.

**Test Strategy:**

No test strategy provided.
