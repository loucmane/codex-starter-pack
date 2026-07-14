# Task 253 Tracked Codex Hook-Trust Verification — 2026-07-14

## Scope

Task 253 removes strict verification's dependency on the ignored Aegis install report. The implementation is limited to the root installer, its packaged asset mirror, focused installer regression tests, and task evidence.

## Root Cause

`codex.hook_trust_guidance` read `.aegis/reports/install-report.json`. Clean clones intentionally lack that generated report, so tracked managed assets could be correct while strict verification failed.

## Decision

Derive guidance only from exactly one complete tracked `codex.hook_trust` manifest gate. Missing, duplicate, malformed, or altered semantics fail closed. Manual `/hooks` review, exact hook-definition hashing, and the no-bypass boundary remain unchanged.

## Verification State

- Focused clean-checkout and adversarial tests pass.
- Schema, adapter, and root/packaged parity tests pass.
- Complete installer suite passes with 143 tests; one explicit opt-in certification smoke is skipped.
- Taskmaster health and dependency validation pass.
- Codex Guard, Meta Workflow Guard, timestamp checks, scanners, and generated-report gates pass.
- Exact parallel CI pytest passes with 2,040 tests and four explicit opt-in distribution/certification smokes skipped.

## Continuation

Close Task 253 through supported workflows, open an attended upstream PR, and wait for hosted Python 3.11/3.12 and guard checks. The dirty primary checkout must remain untouched.

This tracked continuity file was written with native file tooling because no Serena MCP tool was available in the session.
