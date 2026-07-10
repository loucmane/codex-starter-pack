# TM-234 Witness And Delivery Boundary Projection Design

## Purpose

TM-233 proved that selected passive-ledger events can regenerate marker-bounded S:W:H:E
sections across existing session, plan, tracker, implementation, changelog, decisions, and
handoff files without overwriting human-authored content. TM-234 wires the next two explicit
workflow boundaries:

1. deterministic local delivery witness evaluation;
2. machine-observed git and GitHub delivery state synchronization.

This slice does not retire, demote, or stop validating any legacy surface. TM-210 remains
blocked on the TM-229 replacement-parity matrix.

## Authority

- Witness truth comes from the structured report returned by `witness_lib.run_witness`.
- Branch and upstream truth come from git.
- Pull-request truth comes from `gh pr list` or `gh pr view` through the existing installer
  helpers.
- The append-only ledger is the machine-event source for generated legacy projections.
- Human prose outside the generated marker block remains human-owned.

No command accepts a caller-supplied PR state, witness verdict, check result, merge state, or
commit as authoritative truth.

## CLI Contract

### `aegis witness`

For a local witness run:

1. refresh the capsule at the pre-delivery boundary;
2. run the deterministic witness and write its normal report;
3. normalize a `witness` ledger event from the report;
4. append it only if its boundary fingerprint differs from the newest matching event;
5. project the selected ledger slice into existing active legacy surfaces;
6. return the original witness exit code regardless of projection success.

For `--ci`:

- retain current witness behavior;
- do not append to the persistent ledger;
- do not write legacy projections;
- report boundary recording as skipped for `ci_mode`.

The JSON report gains advisory `boundary_event` and `legacy_projection` fields. The text report
may add a concise projection status line, but witness PASS/FAIL remains solely the result of the
deterministic witness checks.

### `aegis delivery sync`

Command shape:

```text
aegis delivery sync --target-dir . [--pr <number>] [--branch <name>] [--json]
```

Resolution rules:

- `--pr` queries that exact PR and supports post-merge synchronization after branch switching.
- `--branch` queries that branch; absent means the current git branch.
- no upstream and no PR yields `local_only` and no delivery event;
- upstream with no PR yields `branch_pushed`;
- draft PR yields `pr_draft`;
- non-draft open PR yields `pr_open`;
- merged PR yields `pr_merged`;
- closed, unmerged PR yields `pr_closed`;
- unavailable or invalid GitHub truth returns nonzero and appends nothing.

The command records the normalized snapshot and projects existing surfaces. It does not push,
open, ready, close, or merge a PR. Merge approval remains a separate human boundary.

## Event Contract

### Witness event

```json
{
  "event_type": "witness",
  "branch": "feat/task-234-witness-delivery-projection",
  "outcome": "pass",
  "exit_class": "pass",
  "extra": {
    "action": "witness",
    "base": "origin/main",
    "boundary_fingerprint": "sha256:...",
    "checks": {"scope_mapping": "pass"},
    "head_commit": "abc1234",
    "mode": "local",
    "passed": true,
    "report_path": ".aegis/reports/witness-report.json",
    "work_id": "task-234-witness-delivery-projection"
  }
}
```

### Delivery event

```json
{
  "event_type": "delivery",
  "branch": "feat/task-234-witness-delivery-projection",
  "outcome": "pass",
  "exit_class": "pass",
  "extra": {
    "action": "pr_open",
    "boundary_fingerprint": "sha256:...",
    "checks_state": "passed",
    "head_commit": "abc1234",
    "pr_number": 256,
    "state": "OPEN",
    "url": "https://github.com/example/repo/pull/256",
    "work_id": "task-234-witness-delivery-projection"
  }
}
```

Raw command strings, tokens, environment values, and full hook payloads are not stored in these
boundary events or rendered into legacy files.

## Deduplication

The boundary fingerprint is SHA-256 over canonical JSON containing only normalized fields that
define the boundary state.

Witness fingerprint fields:

- mode;
- branch;
- base;
- head commit;
- passed;
- normalized per-check status;
- escalations.

Delivery fingerprint fields:

- canonical action;
- branch;
- upstream;
- PR number and URL;
- PR state, draft state, merge state, and merged timestamp;
- head commit;
- summarized check state.

Before append, read matching events for the branch and event type. If the newest matching event
has the same fingerprint, return `unchanged` and reuse its event ID. Projection may still run so
missing or stale generated blocks can be rebuilt, but repeated identical calls must leave every
target byte-stable.

## Projection Semantics

- Add `witness` to the default high-signal event set.
- Render witness entries with `H:witness` and evidence pointing to the ledger event ID.
- Render the report path, PASS/FAIL, and head commit in normalized prose.
- Continue rendering delivery entries with `H:delivery`, now including canonical action, PR
  number when present, and head commit.
- Resolve existing surfaces through `current-work.json`, including completed archived folders.
- Never create legacy scaffolding when none exists.
- Never write outside the generated markers.

Projection exceptions are captured as structured warning metadata. They do not roll back the
ledger append and do not change witness or delivery-truth outcomes.

## Implementation Boundaries

- `aegis_foundation/cli.py`: CLI parsers, boundary normalization, deduplicated append, and
  projection orchestration.
- `aegis_foundation/legacy_projection.py`: witness selection and normalized rendering.
- `scripts/_aegis_installer.py`: reusable git/GitHub delivery snapshot helper.
- `aegis_foundation/assets/scripts/_aegis_installer.py`: byte-identical packaged mirror.
- tests: unit normalization, deduplication, CLI behavior, failed projection behavior, CI skip,
  GitHub unavailable behavior, and packaged/live parity.

The async Claude recorder remains unchanged in this slice. It may continue recording raw
delivery tool observations, but the explicit delivery boundary is the authoritative normalized
snapshot and must deduplicate only against other normalized boundary snapshots.

## Dogfood

Use blog draft PR #6:

1. update the target runtime to the TM-234 branch through source-root mode;
2. record explicit scope for the infrastructure paths;
3. run local witness and confirm a witness entry reaches all eight archived surfaces;
4. run `aegis delivery sync --pr 6` and confirm an open/draft delivery entry reaches the same
   surfaces;
5. repeat both commands and prove no new ledger event and `changed: false` projections;
6. verify marker-external hashes are unchanged;
7. commit the updated projections to PR #6 as dogfood evidence.

## Acceptance

- Local witness outcome is reconstructable from ledger plus report.
- Delivery state is derived from git/GitHub, never caller narration.
- Identical boundary calls are event-idempotent and projection-idempotent.
- CI witness does not persist boundary state.
- Projection failure cannot turn witness PASS into failure or witness FAIL into success.
- Human-authored content remains byte-identical outside markers.
- Blog PR #6 contains real projected scope, witness, and delivery evidence.
- TM-229 records the new evidence without changing any PR-4 row to retire.
