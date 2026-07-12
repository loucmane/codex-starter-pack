# Task 244 Verification

Date: 2026-07-11

## Scope

- source-only completed-work resolver;
- canonical and packaged readiness integration;
- canonical and packaged `codex-guard` integration;
- source/installed positive and fail-closed fixtures;
- archive preservation and next-task kickoff behavior;
- source closeout documentation and rollback.

## Results

| Check | Result |
|---|---|
| Source closeout contract fixtures | 13 passed |
| Existing guard regression suite | 83 passed |
| Archive and kickoff focused tests | 2 passed |
| Post-dogfood workflow regression set | 307 passed |
| Complete installer suite | 121 passed, 1 opt-in certification smoke skipped |
| Final CI-equivalent coverage | 1,771 passed under xdist plus 1 stdio smoke passed in isolation; 4 existing opt-in distribution smokes skipped |
| Ruff for new helper and fixture | Passed |
| Canonical/package readiness parity | Byte-identical |
| Canonical/package guard parity | Byte-identical |
| Taskmaster health | 243 tasks, 383 subtasks, 428 valid dependency references, 0 invalid |
| Dependency validation | Passed |
| Git whitespace validation | Passed |

The four full-suite skips require explicit release/wheel/MCP smoke environment flags and are
unchanged by Task 244. Hosted CI remains authoritative for Python 3.11 and 3.12 after delivery.

## Fail-Closed Coverage

- non-done or missing Taskmaster task;
- zero or multiple matching archives;
- missing, mismatched, or non-completed tracker;
- archive symlink;
- installed manifest or current-work state;
- incomplete completed-plan checklist;
- active envelope precedence;
- next active task with the previous completed archive retained.
- next-day continuation directly from the completed source archive.

## Live Dogfood Gate

Before delivery, Task 244 must mark its plan/tracker complete, set Taskmaster to `done`, archive
its own work-tracking bundle, and prove source readiness plus `codex-guard` resolve the completed
archive without `.aegis/state/current-work.json`. The final result is appended below after that
transition.

## Live Dogfood Result

Task 244 was marked `done`, regenerated with the targeted Taskmaster helper, and archived through
`work-tracking archive`. Readiness immediately derived the completed tracker and reported READY
without `.aegis/state/current-work.json`.

The first guard run correctly exposed a stale-reference integration defect: the plan evidence
still named the ACTIVE bundle after that bundle had moved. The archive transition was updated to
rewrite only exact moved-root references in the archive Markdown, current plan, and current
session, and to append a fresh plan/tracker sync record only for an uninstalled source checkout.
Focused regression tests cover both the source rewrite/hashes and unchanged installed-target
behavior. Replaying the live archive transition then produced:

- source readiness READY for completed Task 244;
- completed tracker derived from
  `docs/ai/work-tracking/archive/20260711-task244-derivable-source-closeout-COMPLETED`;
- no installed current-work state;
- a 2026-07-12 continuation session created directly from the completed archive without
  recreating ACTIVE state;
- `codex-guard validate --include-untracked` passed with only the explicitly excluded,
  user-owned `.codex`, `.agents`, and local `.aegis` drift omitted from task scope; and
- all 1,772 collected tests covered: 1,771 under xdist and the stdio smoke in isolation, with
  four unchanged opt-in smoke skips.

The first final xdist run completed all ordinary tests but the existing bounded stdio MCP smoke
received three of four responses before its 120-second worker timeout; the server log showed the
fourth request had been processed. The exact smoke passed immediately in isolation. The race
recurred after the rollover fixture was added, while the other 1,771 tests passed under xdist.
This is a `select` plus `TextIOWrapper` buffering defect in the smoke harness, not evidence of a
server failure; it remains a separate follow-up rather than an unrelated Task 244 code change.

## Hosted Guard Feedback

The first branch guard run failed before validation because CI invokes
`python3 scripts/codex-task plan sync` without an explicit tracker. Its default resolver still
required an ACTIVE folder even though readiness, guard, archive, and session continuation already
used the completed-source authority. The default tracker resolver now consumes the same derivation,
and the completed-source continuation fixture executes that exact no-argument plan-sync path.

After the correction, the exact CI command passed locally, the focused 307-test set passed, the
1,771-test non-stdio xdist matrix passed, the bounded stdio smoke passed in isolation, and source
readiness plus the scoped guard remained green.

The first PR-context rerun then showed that GitHub checks out a detached commit. `codex-task`
supplied an empty branch to the fail-closed resolver, while `codex-guard` already used
`GITHUB_HEAD_REF`/`GITHUB_REF_NAME`. The task helper now follows that existing identity order.
A detached-checkout simulation with `GITHUB_HEAD_REF=feat/task-244-derivable-source-closeout`
passes the exact no-argument plan-sync command.
