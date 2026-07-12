# Task 246 Verification Report

## Scope

Task 246 restores completed-source validation on taskless `main` and introduces
persistent evidence-gated autonomous delivery. It preserves advisory enforcement,
Taskmaster, legacy plans/sessions/trackers, S:W:H:E narration, protected branch checks,
and attended handling for governance or high-risk changes.

## Security Invariants

- Missing, malformed, revoked, or attended policy requires per-PR owner approval.
- Routine Taskmaster transition, safe repair, verified closeout, commit/push/PR, and CI
  remediation authority is explicit in the policy and effective only in valid active
  evidence-gated mode; disabled capability falls back to attended.
- The bootstrap policy/workflow/installer paths classify as attended, so this pull
  request cannot authorize itself.
- The privileged workflow checks out only the current default branch and never checks
  out or executes pull-request code, artifacts, actions, or generated policy output.
- Complete paginated changed-file and review-thread evidence is required.
- Required workflow runs must be successful pull-request runs at the exact head SHA.
- The pull-request head and base are re-fetched immediately before a normal protected
  squash merge; the merge request carries the expected head SHA.
- The workflow uses no admin bypass, force operation, PAT, or repository secret.
- Exact-merge-SHA `repository_dispatch` runs post-merge CI and guards because events
  created by a workflow token do not provide a dependable ordinary push lane.
- Each dispatch workflow validates the 40-hex merge SHA and binds that exact object to
  the repository default branch locally before guards run, avoiding detached-HEAD loss
  of the `main` identity while preserving exact-object validation.
- A tier-c PreToolUse policy blocks destructive Git, protected-branch pushes, remote
  replacement, and GitHub branch-protection/ruleset mutation before ordinary advisory
  or readiness evaluation. Its audit record is best-effort, but its denial is fail closed
  and never break-glass eligible.

## Local Verification

### Focused policy and workflow contract

`tests/meta_workflow_guard/test_aegis_delivery_policy.py` and
`tests/meta_workflow_guard/test_aegis_autonomous_delivery_workflow.py` cover allow,
attended, defer, deny, self-authorization resistance, protected paths/labels, test
deletion, exact head/base, complete inventory, required workflows, review threads,
trusted checkout, minimal permissions, merge request shape, post-merge dispatch, and
embedded Bash syntax.

### Comprehensive Task 246 regression

Command covered source checkout, delivery policy, autonomous workflow, installer,
schemas, packaged parity, CI workflows, continuation guidance, Codex task helpers, and
guard integration.

Result: **455 passed, 1 skipped**. The skip is the opt-in full release-certification
smoke controlled by `AEGIS_RUN_CERTIFICATION_SMOKE=1`.

### Complete repository suite

Command: `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -q`

Final result after the destructive-operation hardening amendment: **1,867 passed, 4
skipped** in 335.91 seconds. All skips are documented opt-in wheel/release/real-target
smoke tests:

- `AEGIS_RUN_CERTIFICATION_SMOKE=1`
- `AEGIS_RUN_WHEEL_SMOKE=1`
- `AEGIS_RUN_WHEEL_MCP_SMOKE=1`
- `AEGIS_RUN_WHEEL_MCP_TARGET_SMOKE=1`

### Static and graph checks

- Ruff on all changed Python and executable policy scripts: **passed**.
- Black applied to bounded helper/test modules; monolithic legacy installer files were
  intentionally not globally reformatted. Ruff covers their changed code without
  unrelated churn.
- Source/packaged installer bytes: **identical**.
- Source/packaged policy evaluator bytes: **identical**, executable mode `0755`.
- Source/packaged policy schema bytes: **identical**.
- Source/packaged `gate_lib.py` bytes: **identical**.
- Focused PreToolUse gate suite: **168 passed**, including wrapped/compound destructive
  commands, protected `main`, advisory mode, API governance mutation, and normal-delivery
  allow cases.
- Installed-target, delivery-policy, and schema regressions: **180 passed, 1 documented
  opt-in certification smoke skipped**.
- A parallel xdist diagnostic reached 1,866 passing tests but one direct MCP stdio smoke
  timed out after returning initialize/tools/resources and before prompts. The exact
  smoke immediately passed serially in 0.60 seconds; the complete authoritative serial
  suite above also passed it. No skip, timeout increase, or assertion weakening was made.
- Taskmaster health: **OK**, 245 tasks, 383 subtasks, 430 dependency references, zero
  invalid references.
- Plan/tracker sync: **passed** after implementation evidence updates.
- Source readiness: **READY**, Task 246.
- Work-tracking audit and Codex Guard: **passed**.
- Live `aegis status`: valid active `evidence-gated` policy,
  `requires_per_pr_approval: false`, and all five routine capabilities enabled.
- Strict installed-target verification: **not applicable to the intentionally uninstalled
  Aegis source checkout**. `uv run aegis verify --strict --target-dir .` failed closed on
  the missing installed manifest, matching the established source-repository boundary;
  Task 246 did not install Aegis into itself or fabricate installed state.

## Live Read-Only GitHub API Replay

Historical PR #261 (`af253b287d2052c0fd4b83b350d514b12eb89056`) was queried without
mutation to validate the workflow's real API shapes:

- paginated pull-request file inventory returned the expected files;
- exact-head Actions query returned successful `CI`, `Codex Guard`,
  `Meta Workflow Guard`, and `aegis-witness` runs;
- paginated GraphQL review-thread query returned a non-truncated empty thread set;
- the Actions run's top-level `pull_requests` array was empty despite being a known PR
  run, validating the implementation choice to resolve workflow candidates through
  `commits/{head_sha}/pulls` and require one open exact-head match.

## PR #261 Failure Replay

The checked-in source-completion fixtures reproduce the task-bearing feature-branch path
and taskless-default-branch path. Tests prove:

- feature branch behavior remains unchanged;
- missing policy leaves taskless-main fallback inapplicable;
- malformed, schema-skewed, or revoked policy fails closed;
- escaped or stale current pointers fail closed;
- plan/session identity, Taskmaster done status, and one completed archive must agree;
- readiness accepts synchronized completed source on the configured default branch;
- installed targets never use source-only fallback.

This directly addresses PR #261's push-context failures, where pull-request runs had a
task-bearing head branch but push-to-main guards saw only `main` and rejected the absence
of an ACTIVE tracker.

After Task 246 was marked done and archived, the repository's real evidence was evaluated
with branch `main`. It resolved Task 246 and the unique
`20260712-task246-evidence-gated-autonomy-bootstrap-COMPLETED` archive. Feature-branch
readiness, Codex Guard, and Taskmaster full-graph health also passed from that terminal
state.

## Hosted Acceptance Pending

The bootstrap pull request is intentionally the final attended boundary. Hosted
acceptance requires:

1. all existing pull-request checks green at the exact head;
2. no unresolved review threads and clean mergeability;
3. attended owner approval for this bootstrap only;
4. normal protected squash merge without admin bypass;
5. exact-merge-SHA post-merge dispatch with CI, Codex Guard, and Meta Workflow Guard
   green on the merged tree;
6. a later routine canary PR proving `decision: allow` merges without a new owner chat
   approval.

No hosted result is claimed in this pre-PR report.
