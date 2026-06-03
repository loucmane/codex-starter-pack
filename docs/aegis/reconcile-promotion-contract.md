# Aegis Reconcile Promotion Contract

**Status:** active contract for Tasks 144-150.
**Scope:** `aegis reconcile` remains a read-only drift report. This document defines the
minimum bar for any separate future task that proposes reconcile-driven mutation.

## Current Contract

The reconcile surfaces are report-only:

- `python3 scripts/codex-task aegis reconcile`
- `aegis_foundation/cli.py` package command `aegis reconcile`
- `scripts/_aegis_installer.py::reconcile`
- MCP tool `aegis.reconcile`

Those surfaces must not mutate Taskmaster status, Aegis workflow state, git refs, PR
state, closeout artifacts, generated task stubs, or work-tracking files. The command may
inspect git, Taskmaster, Aegis state, and optional GitHub PR metadata, then emit a report.
It must not implement hidden status-setting paths, closeout automation, git write
commands, PR writes, or Taskmaster mutation.

Task 143 captured the promotion evidence that justifies keeping this line in place:
`docs/ai/work-tracking/archive/20260602-task143-reconcile-promotion-criteria-COMPLETED/reports/reconcile-promotion-criteria/promotion-criteria-summary.md`.
That dogfood pass proved the report is useful for finding drift, but it also showed that
some findings are intentionally ambiguous and should not be auto-resolved.

## Mutation Is A Separate Task

Any future reconcile auto-mutation mode must be implemented as a separate Taskmaster task
and branch. It cannot be introduced by adding casual flags to the current read-only
surfaces.

The existing CLI and MCP contracts intentionally exclude mutating flags and parameters such
as:

- `--apply`
- `--auto`
- `--auto-fix`
- `--fix`
- `--set-status`
- `--status`
- `--done`
- `--closeout`
- `--mutate`
- `--write`
- `--push`

Tests must fail if those options appear on reconcile before the separate mutation task
defines and verifies the required safety model.

## Promotion Criteria

A future mutation mode must prove all of the following before it can move past report-only:

- **Operator confirmation:** every proposed mutation is shown to the operator with the
  target task, proof source, current state, proposed state, and affected files. The
  operator must explicitly confirm the action.
- **Audit breadcrumb:** every proposed mutation records an audit event before execution and
  a result event after execution. The record must include tool, handler, task id, proof,
  changed paths, timestamp, and outcome.
- **Rollback evidence:** every mutation has either a reversible operation plan or a
  captured before/after artifact that can restore the previous state.
- **High-confidence proof:** each mutation class has a positive proof requirement. Examples
  include `git_ancestor` for merged branches and GitHub `MERGED` PR metadata for squash
  merges. Absence of proof is not proof of drift.
- **Manual-only finding classes:** ambiguous findings remain report-only unless a later
  task proves a narrower safe rule.
- **No closeout shortcut:** reconcile cannot mark Aegis closeout complete. Closeout remains
  governed by its own scope, evidence, verification, and handoff gates.
- **No git or PR writes by default:** pushing, deleting branches, editing PRs, or changing
  refs must be separately confirmed and audited.

## Manual-Only Findings

These finding kinds stay manual-only under the current contract:

- `multi_pr_epic_ambiguity`
- `abandoned_in_progress_branch`
- `stale_local_stub`
- `local_ad_hoc_stub`
- squash/offline unknown merge truth, including `git_only_non_ancestor_or_missing_base`

These cases are valuable as report output because they tell an operator where to inspect.
They are not safe automatic mutation targets.

## Test Gate

Task 144 encodes the contract in tests:

- CLI parser tests reject reconcile mutation flags in both `scripts/codex-task` and the
  packaged `aegis_foundation` CLI.
- MCP schema tests assert `aegis.reconcile` exposes only `target_dir`, `base_ref`, and
  `use_github`.
- MCP execution tests assert the tool response and core result are marked `read_only=True`.
- Reconcile smoke checks compare git status before and after execution to guard the
  report-only behavior.

Task 145 strengthens the behavioral side-effect proof:

- `tests/meta_workflow_guard/reconcile_side_effect_oracle.py` snapshots path existence,
  path type, mode, symlink target, regular-file content hash, and recursive membership.
- `tests/meta_workflow_guard/test_reconcile_side_effect_oracle.py` proves the oracle catches
  content edits, creation, deletion, mode changes, symlink target changes, type swaps,
  missing-path creation, and unauthorized deltas while allowing only exact declared output
  paths.
- Whole-tree isolated fixture checks in `tests/meta_workflow_guard/test_aegis_installer.py`
  assert reconcile changes nothing anywhere in the temp fixture, aside from narrowly
  tolerated git discovery churn such as `.git/FETCH_HEAD` and `.git/logs/**`.
- Focused control-plane checks cover larger-repo surfaces where whole-tree snapshots are
  noisy: `.aegis/**`, `.taskmaster/**`, `docs/ai/work-tracking/**`, `sessions/**`,
  `plans/**`, `.git/HEAD`, `.git/refs/**`, and `.git/packed-refs`.

Task 146 adds the precision and boundary-leakage gate:

- `docs/aegis/reconcile-precision-corpus.md` defines the pre-registered auto-eligible
  proof classes and manual-only classes.
- `tests/meta_workflow_guard/reconcile_precision_corpus.py` normalizes observed reconcile
  findings and fails on unlabelled findings, false positives, non-finding proof drift, or
  auto/manual boundary leaks.
- `tests/meta_workflow_guard/test_aegis_reconcile_precision_corpus.py` rebuilds the
  labeled fixture corpus and recomputes precision from real reconcile execution rather than
  relying on prose-only labels.

Task 147 adds the first rollback and blast-radius proposal contract, still without
promoting reconcile into mutation:

- `docs/aegis/reconcile-mutation-rollback-contract.md` defines the only first candidate as
  `merged_but_not_done` with `git_ancestor` proof, subject to Task 146 precision plus
  explicit operator confirmation.
- `tests/meta_workflow_guard/reconcile_mutation_rollback_contract.py` models the proposal,
  audit breadcrumb, exact blast-radius, and rollback handle as test-only contract data. It
  does not import or change reconcile implementation behavior.
- `tests/meta_workflow_guard/test_aegis_reconcile_mutation_rollback_contract.py` proves
  non-first auto classes and manual-only classes cannot enter the first proposal set,
  confirmation and before/after audit breadcrumbs are mandatory, the real Taskmaster done
  cascade has an exact registered path inventory, unregistered path deltas fail, and
  rollback restores the registered paths.

Task 148 adds the inert, opt-in candidate preview contract:

- `docs/aegis/reconcile-mutation-candidate-preview-contract.md` defines preview data as an
  operator-facing read-only surface, not an execution API for agents.
- Default reconcile output remains observational; `mutation_candidate_preview` appears only
  when explicitly requested.
- Candidate preview admits only `merged_but_not_done` with `git_ancestor` proof and carries
  `executable=false`, `apply_path_exists=false`, and
  `blocked_reason="report-only per Task 147 contract"`.
- No-consumer tests assert writer functions do not read preview data to drive mutation, and
  installed gate coverage asserts out-of-band Taskmaster completion for a non-active
  previewed task remains blocked.

Task 149 defines the first apply-path proposal contract without enabling mutation:

- `docs/aegis/reconcile-apply-path-proposal-contract.md` defines the first future apply
  boundary as `merged_but_not_done` with `git_ancestor` proof only.
- The contract is design-only: no `--apply` flag, no writer path, and no default preview
  behavior are added.
- The future implementation bar explicitly requires the Task 144 promotion contract, Task
  145 side-effect oracle, Task 146 precision corpus, Task 147 rollback contract, and Task
  148 inert preview contract before any write can exist.
- The contract embeds a Claude discussion prompt so external review happens before any
  operator-confirmed execution path is implemented.

Task 150 adds a disabled scaffold, still without enabling mutation:

- `docs/aegis/reconcile-disabled-apply-scaffold-contract.md` defines the disabled scaffold
  contract.
- `aegis_foundation/reconcile_apply_scaffold.py` models positive approved-context proof,
  apply-audit transaction records, kill-switch evaluation, and an always-refusing
  orchestrator.
- The scaffold remains unreachable from governed-agent surfaces: no reconcile mutation
  flag, no MCP apply tool, no Codex helper apply path, and no writer consuming preview
  data.
- Tests prove the scaffold has zero filesystem side effects across the reconcile corpus and
  that the enable gate is unsatisfiable under current inputs.

Task 151 adds shadow apply artifacts, still without enabling mutation:

- `docs/aegis/reconcile-shadow-apply-contract.md` defines shadow-mode evidence for the
  first candidate class.
- `aegis_foundation/reconcile_shadow_apply.py` builds would-apply artifacts for
  `merged_but_not_done` with `git_ancestor` proof only.
- The shadow path validates predicted Taskmaster blast radius in a detached sacrificial
  clone and records actual deltas without mutating the governed repo.
- CI mode returns artifact-ready JSON and the CI workflow captures a real GitHub Actions
  context proof artifact; local/test mode may write exactly one declared report path.
- Tests prove shadow mode has no live side effects, no agent-facing apply surface, no
  executable command strings, and no writer consumption.

The intended sequence is observe, prove, then automate. Task 141 added the report. Task 143
dogfooded its signal quality. Task 144 prevents accidental promotion to mutation flags.
Task 145 proves read-only behavior at the filesystem side-effect boundary. Task 146 proves
the auto/manual boundary stays precise. Task 147 defines the rollback and blast-radius
proposal bar for the first possible mutation candidate while keeping reconcile itself
strictly report-only. Task 148 makes the first candidate visible only as inert, opt-in
preview data. Task 149 writes the apply-path proposal contract and review prompt while
still keeping reconcile read-only. Task 150 adds the disabled, behaviorally zero-side-effect
scaffold that can be reviewed before any future enable path exists. Task 151 runs the
future apply pipeline in shadow mode with prediction-validated would-apply artifacts while
the final write remains absent.
