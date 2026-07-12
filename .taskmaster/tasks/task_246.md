# Task ID: 246

**Title:** Bootstrap Evidence-Gated Autonomous Delivery

**Status:** done

**Dependencies:** 245 ✓

**Priority:** high

**Description:** Restore protected-main source validation and replace hardcoded per-PR chat approvals with persistent, trusted evidence-gated autonomous delivery while retaining a final attended boundary for policy changes.

**Details:**

Extend completed-source derivation for taskless main only when plans/current, sessions/current, Taskmaster done state, no ACTIVE/current-work state, and exactly one contained COMPLETED archive agree on one task; reject missing, stale, ambiguous, contradictory, installed-target, or self-authorizing evidence. Add a base-controlled machine-readable delivery policy with attended and evidence-gated modes, backward-compatible attended default, and source-repo opt-in. Evidence-gated eligibility must require exact unchanged head, trusted required checks and witness success, complete changed-file inventory, no unresolved review threads, mergeability, current base, and allowed path/risk classification. Routine Taskmaster/Aegis workflow updates, deterministic safe handoff/closeout repair, scoped edits/tests, commits, pushes, draft/ready transitions, CI remediation, protected squash merge, and post-merge remediation may proceed unattended. Policy/governance weakening, secrets/auth, destructive operations, deployments, irreversible migrations, billing/legal/privacy decisions, force/admin bypass, and policy self-amendment remain attended. GitHub must evaluate policy from trusted base, never candidate PR bytes. Persist authority across compaction via tracked human-readable and machine-readable contracts plus ledger/capsule projection. Preserve advisory enforcement, installed-target compatibility, legacy plans/sessions/trackers/handoffs and S:W:H:E, and unrelated local drift. Add main-push, PR-context, fail-closed, self-authorization, policy classification, post-merge remediation, source/package parity, and cross-project compatibility tests. The bootstrap PR itself remains the final attended merge boundary.

**Test Strategy:**

No test strategy provided.
