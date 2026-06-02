# Task ID: 150

**Title:** Add Disabled Reconcile Apply Scaffold with Approved-Context Gate

**Status:** done

**Dependencies:** 149 ✓

**Priority:** medium

**Description:** Create a medium/high-priority Aegis implementation task for a disabled reconcile apply orchestration scaffold that cannot mutate under any current input. The scaffold must add safety primitives for future apply work while staying separate from read-only reconcile and unreachable from governed-agent CLI, MCP, and codex-task surfaces.

**Details:**

Build this as a disabled, fail-closed scaffold in the existing Python Aegis stack without adding any enabled mutation path. Keep read-only reconcile unchanged in `scripts/_aegis_installer.py::reconcile`, `format_reconcile_summary`, `aegis_foundation/cli.py::handle_reconcile`, `scripts/codex-task` `aegis reconcile`, and `aegis_mcp/server.py::aegis_reconcile`; do not add `--apply`, `--auto`, `--fix`, status-setting flags, MCP apply parameters, Taskmaster writes, git/PR writes, closeout writes, or workflow-state writes.

Implement a separate internal scaffold module or clearly isolated helper area, for example `aegis_foundation/reconcile_apply_scaffold.py` or a private section in `scripts/_aegis_installer.py`, but do not expose it through package CLI, MCP tools, or `scripts/codex-task`. The scaffold should define three safety primitives only:

1. Approved-context proof gate: require a positive proof object rather than denylist-based agent detection. Model acceptable future contexts as post-merge CI proof or operator-controlled proof outside the governed agent, but make the current implementation intentionally unsatisfiable. Every current flag, environment variable, runtime string, and supplied context must return disabled/refused. Default to deny when proof is absent, malformed, unknown, stale, or not bound to the requested task/proof.

2. Apply-audit transaction record model: define structured records for before/after phases with required fields for phase, task id, finding kind, proof artifact, allowed-delta before/after hashes using the Task 145 oracle concepts from `tests/meta_workflow_guard/reconcile_side_effect_oracle.py`, approved-context proof id, authorization binding to task id plus proof, rollback handle reference, `rolled_back`, eligibility/corpus version, idempotency key, hash-chain fields, and external-anchor fields. This task should validate and serialize model data but must not write real mutation state or audit breadcrumbs to governed workflow surfaces.

3. Kill-switch semantics: implement global plus per-class kill-switch evaluation that is default-disabled and fail-closed on absent, missing, unreadable, or corrupt state. Explicit disable must override every enable/proof/confirmation path. Disable may be requested by any actor. Enable must require approved non-agent context and must remain impossible in this scaffold. Cover the first future class from Task 149, `merged_but_not_done` with `git_ancestor`, while keeping all other reconcile classes ineligible.

Wire these primitives into a disabled reconcile apply orchestrator that accepts a candidate-shaped input and returns a refusal/audit-preview result without mutating. It may reuse inert candidate concepts from `docs/aegis/reconcile-mutation-candidate-preview-contract.md` and the Task 146 precision corpus helpers, but no writer function may consume `mutation_candidate_preview`. Include or update contract documentation, likely under `docs/aegis/reconcile-disabled-apply-scaffold-contract.md`, explicitly stating the scaffold is not reachable from governed-agent surfaces and cannot currently be enabled.

**Test Strategy:**

Add focused pytest coverage, preferably `tests/meta_workflow_guard/test_aegis_reconcile_disabled_apply_scaffold.py`, plus any small model/unit tests needed for the new helper module.

Required acceptance tests:

- Zero side effects: run the disabled scaffold across the existing reconcile fixture matrix from `tests/meta_workflow_guard/test_aegis_installer.py` and/or `tests/meta_workflow_guard/reconcile_precision_corpus.py`, wrapping each run with `snapshot_whole_tree` from `tests/meta_workflow_guard/reconcile_side_effect_oracle.py`, and assert no filesystem or git-control-plane deltas anywhere.
- Unsatisfiable enable: prove no combination of explicit flags, environment variables, supplied context names, proof objects, confirmations, or future-looking config can make the scaffold mutate or report enabled.
- Agent-surface unreachability: assert `scripts/codex-task` `aegis reconcile` parser still only exposes read-only reconcile options such as `--preview-candidates`, package CLI `reconcile` still rejects mutation flags, `aegis_mcp/server.py` `aegis.reconcile` schema has no apply/mutate/status parameters, and no agent-facing codex-task path calls the new scaffold.
- Kill switches: cover absent state, missing file/path, unreadable state, corrupt state, explicit global disable, explicit per-class disable, and disable precedence over any enable/proof/confirmation input.
- Audit model: validate required before/after fields, task-id plus proof authorization binding, allowed-delta before/after hash binding, idempotency key stability, rollback handle reference, `rolled_back` field validation, eligibility/corpus version, and hash-chain/external-anchor fields without writing real mutation state.

Run focused tests with `uv run python -m pytest tests/meta_workflow_guard/test_aegis_reconcile_disabled_apply_scaffold.py` and include existing guard coverage for reconcile surfaces, such as `uv run python -m pytest tests/meta_workflow_guard/test_aegis_installer.py tests/meta_workflow_guard/test_aegis_mcp_server.py tests/meta_workflow_guard/test_aegis_reconcile_apply_path_proposal_contract.py`.
