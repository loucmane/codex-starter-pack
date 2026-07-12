# Task ID: 245

**Title:** Recognize Completed Delivery Before Historical Branch Mismatch

**Status:** done

**Dependencies:** 244 ✓

**Priority:** high

**Description:** Fix the Blog Task 67 aegis next ordering defect so a genuinely completed task merged into synchronized main is recognized before historical branch-mismatch guidance, and stale closeout reports cannot control newer active work.

**Details:**

Use the secret-free Blog PR #28 corpus: Task 67 branch feat/task-67-gitleaks-repository-dispatch, head 0833414a8faa469c34ea26846e36eb85da277876, merge commit 81511aa10bfa13191f95bd15b80d4d889ce2e0e8, base main, and its passed archived closeout report. Bind passed reports to current work with the existing closeout-report identity predicate. On a recorded/current branch mismatch, inspect merged delivery truth before returning mismatch guidance and accept terminal completion only when the PR matches the recorded branch, the current branch matches the PR base, the merge commit is an ancestor of HEAD, and HEAD is 0 ahead/0 behind its upstream. Missing or contradictory proof stays delivery_unknown. Preserve valid current-work closeout metadata and all same-branch delivery guidance. Add a checked-in replay fixture plus positive and fail-closed tests for behind main, missing/non-ancestor merge commit, unavailable GitHub, stale Task 67 report with active Task 38, and installed compatibility. Keep canonical and packaged installer bytes identical. No generic repair, delivery sync, fabricated state, merge-policy change, output-budget work, PR-4 retirement, hash chain, or OS sandbox scope.

**Test Strategy:**

No test strategy provided.
