# Task 254 Verification Evidence

## Implementation scope

- Live/packaged installer assets persist and validate the exact tracked hook-trust procedure.
- Live/packaged manifest schemas require the no-bypass exact-definition contract.
- Install-report evidence is supplemental and cannot override tracked guidance.
- Tests cover clean worktrees, malformed/weakened guidance, stale reports, and hash renewal.

## Static and parity checks

- Black: passed after formatting the four touched Python files.
- Ruff: passed.
- `py_compile`: passed.
- Root/package installer parity: byte-identical.
- Root/package foundation-manifest schema parity: byte-identical.
- Both JSON schemas parse successfully.
- `git diff --check`: passed.
- Taskmaster health: 253 tasks, 386 subtasks, 442 dependency references, zero invalid references.
- Plan sync: passed.
- Work-tracking audit: passed with no issues.
- S:W:H:E guard: passed with all entries compliant.
- Whole-file mypy: 266 pre-existing errors in the large installer/managed-update surfaces and the
  byte-identical packaged installer; not used as a Task 254 regression gate.

## Automated tests

- Focused installer and Codex-adapter matrix: **166 passed, 1 skipped** in 65.96s.
  The skip is the explicitly opt-in full release-certification smoke.
- Full repository suite with xdist: **2,059 passed, 4 skipped** in 73.83s.
  The skips are explicitly opt-in wheel, wheel-MCP, certification, and target-MCP smoke tests.

## Clean secondary-worktree regression

The test creates a committed tracked installation, adds a real Git secondary worktree with generated
outputs absent, runs kickoff/log/strict verification, repairs only the generated handoff projection,
and runs closeout dry-run. `codex.hook_trust_guidance` and closeout pass with zero required failures;
the dry-run remains non-mutating.

## `/tmp/blog-task42` acceptance

Baseline under the previous source reproduced exactly one required failure:
`codex.hook_trust_guidance`. `.aegis/reports/install-report.json` was absent.

Acceptance under the Task 254 runtime and exact tracked contract:

- command return code: 0;
- strict verification status: passed;
- required failures: 0;
- guidance source: `manifest_gate`;
- `client_trust_asserted`: false;
- supplemental install report: absent;
- no install report copied or synthesized;
- 1,031 Git-visible Task 42 records inventoried before and after;
- dirty-status snapshot unchanged;
- every inventoried byte/mode/symlink record unchanged;
- original manifest, verification report, and capsule state restored in the acceptance script's
  `finally` boundary.

Task 42 product and evidence files therefore remained untouched.

## Source-workflow note

The intentionally uninstalled upstream source worktree has no `.aegis/foundation-manifest.json`.
Running its installed-target strict CLI produced the expected single `aegis.manifest` failure and
guidance to install Aegis; this is not an implementation failure and no installed state was
fabricated. Source workflow completion is established through Taskmaster, plan/tracker parity,
guard/audit checks, the supported archive flow, and the installed-target regressions above.
