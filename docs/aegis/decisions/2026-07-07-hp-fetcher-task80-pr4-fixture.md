# HP-Fetcher Task 80 Residue Is A PR-4 Fixture

Date: 2026-07-07

## Decision

Do not repair, close out, archive, or clear HP-Fetcher's stale Aegis Task 80 workflow
state just to make strict verification green.

Treat the HP-Fetcher Task 80 residue as a real PR-4 replacement-parity fixture. It should
remain preserved until Task #210 / PR-4 proves, row by row through
`docs/aegis/pr-4-replacement-parity-matrix.md`, that the capsule + ledger + witness stack
replaces each old workflow responsibility with equal or better behavior and a rollback path.

## Observed State

This was observed in `/home/loucmane/dev/hpfetcher` after refreshing the installed Aegis
runtime assets to upstream commit `e765f01` (`feat: add computed capsule task orientation
(#252)`).

The refreshed capsule correctly identified the mismatch:

- Taskmaster marks Task 80 as done and superseded.
- The computed capsule reads that Taskmaster truth and reports Task 80 as done/superseded.
- The old Aegis workflow state still has `.aegis/state/current-work.json`,
  `plans/current`, `sessions/current`, and the Task 80 work-tracking folder pointing at
  Task 80 as the active/in-progress envelope.
- Strict verify fails old workflow gates such as branch/task alignment, reports, and
  pending tracking.
- Advisory mode records those would-block decisions without interrupting current product
  work.

## Rationale

The residue is not evidence that the new capsule is stale. It is evidence that the capsule is
doing the intended job: computing current truth from git, Taskmaster, and runtime state, then
surfacing disagreement with old scaffold state.

Manually repairing the residue now would weaken PR-4 evidence. It would make one target repo
look cleaner while removing a concrete example of the legacy responsibilities PR-4 must
replace:

- active task identity previously owned by `current-work.json`
- continuity pointers previously owned by `plans/current` and `sessions/current`
- human-readable task history in work-tracking folders
- pending mutation completeness previously owned by `pending-tracking.json`
- strict readiness and closeout gates previously tied to those surfaces

The project policy is replacement before retirement. Old sessions, plans, trackers, closeout
surfaces, and pending-tracking machinery remain present until the parity matrix authorizes a
specific demotion or retirement.

## PR-4 Implications

Task #210 / PR-4 should use this fixture when evaluating retirement behavior:

- `current-work.json` must not remain authoritative when Taskmaster and the capsule agree it
  is stale.
- `plans/current` and `sessions/current` should remain `shadow` or `keep` until ledger and
  capsule session identity recover the same continuity facts.
- Task 80's work-tracking folder should remain preserved as historical evidence unless a
  parity row explicitly authorizes demotion or archive behavior.
- The pending-tracking queue should not be drained as a cleanup task; PR-4 must replace its
  responsibility with passive ledger and boundary witness evidence before demoting it.
- Strict verify failures caused only by this legacy residue are advisory dogfood evidence,
  not product-work blockers while HP-Fetcher stays in advisory mode.

## Commands Not Authorized By This Decision

This decision does not authorize:

- `aegis repair --apply`
- `aegis closeout`
- `task-master set-status`
- moving or renaming Task 80 work-tracking folders
- deleting or draining `.aegis/state/pending-tracking.json`
- removing sessions, plans, trackers, handoffs, or closeout scaffolding

Those actions require an explicit PR-4 parity row, dogfood evidence, and rollback path, or a
separate owner approval for a narrow operational repair.

## Operational Guidance

For HP-Fetcher product work, keep enforcement in advisory mode and continue from the capsule,
git, and Taskmaster truth. Treat stale Task 80 workflow-state failures as known legacy
residue unless they reveal a real product-work risk.

For upstream Aegis work, use this fixture as a negative test: PR-4 must not make old state
authoritative again, and must not hide the mismatch by deleting evidence before replacement
parity is proven.
