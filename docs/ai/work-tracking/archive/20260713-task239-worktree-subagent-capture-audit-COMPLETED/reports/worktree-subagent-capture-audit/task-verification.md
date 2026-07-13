# Task 239 Verification Evidence

## Scope

Task 239 adds diagnostics, fixtures, tests, and evidence only. It does not change Aegis
runtime behavior, hooks, ledger schema, installer assets, witness policy, or installed
target behavior.

## Focused Checks

| Check | Result |
| --- | --- |
| Ruff on the new module and focused test | passed |
| `tests/claude_adapter/test_worktree_capture_audit.py` | 9 passed |
| deterministic cause replay | 10 scenarios; every cause exactly once |
| concurrent linked-worktree writers | 24/24 events preserved |
| normal teardown persistence | 10,159/10,159 pre-teardown events preserved |
| normalized live fixture secret validation | passed |
| repository secret scan | passed |

Deterministic replay status distribution:

```text
supported=1 unsupported=2 degraded=3 failed=4
```

## Repository Checks

| Check | Result |
| --- | --- |
| full pytest suite | 1,746 passed, 4 opt-in distribution/MCP smokes skipped |
| Taskmaster health | 245 tasks, 383 subtasks, 430 references, 0 invalid |
| Taskmaster dependency validation | passed |
| plan/tracker sync | passed |
| work-tracking audit | passed; no issues |
| Codex guard validation | passed |
| template drift strict check | 0 findings |
| CI-profile template scanner suite | all 6 stages passed; 0 broken references, 0 security findings |
| capsule check | passed |
| Git whitespace check | passed |

The repository-wide Ruff command reports 83 pre-existing violations in unrelated legacy
template-scanner, managed-asset, and existing test files. Task 239 does not modify those
files. The two touched Python files pass Ruff independently, and the hosted workflow does
not define repository-wide Ruff as a required check.

The upstream source checkout intentionally has no installed-target foundation manifest.
`python3 -m aegis_foundation.cli status` therefore reports `not_installed` while also
confirming the passive SQLite ledger, advisory enforcement, evidence-gated delivery
policy, and context-budgeted output. Task 239 did not initialize, repair, or fabricate
installed state. Source-repository readiness, Taskmaster, guard, plan, and tracking checks
are the applicable lifecycle gates.

## Optional Skips

The full suite's four skips are explicitly opt-in release-distribution or MCP smoke tests:

- full release certification smoke;
- real target-project MCP wheel smoke;
- local wheel CLI smoke;
- local wheel MCP smoke.

Task 239 changes no distribution, entry-point, MCP, hook, or installer behavior. The
ordinary distribution tests remain part of the 1,746 passing tests.

## Before/After Safety

- Source HEAD remained `8bf1f1871ff259987fa1b8d66d875b1adaf8d99e` during live scenarios.
- Unrelated `.codex/deep-work.config.toml` retained SHA-256 digest
  `eca031a94a46de3908dbebab0a36c466be1696e27887ef6477ab714a188868f0`.
- No `.codex`, `.agents`, or local `.aegis` drift is in Task 239's staging scope.
- Both disposable worktrees were clean before normal removal; neither branch was pushed.
- The checked-in live fixture contains no raw prompt, transcript, home path, credential,
  or absolute repository path.

## Hosted Evidence

Draft PR: `https://github.com/loucmane/codex-starter-pack/pull/264`

Exact signed implementation head:
`97663b30fb80b2ce454ec96cfd3fb4b72c5a5e33`

| Check | Result | Evidence |
| --- | --- | --- |
| Python tests (3.11) | passed in 6m09s | `https://github.com/loucmane/codex-starter-pack/actions/runs/29233323111/job/86762214614` |
| Python tests (3.12) | passed in 6m46s | `https://github.com/loucmane/codex-starter-pack/actions/runs/29233323111/job/86762214635` |
| Aegis witness | passed in 15s | `https://github.com/loucmane/codex-starter-pack/actions/runs/29233323180/job/86762214795` |
| evidence-gated delivery | passed in 10s | `https://github.com/loucmane/codex-starter-pack/actions/runs/29233323038/job/86762214543` |
| source guard | passed in 37s | `https://github.com/loucmane/codex-starter-pack/actions/runs/29233323036/job/86762214551` |
| meta-workflow guard | passed in 21s | `https://github.com/loucmane/codex-starter-pack/actions/runs/29233323085/job/86762214598` |
| baseline guard | passed in 27s | `https://github.com/loucmane/codex-starter-pack/actions/runs/29213174508/job/86704246910` |

All checks passed at the exact implementation head. A final Taskmaster/archive lifecycle
commit will receive a fresh exact-head matrix before delivery.
