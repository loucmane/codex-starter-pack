# Task 249 Verification Evidence

## Incident reproduction

- Live Blog checkpoint: `feat/task-40-migrate-react-next-framework-build-system` at
  `0fca7a807a8035b6e3afb9d6795dfb9ac9efc69f`, dirty with active Task 40 work.
- Live Blog was not modified.
- A disposable snapshot reproduced `project_update --apply` failing in `runtime_update`
  because the pre-adapter Codex manifest did not yet list `.codex/hooks.json`.

## Implemented invariant

After preview and unsafe-operation refusal, `project_update` applies the reviewed managed
install first. That writes a current-schema manifest and managed adapter candidate. Strict
runtime metadata refresh follows. Direct runtime update remains strict.

## Local regression results

- Focused legacy/manual-review matrix: `6 passed`.
- Project-update/runtime affected matrix: `18 passed`.
- Installer, adapter, fixture, distribution, and schema matrix: `181 passed, 3 skipped`.
- Full local repository suite: `1957 passed, 4 skipped, 1 environmental failure`.
- Source/package installer byte comparison: passed.
- Python compilation and `git diff --check`: passed.

The skipped tests are the existing opt-in release certification, wheel CLI, and wheel MCP
smokes; none are silently disabled by Task 249.

The sole local full-suite failure is
`test_test_enabled_apply_refuses_governed_repo_target_before_validation`. Its safety
premise requires the governed repository to be outside `/tmp`; this Task 249 worktree is
intentionally rooted under `/tmp`, so the test observes the temporary target as already
isolated. The other 1,957 tests pass locally. Unfiltered hosted CI from a normal checkout
is required to exercise that assertion, matching the established Task 248 verification
protocol.

## Blog snapshot replay

With the operator hook preserved under a different name in the disposable snapshot, the
patched updater generated the managed hook, applied all reviewed assets, migrated the
manifest, compiled the capsule, and passed strict verification:

- strict checks: 42 total, 0 required failures;
- enforcement: advisory warning preserved;
- workflow: active Task 40 remained aligned;
- Codex hook registration and exact-hash trust guidance: passed.

## Source workflow verification

- Plan/tracker parity: passed.
- Work-tracking audit: passed with no issues.
- Taskmaster full-graph health: 248 tasks, 383 subtasks, 433 dependency references,
  zero invalid references.
- Taskmaster dependency validation: passed.
- S:W:H:E guard validation: passed.

The Aegis source worktree is intentionally not an installed Aegis target, so strict
installed-target verification is represented by the migrated Blog snapshot above rather
than by fabricating `.aegis` installation state inside this worktree.

## Hook manual-review evidence

| File | Raw SHA-256 | Semantic SHA-256 |
|---|---|---|
| Existing Blog operator hook | `ca892b3fec1633ac05d36006d28da1e7b5d292ca8573135f942f991a34aba0e6` | `f249da9d634c6e2c8344e0b565927f591d7015b19aeb1212d03f59363a3aa021` |
| Task 248 managed candidate | `3334c040bd46a92bd542d53e2919a43b14ba1bf001fa79883a5385dc5ba487d5` | `bc4bd6b708b77a54724b0344b8d00dd0c439006735f9db56a3bb4e14e5ba159e` |

The candidate adds canonical `apply_patch`, atomic ledger recording, Codex attribution,
timeouts, and status messages. The installer must continue to refuse silent overwrite;
the live rollout requires an attended owner choice followed by `/hooks` exact-hash review.
