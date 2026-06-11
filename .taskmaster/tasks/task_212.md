# Task ID: 212

**Title:** Cold-start falsifier v2: recon-to-decision metric + READY-envelope scenarios

**Status:** pending

**Dependencies:** 211 ✓

**Priority:** high

**Description:** First live run of the TM #211 replay-cold-start harness exposed that 'tool-calls-to-first-meaningful-action' is degenerate and inverted on this gated repo: a detached worktree at a recent SHA has BLOCKED readiness (gate refuses mutations) and recent main SHAs are 'done' states with no pending work, so a well-oriented capsule-on agent correctly does nothing (scored 18 recon, no action) while a charge-ahead baseline trips the mutation heuristic at 3 calls and falsely wins. Redesign: (1) metric becomes recon-to-CORRECT-DECISION — grade whether the agent reaches the right next move (including correctly choosing not to mutate) and how much it foraged to get there, against known ground truth; (2) scenarios must be genuine in-progress work in a READY envelope (task branch + sessions/current + plans/current + ACTIVE folder) or run under advisory mode so mutations are not gate-refused; (3) mid-task states were squashed out of main history, so seed from forward-captured in-progress snapshots and/or HP-Coach archived in-progress states. Keep the testable-core/operator-gated split and the fresh-null guard.

**Details:**

No details provided.

**Test Strategy:**

No test strategy provided.
