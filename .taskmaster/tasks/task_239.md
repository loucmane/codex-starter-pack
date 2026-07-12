# Task ID: 239

**Title:** Audit Aegis Capture Across Worktrees And Subagents

**Status:** in-progress

**Dependencies:** 236 ✓

**Priority:** high

**Description:** Build a diagnostic evidence harness that identifies why child worktree activity is missing or misattributed before changing recorder behavior.

**Details:**

Implement roadmap workstream C3 as diagnostics only. Distinguish pre-install checkout age, missing tracked assets, unloaded client hooks, source-root resolution failure, Git-common-dir store mismatch, absent attribution, parent orchestration mistaken for child activity, and loss after ephemeral worktree removal. Record client/version, parent and child identity, worktree/branch/HEAD/common-dir, asset checksums, resolved ledger path, hook capabilities, before/after event IDs and counts, attribution fields, and supported/degraded/failed status. Exercise two linked worktrees, an actual Claude child, a Codex worktree or explicit unsupported result, success, command failure, verification, and teardown. Check in a secret-free coverage report and replay fixture. Do not select or implement a runtime fix in this task.

**Test Strategy:**

No test strategy provided.
