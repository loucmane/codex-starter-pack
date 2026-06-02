# Task ID: 149

**Title:** Define Reconcile Apply-Path Proposal Contract

**Status:** done

**Dependencies:** 148 ✓

**Priority:** medium

**Description:** Create a medium-priority, design-only Aegis contract for the future reconcile apply invocation and confirmation model while keeping reconcile strictly read-only. The primary deliverable is not another Tasks 144-148 precondition enumeration; it is a reviewed contract proving that any future apply path is agent-excluded, unavailable through current reconcile CLI/MCP surfaces, and limited to the smallest future mutation class without implementing or enabling mutation behavior.

**Details:**

Revise/complete `docs/aegis/reconcile-apply-path-proposal-contract.md` and matching guard tests in `tests/meta_workflow_guard/test_aegis_reconcile_apply_path_proposal_contract.py`. Build on the existing read-only reconcile stack: `scripts/_aegis_installer.py::reconcile`, `_reconcile_mutation_candidate_preview`, `format_reconcile_summary`, `scripts/codex-task` `aegis reconcile` parser, `aegis_foundation/cli.py::handle_reconcile`, and MCP `aegis_mcp/server.py::aegis_reconcile`. The observed current surfaces expose only read-only reconcile plus opt-in inert `--preview-candidates` / `preview_candidates`; Task 149 must preserve that boundary.

The design artifact must make the invocation/confirmation model the load-bearing decision. Future apply must be agent-excluded: the governed agent that produced or consumed a reconcile report cannot invoke apply, cannot satisfy confirmation, and cannot call apply through MCP, `scripts/codex-task aegis reconcile`, or `aegis reconcile --apply`. Do not add `--apply`, `--auto`, `--fix`, `--set-status`, `--status`, `--done`, `--write`, `--mutate`, or equivalent reconcile flags; do not add writer code; do not create an enabled execution scaffold; and do not make any existing writer consume `mutation_candidate_preview`.

Define the first acceptable future invocation channels as: post-merge CI after protected-branch merge truth is established, or operator-controlled local invocation outside the governed agent runtime. Confirmation must be explicit, non-default, and supplied by an actor outside the governed agent. The contract should state that agent shell execution, MCP invocation, or tool-mediated typing of confirmation is not acceptable confirmation.

Keep the first future apply class scoped to `merged_but_not_done` with `git_ancestor` proof, current Taskmaster status not `done`, proposed status `done`, and allowed delta exactly `.taskmaster/tasks/tasks.json` plus `.taskmaster/tasks/task_<id>.md`. Explicitly exclude `github_pr_merged`, `done_but_not_merged`, `multi_pr_epic_ambiguity`, `abandoned_in_progress_branch`, `stale_local_stub`, `local_ad_hoc_stub`, and `git_only_non_ancestor_or_missing_base` until separately proven. Reference Tasks 144-148 as inherited gates, but avoid turning the document into another broad precondition inventory.

Add the missing prerequisites for any future disabled scaffold: apply-audit breadcrumbs and a global kill-switch. The apply-audit model must require before/after breadcrumbs with handler, invocation channel, task id, proof, current/proposed status, allowed-delta inventory, timestamp, outcome, and rollback status; the before breadcrumb must exist before any write. The global kill-switch must disable apply across every invocation channel by default and must be impossible for the governed agent to bypass.

Document that future Task 150 should be a disabled apply orchestration scaffold only after this invocation model is reviewed. Task 150 must use an intentionally unsatisfiable enable gate, wire side-effect/precision/rollback/audit/kill-switch checks in disabled form, and still leave reconcile read-only until a later reviewed task proves real enablement.

Include a Claude discussion prompt in the doc asking reviewers to challenge whether the agent-excluded invocation model is enforceable, whether post-merge CI and operator-local channels are the right first channels, whether `merged_but_not_done` with `git_ancestor` remains narrow enough, whether apply-audit breadcrumbs and the kill-switch are enforceable before any write, and whether any agent could misread the contract or preview as permission to mutate now. The prompt must state that Task 149 is contract-only and reconcile remains read-only.

**Test Strategy:**

Add or update documentation contract checks plus guard tests in `tests/meta_workflow_guard/test_aegis_reconcile_apply_path_proposal_contract.py`. Tests should assert the contract text centers the `Invocation And Confirmation Decision`, states future apply is agent-excluded, forbids governed-agent invocation and confirmation, forbids MCP exposure and `aegis reconcile --apply`, names post-merge CI and operator-controlled local invocation as first acceptable channels, and preserves design-only/no-enabled-mutation scope.

Guard tests should continue to assert that `scripts/codex-task` and `aegis_foundation/cli.py` reconcile parsers reject mutation flags while allowing only read-only `--preview-candidates`; `aegis_mcp/server.py::aegis_reconcile` exposes `preview_candidates` but no mutation parameters; `scripts/_aegis_installer.py::reconcile` has no apply/status-writer parameters or Taskmaster write behavior; and writer functions such as `install`, `repair`, `start_local_work`, `kickoff`, `log_work`, `verify`, `closeout`, and `repair_handoff` do not reference or consume `mutation_candidate_preview` or the apply-path contract.

Contract-text tests should validate the first candidate boundary `merged_but_not_done` plus `git_ancestor`, excluded classes, exact allowed delta, explicit non-default external confirmation, apply-audit breadcrumbs, global kill-switch default-disabled behavior, Task 150 disabled scaffold guidance with intentionally unsatisfiable enable gate, and the Claude discussion prompt. Run `uv run python -m pytest tests/meta_workflow_guard/test_aegis_reconcile_apply_path_proposal_contract.py`, then run the existing reconcile guard suite covering side-effect oracle, precision corpus, rollback contract, preview contract, CLI parser, and MCP schema tests.
