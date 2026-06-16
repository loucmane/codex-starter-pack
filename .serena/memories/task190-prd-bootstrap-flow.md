# Task 190 — fresh-project PRD bootstrap states in `aegis next`

**Status:** done (2026-06-16), branch `feat/task-190-prd-bootstrap-flow`. Continuation of the
188/189/225 arc. Built with design + adversarial-review workflows (verdict: ship).

## What shipped (scripts/_aegis_installer.py)
5 read-only bootstrap states in `next_action`'s no-current-work dispatch, BEFORE the
task-selection branch:
- `absent` → `no_taskmaster` (preserves `aegis start` local-work path incl.
  suggested_mcp=aegis.start, ADDS task-master init/PRD path, surfaces an existing PRD)
- `empty` + PRD → `prd_available_not_parsed`; `empty` + no PRD → `taskmaster_empty`
- `valid` + none-started + PRD → `prd_parsed_tasks_pending`; + no PRD → `first_task_ready`
- `valid` + any in-progress/done/completed → `installed_taskmaster_present` (UNCHANGED)
- genuine corruption → `installed_taskmaster_invalid` (UNCHANGED)

Supporting: `_empty_taskmaster_state` (zero-task ledger is `empty`, not `invalid`);
`_prd_state`/`_prd_read_head` (canonical prd.txt/prd.md only, excludes example template by
content+markers, bounded 1MB read, binary-skip); 5 `CONTINUATION_BRIEF_BY_STATE` entries.

## Reusable knowledge
- `_taskmaster_state` now returns absent/empty/invalid/valid. `empty` = fresh-init (NOT corruption).
- PRD detection is canonical-name-only by design (generic *.md would false-positive on
  `reconcile-enablement-gate-backlog-amendment.md`); non-canonical names are a conservative miss.
- `prd_parsed_tasks_pending` vs `first_task_ready` discriminator = PRD presence (no on-disk
  "expansion gate" signal exists).
- `installed_no_current_work` next_action return is now an unreachable defensive fallthrough; its
  brief + `_classify_doctor_state` usage stay live.
- `started` predicate = in-progress/done/completed only; all-terminal (cancelled/deferred/blocked)
  ledgers route to first_task_ready (safe, wording defers to `task-master next`).

## Test impact
New test_prd_bootstrap_states.py (12). Updated 4 existing tests (installed_no_current_work→
no_taskmaster ×2; installed_taskmaster_present→first_task_ready for a single pending task;
removed empty-ledger case from the invalid parametrize). Full suite 1699 passed (parallel).
See [[task193-ci-feedback-time]], [[task225-doctor-repair-states]].
