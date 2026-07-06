# Task 190 — fresh-project PRD bootstrap states (design)

> Filename is the generic kickoff-scaffold name; this is the Task 190 design artifact
> (`plan-step-scope`). Continuation of the TM 188/189/225 arc.

## Problem (scope reconciliation)
`next_action` had no fresh-project bootstrap guidance. `_taskmaster_state` returned only
absent/invalid/valid: `absent` collapsed into `installed_no_current_work` ("start local work"),
and an EMPTY ledger returned `invalid` (`empty_taskmaster_tasks`) → `installed_taskmaster_invalid`
("repair Taskmaster") — wrong for a brand-new project. No PRD awareness existed.

## Design
Add five read-only bootstrap states to `next_action`'s no-current-work dispatch, between the
client-reload guard and the active-work region:

1. **`_empty_taskmaster_state`** — a zero-task ledger is now state `empty` (a fresh phase), not
   `invalid`. Genuine corruption stays `invalid`.
2. **`_prd_state` / `_prd_read_head`** — read-only, bounded (1MB), binary-skipping PRD detection.
   Canonical `.taskmaster/docs/prd.txt`/`prd.md` only (a generic `*.md` glob would false-positive
   on unrelated docs). The example template is excluded by content-equality to the live
   `example_prd.txt` + placeholder markers (no hard-coded hash → survives drift).
3. **Dispatch** (first-match): `absent`→`no_taskmaster`; `empty`+PRD→`prd_available_not_parsed`;
   `empty`+no-PRD→`taskmaster_empty`; `invalid`→`installed_taskmaster_invalid` (unchanged);
   `valid`+none-started+PRD→`prd_parsed_tasks_pending`; `valid`+none-started+no-PRD→
   `first_task_ready`; `valid`+any-started→`installed_taskmaster_present` (unchanged).
4. **5 `CONTINUATION_BRIEF_BY_STATE` entries** — separate setup/planning mutations (init,
   parse-prd, expand) from product implementation; parse-prd requires explicit approval; never
   bind a fabricated task id before the ledger exists.

## Transitions
no_taskmaster --init--> taskmaster_empty --author PRD--> prd_available_not_parsed --parse (with
approval)--> prd_parsed_tasks_pending --review/expand--> first_task_ready --kickoff-->
installed_taskmaster_present.

## Key decisions / deviations from the design workflow
- `prd_parsed_tasks_pending` vs `first_task_ready` discriminator = PRD presence (no clean on-disk
  "expansion gate" signal). Documented in DECISIONS.
- `no_taskmaster` preserves the local-work `aegis start` path (incl. `suggested_mcp=aegis.start`)
  AND adds the task-driven path; surfaces an already-authored PRD when present.
- Only the zero-task case is reclassified to `empty` (not `missing_task_container`, which stays
  invalid — fresh `task-master init` produces `{"master":{"tasks":[]}}`, the zero-task case).

## Safety invariants (locked by tests)
Detection is read-only (no parse/init side effects); pre-ledger states never emit a bound task
id; parse-prd is only suggested behind explicit approval; existing terminal states unchanged.
Adversarial review verdict: ship (no must-fix).
