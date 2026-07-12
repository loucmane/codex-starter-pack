# Task 246 Bootstrap Evidence-Gated Autonomous Delivery – Implementation Notes

## Planned Workstreams
- Extend source-only completed-work derivation with a policy-gated taskless-default-branch path and pointer-containment/identity checks.
- Add a stdlib-only delivery-policy evaluator, JSON schema, source-repository evidence-gated policy, and packaged managed copies where applicable.
- Replace hardcoded delivery confirmation booleans with mode-aware Aegis status/next guidance while preserving attended default behavior.
- Add a minimal-permission GitHub workflow that checks out trusted `main`, collects PR/API evidence, evaluates it with trusted code, and squash-merges only eligible exact heads.
- Cover PR #261 push-context reproduction, stale/ambiguous pointers, installed-target exclusion, self-authorization, protected paths/labels, incomplete inventories, failed/pending workflows, exact-head movement, unresolved threads, and source/package parity.

## Implemented

- `scripts/_source_workflow_state.py` preserves feature-branch identity first and adds a taskless-default-branch fallback only when a valid active delivery policy, contained current plan/session pointers, Taskmaster done state, and one completed archive agree.
- `aegis.delivery-policy.json`, its schema, and the stdlib-only `scripts/aegis-delivery-policy` classify complete evidence as `allow`, `attended`, `defer`, or fail-closed `deny`; packaged script/schema bytes remain identical.
- The policy's explicit routine capability block persists authorization for supported Taskmaster transitions, deterministic safe repairs, verified closeout, commit/push/PR, and CI remediation while manual-review/high-risk operations remain attended.
- `.github/workflows/aegis-autonomous-delivery.yml` executes only trusted default-branch code, retrieves complete GitHub API evidence, revalidates head/base, and uses the normal exact-head squash endpoint only for `allow`.
- CI, Codex Guard, and Meta Workflow Guard accept an exact-merge-SHA repository dispatch so a merge performed with `GITHUB_TOKEN` still receives protected-main validation.
- `scripts/_aegis_installer.py`, its packaged mirror, and `CODEX.md` now surface active delivery policy instead of asserting that every merge is permanently manual. Missing, invalid, revoked, or attended policy still requires owner approval.
- `docs/aegis/evidence-gated-autonomous-delivery.md` records the authority boundary, eligibility, attended categories, persistence, post-merge behavior, revocation, rollback, and verification contract.
- `.codex/deep-work.config.toml` removes quota-backed Auto-review and legacy `workspace-write` overlap in favor of a tested `aegis-autonomous` permission profile. It keeps the built-in workspace sandbox, reopens primary-checkout Git metadata, allowlists required delivery/package domains, and runs with `approval_policy = "never"` so out-of-profile actions fail rather than prompt.
- `.claude/scripts/gate_lib.py` and its installer-packaged mirror add a non-overridable tier-c command policy before advisory/readiness evaluation. It denies worktree-discarding Git modes, force/deleting/protected-branch pushes, forced branch deletion, remote replacement, and GitHub branch-protection/ruleset mutation while preserving routine feature-branch delivery, dry runs, read-only inspection, and index-only unstaging.
