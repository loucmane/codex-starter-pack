# Task 190 Support fresh-project PRD bootstrap continuation flow – Implementation Notes

## Changes (scripts/_aegis_installer.py)
- `_empty_taskmaster_state()` + `_validate_taskmaster_tasks`: a zero-task ledger now returns
  state `empty` (a fresh-project phase) instead of `invalid`. Genuine corruption stays `invalid`.
- `_prd_state(target_root)` + `_prd_read_head`: read-only, bounded (1MB), binary-skipping PRD
  detection. Canonical `prd.txt`/`prd.md` only; the example template is excluded by
  content-equality + placeholder markers.
- `next_action` no-current-work dispatch now emits the 5 bootstrap states:
  `absent`→`no_taskmaster` (preserves the local-work `aegis start` path + adds init/PRD;
  surfaces an already-authored PRD), `empty`+PRD→`prd_available_not_parsed`,
  `empty`+no-PRD→`taskmaster_empty`, `valid`+none-started+PRD→`prd_parsed_tasks_pending`,
  `valid`+none-started+no-PRD→`first_task_ready`. `installed_taskmaster_present` (a task
  started) and `installed_taskmaster_invalid` (genuine corruption) are unchanged.
- `CONTINUATION_BRIEF_BY_STATE`: 5 new entries (setup/planning mutations separated from product
  implementation; parse-prd requires explicit approval; never bind a fabricated task id).
- `aegis_foundation/assets/scripts/_aegis_installer.py`: re-mirrored byte-identical (TM 219).

## Tests
- New `tests/meta_workflow_guard/test_prd_bootstrap_states.py` (12): every state + boundaries
  (example-template rejection, non-canonical doc, whitespace PRD, read-only detection, no
  fabricated task id, regressions for present/invalid).
- Updated 4 existing tests for the new (correct) routing (`installed_no_current_work`→
  `no_taskmaster` ×2; `installed_taskmaster_present`→`first_task_ready` for a single pending
  task; removed the empty-ledger case from the invalid parametrize).

## Method
Design workflow (5 agents) mapped the dispatch + PRD detection; adversarial-review workflow
(5 agents) returned **ship** (no must-fix). Folded in the cheap polish it surfaced: bounded/
binary-safe PRD read, no_taskmaster surfaces an existing PRD, softened first_task_ready wording
for all-terminal ledgers + documented the `started` predicate, annotated the now-defensive
`installed_no_current_work` fallthrough, tightened the fake-task-binding test helper. See
designs/wizard-flow.md and DECISIONS.md.

## Verification
Full suite green (parallel via TM 193); see reports/.
