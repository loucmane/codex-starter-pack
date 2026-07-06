# Task ID: 229

**Title:** Define PR-4 Replacement Parity Matrix

**Status:** done

**Dependencies:** 209 ✓, 228 ✓

**Priority:** medium

**Description:** Create a design-only Aegis parity matrix that proves every workflow surface Capsule PR-4 may demote or retire has an equal-or-better replacement in the capsule, ledger, and witness stack before any retirement work begins.

**Details:**

Deliver a committed documentation artifact, preferably `docs/aegis/pr-4-replacement-parity-matrix.md`, and do not implement any PR-4 retirement behavior in this task. Base the matrix on the current contracts in `docs/aegis/AEGIS_CAPSULE_SPEC.md` sections 5.1 and 5.2, `docs/aegis/LEDGER_SCHEMA.md`, `docs/aegis/capsule-boundary-dogfood-2026-07-06.md`, `docs/aegis/invocation-contract.md`, `docs/aegis/agent-adapter-contract.md`, `docs/aegis/state-recovery-model.md`, and existing runtime surfaces in `scripts/_aegis_installer.py`, `aegis_foundation/cli.py`, `.claude/scripts/*`, and `aegis_foundation/assets/.claude/scripts/*`.

For every old workflow surface PR-4 might demote or remove, add a row with these required columns: old surface, current job performed, current enforcement or advisory owner, replacement surface in the capsule/ledger/witness stack, proof required for equal-or-better behavior, dogfood evidence required, rollback path, retirement state (`keep`, `shadow`, `demote`, or `retire`), and explicit PR-4 go/no-go decision. Cover at minimum: `sessions/`, `sessions/current`, `sessions/state.json`, `plans/`, `plans/current`, `TRACKER.md`, `HANDOFF.md`, active/archive work-tracking folders under `docs/ai/work-tracking/`, `.aegis/state/pending-tracking.json`, `posttooluse-tracking.sh`, `tracking-stop-gate.sh`, closeout and handoff semantic gates, strict readiness/current-work blocks, kickoff and closeout commands, protected workflow path rules such as sessions/plans/work-tracking link protection, target-repo ceremony scaffolding, packaged workflow templates under `aegis_foundation/assets/templates/aegis/workflow/`, installed guidance/docs that still require ceremony, and doctor/repair behavior that reconstructs or validates old surfaces.

Map replacements to concrete shipped surfaces where possible: append-only ledger events and `ledger_lib.py` for passive evidence, `.aegis/capsule/current.md` and `.aegis/capsule/current.json` plus `aegis brief --status/--check/--inject` for orientation and recall, `aegis witness` and `.claude/scripts/witness_lib.py` for delivery-boundary proof, scope records for intent, gate registry verification events for proof at HEAD, and capsule freshness triggers from orientation, verification, pre-delivery, task-status-change, post-merge, risk-register-change, session-start, and session-resume boundaries. When a replacement is not yet proven, mark the retirement state `keep` or `shadow`, never `demote` or `retire`.

Add a hard-rule section stating that Capsule PR-4 must not remove, demote, stop validating, or stop rendering any existing workflow surface until this matrix proves the replacement covers the same function with equal or better reliability. Include a companion checklist for PR-4 reviewers: no code deletion without a matrix row, no row marked `retire` without proof and dogfood evidence, no target-repo ceremony removal without rollback steps, and no relaxing protected-path/readiness/closeout semantics unless witness/capsule/ledger evidence demonstrates equivalent boundary discipline.

Wire Taskmaster dependencies so the existing `Capsule PR-4: retirement (codex + companion target-repo PR)` task depends on this task before retirement work starts. Use Taskmaster commands rather than hand-editing `.taskmaster/tasks/tasks.json`; after adding the dependency, regenerate only affected task files with `python3 scripts/codex-task taskmaster generate-one --id 229` and `python3 scripts/codex-task taskmaster generate-one --id 210` or the equivalent repo-approved targeted refresh.

**Test Strategy:**

Add documentation/guard coverage, likely in a new `tests/meta_workflow_guard/test_aegis_pr4_replacement_parity_matrix.py`, that parses `docs/aegis/pr-4-replacement-parity-matrix.md` and asserts all required old surfaces are present; every row includes current job, replacement surface, proof, dogfood evidence, rollback path, retirement state, and go/no-go decision; retirement state values are limited to `keep`, `shadow`, `demote`, and `retire`; and no row marked `demote` or `retire` has placeholder or missing proof/dogfood/rollback text.

Add a guard assertion that the document contains the hard rule forbidding PR-4 removal or demotion before parity is proven, and that it explicitly says this task is design-only and must not implement PR-4 retirement. Verify Taskmaster wiring with `python3 scripts/codex-task taskmaster health` and by showing Task 210 depends on Task 229. Run the focused docs test, then final workflow checks: `python3 scripts/codex-task taskmaster health`, `python3 scripts/codex-task work-tracking audit`, `python3 scripts/codex-guard validate --include-untracked`, and `git diff --check`.
