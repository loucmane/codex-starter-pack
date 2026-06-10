# Task ID: 208

**Title:** Capsule PR-3: narration

**Status:** pending

**Dependencies:** 207

**Priority:** medium

**Description:** Spec: AEGIS_CAPSULE_SPEC.md section 4. Deterministic Stop-hook checkpoints every turn (ts, turn index, mutation-event count, dirty-file list, branch — no LLM); narration is ONE budgeted per-session distill over transcript tail + checkpoints, triggered by the SessionEnd detached finalizer (nohup, exit 0, never inline) or lazily at next SessionStart compile-on-read when SessionEnd never fired. Day-one guards: AEGIS_COMPILE=1 short-circuits Aegis hooks in the distiller session; skip subagent/headless/short sessions (<10 mutation events); hard daily distill budget (4/day) with counter in the out-of-worktree store; LLM spend via subscription subagents only. Anti-compounding: distiller NEVER reads prior capsules including the injected-capsule transcript span. TTL scoping: story/decisions_made expire after 3 main-thread sessions unless re-evidenced; open_loops/risk_register/decisions_pending_owner are TTL-exempt with machine-checkable close/supersede conditions. Build only after the computed capsule proves useful. Merge gate: acceptance section 8 items 5 and 7.

**Details:**

No details provided.

**Test Strategy:**

No test strategy provided.
