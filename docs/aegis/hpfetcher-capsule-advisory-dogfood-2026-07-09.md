# HP-Fetcher Capsule Advisory Dogfood - 2026-07-09

Target repo: `/home/loucmane/dev/hpfetcher`

Scope: downstream dogfood for the Aegis capsule, advisory enforcement, passive gate-decision
recording, verification ledger, and legacy workflow-surface replacement plan. This note records
observed evidence only. It does not authorize repair, closeout, pending-tracking drain, or
retirement of old sessions/plans/trackers.

## Why This Matters

HP-Fetcher now has enough live advisory-mode history to evaluate the capsule model against real
operator behavior, not a synthetic cold-start workload. The operator primarily resumes long
sessions rather than starting clean sessions, so the value signal is resume-time truth refresh:
does the capsule revalidate drift, stale verification, task truth, PR state, and legacy workflow
residue before the agent acts?

The 2026-07-09 snapshot says yes. The capsule is no longer just a handoff replacement candidate;
it is already compiling useful truth that old scaffolding failed to keep current.

## Stable Capsule Snapshot

Observed from `.aegis/capsule/current.json` and `.aegis/capsule/current.md` compiled at
`2026-07-09T15:13:24Z`.

- Branch: `main`
- Source commit: `3fc7a73`
- Upstream state: `ahead: 0`, `behind: 0`
- Tracked dirty files:
  - `.taskmaster/tasks/tasks.json`
  - `AGENTS.md`
  - `CLAUDE.md`
- Untracked count: `95`
- Ledger events at compile time: `32180`
- Ledger span: `2026-06-11T11:17:25Z` to `2026-07-09T15:13:23Z`
- Gate decisions at compile time: `16227`
- Latest gate decision at compile time: `2026-07-09T15:13:16Z`
- Governance mode: `advisory`
- Governance reason: `product work; program Phase 0`
- Decisions since previous capsule: `782 would_block`, `211 allow`

## Read-Time Append-Only Surfaces

Observed directly from live files after the capsule compile. These files were still growing under
advisory mode while agents worked, so these counts are read-time counts rather than stable capsule
snapshot counts.

- `.aegis/reports/gate-decisions.jsonl`: `16453` lines
- Gate verdict counts:
  - `14336 would_block`
  - `2117 allow`
- `.aegis/state/pending-tracking.json`: `1659` advisory events
- `.aegis/reports/observation-report.json`: `36036252` bytes, preserving the old report-bloat
  fixture

## Capsule Value Observed

The capsule surfaced current operator-relevant truth without requiring a fresh transcript scan:

- `app:test` passed at `e75df8a` on `2026-07-09T10:46:46Z`, but is stale because HEAD moved.
- `app:typecheck` passed at `fd0fb70` on `2026-06-11T12:48:43Z`, also stale.
- `app:build`, `app:e2e`, `app:lint`, `worker:lint`, `worker:test`, and `worker:typecheck`
  have no run on record.
- Open PR state is stale because `gh` timed out or was unavailable.
- Task truth says Task 80 is done and superseded, but legacy current-work still orients through
  Task 80.
- Task-truth events were recorded while `tasks.json` changes were still uncommitted.
- A done-flip sits uncommitted in `tasks.json`, reproducing the stranded-flip class.
- The drift sentinel caught the planted canary and real drift:
  - `CLAUDE.md` claims 79 parent tasks while `tasks.json` has 92.
  - local branch count is 149 and exceeds the hygiene threshold.

This is the intended "resume-drift refresh" value. The capsule is computing facts that a long
chat can easily misremember.

## Gate-Decision Evidence

Overall verdict distribution from `.aegis/reports/gate-decisions.jsonl` at read time:

| Verdict | Count |
| --- | ---: |
| `would_block` | 14336 |
| `allow` | 2117 |

Hook distribution from the same file:

| Hook | Count |
| --- | ---: |
| `pretooluse` | 16040 |
| `stop` | 410 |

Dominant tool distribution:

| Tool | Count |
| --- | ---: |
| `Bash` | 14312 |
| `Edit` | 741 |
| `Stop` | 410 |
| `Write` | 329 |
| `mcp__chrome-devtools__evaluate_script` | 158 |
| `mcp__chrome-devtools__take_screenshot` | 149 |
| `mcp__chrome-devtools__navigate_page` | 116 |
| `mcp__playwright__browser_take_screenshot` | 42 |
| `mcp__playwright__browser_navigate` | 35 |

Reason distribution:

| Reason | Count |
| --- | ---: |
| `readiness_blocked` | 13952 |
| `read_only` | 2025 |
| `pending_tracking` | 380 |
| `no_pending_tracking` | 73 |
| `allow` | 19 |
| `workflow_owned_path` | 2 |

## July 8-9 Spike

The recent dogfood is materially richer than the original June evidence:

| Date | Gate decisions |
| --- | ---: |
| `2026-07-08` | 7129 |
| `2026-07-09` | 2850 |

For `2026-07-08` and later, reason distribution was:

| Reason | Count |
| --- | ---: |
| `readiness_blocked` | 9140 |
| `read_only` | 779 |
| `pending_tracking` | 61 |

Dominant `2026-07-08+` verdict/tool/reason combinations:

| Count | Verdict | Tool | Reason |
| ---: | --- | --- | --- |
| 8931 | `would_block` | `Bash` | `readiness_blocked` |
| 770 | `allow` | `Bash` | `read_only` |
| 133 | `would_block` | `Edit` | `readiness_blocked` |
| 75 | `would_block` | `Write` | `readiness_blocked` |
| 61 | `would_block` | `Stop` | `pending_tracking` |

## Interpretation

This dogfood strengthens the vNext direction:

- Advisory mode is working as the evidence lane: product work continues while would-block
  decisions are recorded.
- Strict legacy readiness would still be unusable for this target repo. Most would-blocks are
  `readiness_blocked`, commonly caused by work on `main` or stale current-work/task-envelope
  assumptions, not necessarily unsafe product edits.
- The capsule is useful for resumed sessions. It catches stale tests, dirty task flips, stale PR
  lookup, Taskmaster/current-work disagreement, and seeded risk state.
- Verification evidence is useful but incomplete. The ledger can mark old passes stale, but the
  delivery boundary still needs a witness that refuses merge when required gates are missing or
  stale.
- Advisory pending events are evidence, not debt that should be drained as if strict mode were
  active. Their lifecycle needs an explicit PR-4 rule.
- Old workflow surfaces still contain value and residue. Removing them now would destroy a
  concrete replacement-parity fixture.

## PR-3 Implications

PR-3 narration remains optional and should be justified by evidence that deterministic capsules
cannot preserve needed intent. This snapshot shows deterministic fields already cover much of the
operator's resume need:

- current branch and dirty state
- stale verification
- task-truth drift
- uncommitted done-flips
- stale PR lookup
- risk-register reminders
- legacy current-work residue

The next PR-3 test should be narrow: identify which decisions or "why" facts are still not
recoverable from deterministic ledger/capsule fields before adding narrated distill machinery.

## PR-4 Implications

Do not retire old sessions, plans, trackers, current-work, closeout surfaces, or pending tracking
based only on the presence of the capsule. The HP-Fetcher evidence says replacement must be row by
row:

- `current-work.json` is stale and should not remain authoritative when Taskmaster and capsule
  agree it is stale.
- `plans/current` and `sessions/current` still represent legacy continuity pointers and should not
  be deleted until the capsule and ledger recover the same continuity facts.
- Task 80's tracking folder remains useful historical evidence for replacement parity.
- Advisory-era pending events should not brick strict re-entry, but also should not be silently
  discarded without a documented lifecycle.
- Boundary witness must exist before old closeout claims are retired. The witness should block
  merge, not editing, when verification is missing or stale at HEAD.

This reinforces `docs/aegis/decisions/2026-07-07-hp-fetcher-task80-pr4-fixture.md`.

## Commands Not Authorized By This Note

This note does not authorize:

- `aegis repair --apply`
- `aegis closeout`
- `task-master set-status`
- clearing or draining `.aegis/state/pending-tracking.json`
- moving or renaming Task 80 work-tracking folders
- deleting legacy sessions, plans, trackers, handoffs, implementation logs, decisions, or
  changelog surfaces

Those actions require an explicit PR-4 parity row, acceptance evidence, and rollback path, or a
separate owner approval for a narrow operational repair.

## Next Evidence To Capture

- A dated witness dry-run against the current HP-Fetcher state, especially stale verification at
  HEAD.
- A comparison between capsule orientation and a human/agent transcript scan for the same resume.
- A lifecycle rule for advisory-era pending events: retained as audit, summarized into capsule, or
  reconciled at boundary without strict-mode ambush.
- A report-size budget check that keeps the 36 MB observation report as a regression fixture.
- A `gh`-available run so the capsule can distinguish "no open PRs" from "PR state unavailable."

## Validation Notes

This note was produced from read-only inspection of `/home/loucmane/dev/hpfetcher` Aegis
surfaces. Broad home-directory ledger discovery was intentionally stopped after repo-local
surfaces provided sufficient evidence.
