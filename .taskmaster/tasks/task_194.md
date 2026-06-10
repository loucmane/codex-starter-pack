# Task ID: 194

**Title:** Surface post-closeout GitHub delivery state

**Status:** done

**Dependencies:** 192 ✓

**Priority:** high

**Description:** After local Aegis closeout, agents must clearly surface whether the task branch is pushed, has a PR, has passing CI, and is merged, so done does not accidentally mean local-only. HP-Coach #73 proved that reporting alone is insufficient: after closeout passed and Taskmaster #73 was marked done, `git push -u origin feat/task-73-p0-poisoned-resume-fallback` was blocked because current work was `completed` rather than `in-progress`. Aegis must therefore expose a sanctioned post-closeout delivery path, or prescribe delivery before final closeout, while still requiring explicit user approval before merge.

**Details:**

Extend Aegis next/closeout guidance and continuation contract so completed local work transitions into an explicit delivery checkpoint instead of a terminal no-mutation gap. Anchor implementation in `scripts/_aegis_installer.py`: `next_action()` / `_workflow_guidance_payload()` for read-only guidance, `_classify_doctor_state()` for completed-closeout state classification, `_closeout_git_report()` for closeout git guidance, and `closeout()` / `_workflow_next_action()` for the post-closeout `next_action` payload surfaced through `scripts/codex-task handle_aegis_next` and `handle_aegis_closeout`.

Add HP-Coach #73 reproduction evidence to the implementation notes and regression coverage: closeout passed, Taskmaster task #73 was marked done, then PreToolUse refused `git push -u origin feat/task-73-p0-poisoned-resume-fallback` with `BLOCKED | task=73 | blocked=2 | first=Aegis current work status is 'completed', expected 'in-progress'`. Treat this as the concrete failure mode for `completed_closeout + local branch not pushed/no PR`.

Detect and classify delivery states for the active/completed task branch: local-only commits, missing upstream branch, missing PR, pending/failed GitHub checks, open unmerged PR, merged PR, and unknown GitHub state when `gh` is unavailable. Introduce an explicit state such as `delivery_pending` for completed closeout with unpublished/unopened delivery, and return machine-readable `next_safe_action` values including `push_branch`, `open_pr`, `wait_for_ci`, `ask_before_merge`, and `merged_complete`. The payload should also include concrete suggested commands such as `git push -u origin <branch>` and `gh pr create --draft` only when policy allows them.

Preserve safety boundaries. Completed closeout must not allow arbitrary source edits or unrelated Git mutation, but it must either permit the specific sanctioned delivery actions or make it impossible to close out before delivery when project policy requires pre-closeout delivery. Never merge without explicit user approval unless a project policy explicitly enables auto-merge; never stage unrelated drift; report blockers exactly. Natural prompts such as `finish this`, `continue`, `ship it`, and `done` should route to the delivery checkpoint rather than incorrectly reporting local-only completion.

Reuse existing patterns where possible: read-only `aegis.next` guidance must remain non-mutating as covered in `tests/meta_workflow_guard/test_aegis_mcp_server.py`; completed-closeout guard behavior is already exercised around `test_installed_gate_allows_taskmaster_completion_after_closeout` in `tests/meta_workflow_guard/test_aegis_installer.py`; reconcile already has GitHub PR classification examples such as `test_reconcile_reports_done_task_with_open_pr_as_not_merged` that can guide mocked `gh` handling.

**Test Strategy:**

Add focused regression tests in `tests/meta_workflow_guard/test_aegis_installer.py` for a local git fixture representing HP-Coach #73: completed Aegis closeout, Taskmaster done, local branch with commits, no upstream and no PR. Assert `aegis.next` or doctor/closeout guidance classifies the state as `delivery_pending` and returns `next_safe_action: push_branch` instead of a generic completed terminal state.

Add mocked `gh`/git-state tests for the delivery matrix: missing upstream -> `push_branch`; upstream exists but no PR -> `open_pr`; PR open with pending checks -> `wait_for_ci`; PR open with passing checks but unmerged -> `ask_before_merge`; merged PR or branch merged to base -> `merged_complete`. Include negative coverage proving merge actions require explicit user approval.

Add PreToolUse/hook regression coverage using the existing installed target helpers to prove the completed-closeout state no longer blocks sanctioned `git push -u origin <branch>` and `gh pr create` actions when policy permits delivery, while still blocking unrelated source edits and unrelated Git mutation. Add MCP read-only coverage in `tests/meta_workflow_guard/test_aegis_mcp_server.py` so `aegis.next` exposes the same delivery guidance without mutating files.

## Subtasks

### 194.1. Map current Aegis closeout and delivery guidance surfaces

**Status:** pending
**Dependencies:** None

Inspect `scripts/_aegis_installer.py`, `scripts/codex-task`, and existing installer/MCP tests to identify all surfaces that currently report completed closeout, git guidance, next actions, and PreToolUse readiness behavior.

**Details:**

Confirm how `next_action()`, `_classify_doctor_state()`, `_closeout_git_report()`, `closeout()`, and `_workflow_next_action()` interact today. Record HP-Coach #73 as the reproduction target for the delivery gap.

### 194.2. Classify post-closeout GitHub delivery states

**Status:** pending
**Dependencies:** 194.1

Implement delivery-state detection for completed closeout, including local-only commits, missing upstream, missing PR, pending or failed CI, unmerged PR, and merged completion.

**Details:**

Add a machine-readable state such as `delivery_pending` for `completed_closeout + local branch not pushed/no PR`. Prefer structured git/gh helpers or mocked wrappers over ad hoc output parsing where the codebase already provides helpers.

### 194.3. Expose sanctioned delivery next actions

**Status:** pending
**Dependencies:** 194.2

Update Aegis next/closeout guidance and continuation payloads to return `next_safe_action` values for `push_branch`, `open_pr`, `wait_for_ci`, `ask_before_merge`, and `merged_complete`.

**Details:**

For natural continuation prompts, ensure completed local work routes to delivery guidance rather than terminal completion. Suggested commands must be concrete when policy permits them, but merge must remain approval-gated.

### 194.4. Permit or schedule safe delivery around completed closeout

**Status:** pending
**Dependencies:** 194.2, 194.3

Adjust PreToolUse/readiness policy so completed closeout does not trap an agent before push/PR delivery, while still preventing unrelated mutation.

**Details:**

Either permit narrowly-scoped delivery commands from completed closeout under explicit policy or update closeout guidance so delivery is scheduled before final closeout. Preserve the existing allowance for Taskmaster completion after closeout and keep unrelated source edits blocked.

### 194.5. Verify delivery checkpoint end to end

**Status:** pending
**Dependencies:** 194.2, 194.3, 194.4

Add installer and MCP tests proving the post-closeout delivery checkpoint is visible, non-mutating when read-only, and safe across git/PR/CI/merge states.

**Details:**

Cover `tests/meta_workflow_guard/test_aegis_installer.py` for local git and hook behavior, and `tests/meta_workflow_guard/test_aegis_mcp_server.py` for read-only MCP guidance. Reuse reconcile PR classification patterns where applicable.
