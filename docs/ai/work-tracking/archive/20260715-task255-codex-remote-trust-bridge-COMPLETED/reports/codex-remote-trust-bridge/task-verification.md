# Task 255 Verification Evidence

**Task:** 255 — Host-Scoped Codex Remote Control Trust Management  
**Branch:** `feat/task-255-codex-remote-trust-bridge`  
**Date:** 2026-07-15  
**Result:** implementation and source-workflow verification passed; hosted delivery verification remains pending

## Verified contract

- Normal Codex and autonomous Remote Control remain separate `CODEX_HOME` security contexts.
- Remote Control project authority is an explicit, schema-versioned, host-scoped allowlist; no project can authorize itself implicitly.
- Aegis owns only a delimited `[projects]` projection and preserves unrelated Remote Control configuration bytes and file mode.
- Trust mutations are previews unless `--apply` is explicit.
- Apply operations use canonical paths, restrictive state-file modes, a bounded inter-process lock, atomic replacement, fsync, last-known-good backup, post-write validation, and exact rollback verification.
- Normal project trust, Remote Control authorization, effective Remote Control project trust, tracked hook-review guidance, and Codex client-local exact-definition `/hooks` trust are reported separately.
- Aegis does not copy normal-home trust, hook hashes, credentials, connector approvals, sessions, or databases; it does not symlink either whole config or whole home; it never claims that visible guidance or hashes prove client trust.

## Changed implementation surfaces

- `aegis_foundation/codex_remote_trust.py`
- `aegis_foundation/cli.py`
- `docs/aegis/codex-remote-control-trust.md`
- `aegis_foundation/assets/docs/aegis/codex-remote-control-trust.md`
- `tests/meta_workflow_guard/test_codex_remote_trust.py`
- Task 255 Taskmaster, plan, session, Serena memory, and work-tracking projections

## Automated verification

| Surface | Result |
|---|---|
| Task 255 focused trust, security, concurrency, rollback, preservation, and CLI tests | 42 passed |
| Adjacent Codex adapter, bootstrap, and schema tests | 37 passed |
| Release-distribution tests | 14 passed; two documented opt-in smokes skipped in the default run |
| Installer tests | 153 passed; one documented opt-in certification smoke skipped |
| Installed-wheel CLI smoke with `AEGIS_RUN_WHEEL_SMOKE=1` | 1 passed in 14.22s |
| Full repository suite | 2100 passed, 4 documented opt-in smokes skipped, 1 environment-sensitive failure investigated below |
| The environment-sensitive test with a non-overlapping `TMPDIR` | 1 passed in 0.10s |
| Ruff on the new module, CLI integration, and tests | passed |
| Mypy on `aegis_foundation/codex_remote_trust.py` | passed |
| Black check on new module and test | passed |
| `git diff --check` | passed |
| Taskmaster full-graph health | 254 tasks, 386 subtasks, 443 dependency references, 0 invalid |
| Plan/tracker sync | passed |
| Work-tracking audit | passed |
| Source guard with untracked Task 255 paths | passed after real Serena memory creation |

### Full-suite environment finding

The default full-suite run from `/tmp/codex-task255` produced one failure in the pre-existing test
`test_test_enabled_apply_refuses_governed_repo_target_before_validation`. Its fixture assumes the
source repository is outside the operating-system temporary root. Because the entire Task 255
worktree itself is under `/tmp`, `_is_under_temp(REPO_ROOT)` classified the governed source
worktree as an allowed isolated temporary target and the test advanced to the unrelated Task 42
status check, returning `candidate_already_done` instead of the expected
`target_not_isolated_temp`.

The exact test passed when rerun with
`TMPDIR=/home/loucmane/codex/.git/task255-pytest-tmp`, which makes the process temporary root
non-overlapping with `/tmp/codex-task255`. Task 255 does not modify that test or its production
path. This is recorded as an environment-sensitive baseline assumption, not hidden or weakened.

## Live read-only diagnosis

The new status command was run read-only against the real host paths. It correctly reported:

- normal Codex trusts `/home/loucmane/dev/blog`;
- the active Remote Control home does not yet authorize or effectively trust Blog;
- Blog's current `.codex/hooks.json` definition digest is
  `3334c040bd46a92bd542d53e2919a43b14ba1bf001fa79883a5385dc5ba487d5`;
- tracked hook-review guidance and actual client-local exact-hash trust are different states;
- `/hooks` review remains required and client trust is never asserted by Aegis.

No host allowlist, lock, backup, normal/Remote config, Blog file, hook record, or Blog Aegis state
was created or changed. The later Blog rollout remains an attended post-merge operation.

## Continuity and scope controls

- Serena MCP was genuinely available through the deferred tool registry, activated for
  `/tmp/codex-task255`, and used to write
  `.serena/memories/2026-07-15_task255_codex_remote_trust_bridge.md`.
- Unrelated drift in `/home/loucmane/codex` remains untouched.
- `/home/loucmane/dev/blog` remains untouched.
- Enforcement remains advisory.
- The Taskmaster-to-Gas-Town migration has not started.

## Remaining delivery gates

- Commit, push, open the reviewed PR, run hosted CI, witness, and secret checks, and follow the repository's evidence-governed merge policy.
- Synchronize upstream main, then prepare—but do not execute—the exact attended Blog rollout through the `/hooks` review boundary.

## Hosted witness remediation

The first PR witness run accounted for 21 of 22 paths and failed only on a convenience link added
to root `README.md`, which was not part of Task 255's declared scope. The link was removed rather
than broadening the task scope or weakening witness accounting. No runtime, trust, test, policy, or
Blog behavior changed in this remediation.

## Source closeout result

- Taskmaster Task 255 is `done`; targeted Taskmaster generation completed.
- The supported work-tracking archive transition preserved the full evidence bundle under
  `docs/ai/work-tracking/archive/20260715-task255-codex-remote-trust-bridge-COMPLETED/`.
- Post-archive readiness returned `READY | task=255`.
- Post-archive Taskmaster health reports 254 tasks, 386 subtasks, 443 valid dependency references,
  and zero invalid references.
- Post-archive source guard and diff checks pass. The work-tracking audit reports only the expected
  between-session warning that no ACTIVE folder remains.
