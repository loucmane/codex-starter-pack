# Task 149 Define reconcile apply-path proposal contract – Implementation Notes

## Implemented Workstreams
- Added `docs/aegis/reconcile-apply-path-proposal-contract.md` as the Task 149
  contract artifact. The document is contract-only: no enabled mutation, no
  `--apply`, no writer path, no default preview behavior.
- Centered the missing design decision: future apply must be agent-excluded.
  The governed agent cannot invoke apply or satisfy confirmation; first
  acceptable channels are post-merge CI or operator-controlled local invocation.
- Preserved the first future apply class as `merged_but_not_done` with
  `git_ancestor` proof only, and documented all excluded/manual-only classes.
- Added explicit prerequisites for a future implementation: agent-context
  refusal, apply-audit breadcrumbs, global kill-switch, exact Task 145
  side-effect proof, Task 146 precision, Task 147 rollback, and Task 148
  inertness.
- Embedded a Claude discussion prompt focused on invocation safety, kill-switch
  semantics, apply-audit content, and whether Task 150 should be a disabled
  scaffold with an unsatisfiable enable gate.
- Added
  `tests/meta_workflow_guard/test_aegis_reconcile_apply_path_proposal_contract.py`
  to enforce the design-only boundary, agent-excluded invocation model, first
  candidate/exclusion scope, no mutation flags, no MCP mutation parameters, no
  writer consumption, and no enabled apply path in reconcile.
