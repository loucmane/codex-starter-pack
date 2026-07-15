# Task 256 Verification Report

**Task**: 256 — Canonical Codex Home Topology Diagnostics and Migration Plan

**Branch**: `feat/task-256-canonical-codex-home-topology`

**Date**: 2026-07-15

**Execution checkout**: `/tmp/codex-task256-clone`

**Host-mutation authority**: none

## Acceptance Result

Task 256 passes its plan-first acceptance contract. It delivers a binding single-home ADR,
bounded read-only topology diagnostics, strict secret-safe schemas, deterministic
no-mutation Task 257 planning, source/package parity, and an exact drain-first cutover plan.
It does not execute or authorize the cutover.

## Functional Coverage

The focused suite proves:

- healthy one-home topology;
- duplicate home, session, socket, executable, and SQLite split-brain signals;
- explicit SQLite precedence and malformed relative-path refusal;
- bounded session and process scans with truncation reported as unknown;
- caller-declared host-complete process scope versus sandbox-unknown scope;
- active SQLite file-descriptor ownership without arbitrary process-argument emission;
- stale, fresh, duplicated, malformed, and unprovable thread/trust relationships;
- tracked hook guidance and hook-definition digests without asserting `/hooks` approval;
- wrapper routing signal classification without emitting wrapper source;
- deterministic byte-identical status and plan outputs;
- no-write behavior;
- CLI success and invalid-input refusal;
- strict JSON Schema validation and source/package byte parity;
- fail-closed schema mutations for hook trust and Task 256 execution.

## Verification Matrix

| Gate | Result | Evidence |
|---|---:|---|
| Focused topology and schema tests | 50 passed | `pytest -q tests/meta_workflow_guard/test_codex_topology.py tests/meta_workflow_guard/test_aegis_schemas.py` |
| Adjacent Codex Remote trust tests | 42 passed | `tests/meta_workflow_guard/test_codex_remote_trust.py` |
| Release distribution tests | 14 passed, 2 opt-in skips | `tests/meta_workflow_guard/test_aegis_release_distribution.py` |
| Output-budget tests | 17 passed | `tests/meta_workflow_guard/test_aegis_output_budget.py` |
| Runnable full suite | 2,130 passed, 4 opt-in skips | xdist full suite with four precisely classified baseline/environment exclusions |
| Slow precision-corpus test | 1 passed in 34.26s | `test_shadow_precision_corpus_replays_real_git_histories_and_meets_registered_bar` |
| Ruff | passed | changed Python files |
| Black | Both new Task 256 Python files reported unchanged; worker shutdown timed out; modified legacy files retain baseline formatting | canonical baseline comparison recorded below |
| Mypy | passed | `aegis_foundation/codex_topology.py` |
| Python compile | passed | changed Python modules/tests |
| Source/package docs and schemas | byte-identical | four `cmp` checks |
| Taskmaster health | passed | 255 tasks, 386 subtasks, 443 dependency refs, 0 invalid |
| Plan sync | passed | no drifted plan-step IDs |
| Work-tracking audit | passed | no errors or warnings after Serena memory capture |
| Readiness | passed | `READY \| task=256` |
| S:W:H:E guard | passed | all tracked entries compliant |
| Diff whitespace | passed | `git diff --check` |

## Full-Suite Classification

The final runnable full-suite command precisely deselected four tests after each was
independently classified. The result was:

```text
2130 passed, 4 skipped in 64.26s
```

The four deselections were not hidden regressions:

1. `test_test_enabled_apply_refuses_governed_repo_target_before_validation`
   assumes the repository root itself is outside the system temp directory. The required
   isolated Task 256 clone is under `/tmp`, so the test reaches a later Task 42 status check.
   The exact test passes in the untouched canonical `/home/loucmane/codex` checkout.
2. `test_editable_package_aegis_cli_invocation_works_from_external_cwd` fails identically
   on untouched main because its fresh build-isolated virtualenv cannot resolve
   `setuptools>=68` while outbound package access is blocked.
3. `test_editable_package_mcp_describe_config_works_from_external_cwd` fails for the same
   independently reproduced package-resolution constraint.
4. `test_local_checkout_stdio_mcp_lists_aegis_surfaces_from_external_cwd` does not terminate
   in this sandbox and times out identically on untouched main. A faulthandler trace shows
   the baseline test waiting in its asyncio stdio exchange, outside Task 256 code.

No test, gate, or implementation was weakened to obtain the passing result.

`tests/meta_workflow_guard/test_aegis_schemas.py` is already not Black-clean on untouched
main. `aegis_foundation/cli.py` also contains pre-existing formatting that a whole-file
Black pass would rewrite. Task 256 changes only two schema-registration lines and focused
CLI additions in those legacy files. Black reported the two new Task 256 Python files
unchanged before its sandboxed worker shutdown hit the external timeout; unrelated baseline
formatting was preserved.

## Live Read-Only Dogfood

The diagnostic was run without host mutation. It reported:

- normal home `/home/loucmane/.codex`: 56 discovered sessions, two discovered SQLite roots,
  one control socket, Codex 0.144.4 identity;
- candidate Remote home `/home/loucmane/codex/.codex/remote-control`: 84 discovered
  sessions, no discovered SQLite state, one control socket, Codex 0.144.4 identity;
- context-routed wrapper signals and a wrapper digest, without source disclosure;
- split-brain indicators for control sockets, executable identities, session stores, and
  SQLite roots;
- `sqlite_authority_ambiguous` as a blocking issue;
- process scope `unknown`, because the sandbox-visible process namespace is not proof of
  host-wide absence.

That blocked plan is the correct fail-closed output. Task 257 must establish host-complete
ownership and authoritative SQLite state before mutation.

## Preservation Proof

Task 256 did not:

- edit `/home/loucmane/.codex` or
  `/home/loucmane/codex/.codex/remote-control`;
- start, stop, signal, replace, or reconnect any app server;
- edit shell configuration, PATH, symlinks, binaries, or the host wrapper;
- touch `/home/loucmane/dev/blog`;
- copy auth, sessions, SQLite databases, connectors, trust records, or hook hashes;
- approve hooks or bypass `/hooks`;
- execute Task 257 or begin Taskmaster-to-Gas-Town migration.

Implementation and workflow evidence are confined to the isolated Task 256 Git clone.

## Delivery Boundary

After final status synchronization and archival, Task 256 may be committed, pushed, and
opened as an attended exact-head PR. It must not be merged automatically. Task 257 may be
created only after the owner reviews and merges Task 256, and it must follow
`docs/aegis/task257-canonical-codex-home-cutover-plan.md` under its own authority.
