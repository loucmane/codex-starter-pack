# Aegis State Recovery Model

This document defines the recovery and idempotency contract for Aegis-installed projects.
It complements the invocation contract, update/rollback guide, and public adoption flow.

## Design Goals

- Diagnostics are read-only by default.
- Repairs are explicit, reviewed, and narrowly scoped.
- Re-running a command should not duplicate workflow state.
- Completed closeout state is terminal evidence, not a readiness failure.
- Taskmaster and Serena remain optional integrations unless current work explicitly marks them required.
- Aegis-owned state is recoverable without overwriting divergent project-owned files.

## State Classes

| State | Meaning | Typical Next Action |
|---|---|---|
| `not_installed` | No valid `.aegis/foundation-manifest.json` is present. | Run `aegis init` or review `aegis plan-install`. |
| `invalid_manifest` | A manifest exists but cannot be parsed or validated against the installed schema. | Review manifest drift; repair only if the manifest can be restored from managed evidence. |
| `installed_no_current_work` | Runtime files are installed, but `.aegis/state/current-work.json` is absent. | Start local work with `aegis start "<title>"` or explicit-id work with `aegis kickoff`. |
| `in_progress_ready` | Current work exists, branch/session/plan/work-tracking state is aligned, and readiness passes. | Continue normal implementation or verification. |
| `workflow_scaffold_incomplete` | Current work exists, but required pointers, directories, or workflow surfaces are missing. | Run `aegis doctor`, then `aegis repair --apply` only for safe mechanical fixes. |
| `pending_tracking` | `.aegis/state/pending-tracking.json` contains one or more unlogged mutation events. | Run `aegis log --pending-id current ...`; repair must not clear these events. |
| `strict_verification_required` | Work exists and tracking is clean, but strict verification evidence is absent or failing. | Run `aegis verify --strict`, then log the verification report. |
| `closeout_required` | Strict verification passes, but final closeout has not completed. | Run `aegis closeout --dry-run --update-handoff`, repair reported gaps, then final closeout. |
| `completed_closeout` | Current work and closeout report prove the task was closed out successfully. | Report completion or start new work. Repeated closeout checks should pass from completed state. |
| `stale_or_broken_pointers` | Symlinks, active folders, or reports reference stale or missing targets. | Repair only mechanically derivable pointers; report ambiguous or stale folders for manual review. |

## Command Idempotency

| Command | Re-run Contract |
|---|---|
| `aegis inspect` | Read-only; no target files change. |
| `aegis status` | Read-only; reports installation and update state. |
| `aegis next` | Read-only; recommends the next workflow action. |
| `aegis plan-install` | Read-only; may write no target files and should be stable for unchanged inputs. |
| `aegis init` / `aegis install --apply` | Safe to repeat. Existing user content is preserved, managed content is updated only through reviewed installer rules, and backup sidecars are not created. |
| `aegis start "<title>"` | If no current work exists, allocate one local task id and scaffold work. If matching in-progress work already exists, return an already-started/no-op result. If different work is in progress, refuse with next action. If previous work is completed, allow new work. |
| `aegis kickoff --task ...` | Same replay behavior as `start`, but keyed by explicit external numeric task id. |
| `aegis log` | Replaying an already-recorded pending event should avoid duplicate S:W:H:E entries and duplicate plan evidence. A mismatched pending event should still be refused. |
| `aegis verify` | Safe to repeat. It may refresh `.aegis/reports/verification-report.json`, but should not create ambiguous pending tracking or duplicate manifest report records. |
| `aegis closeout_ready` / `aegis closeout --dry-run` | Read-only closeout preflight. Repeated runs after completion pass from completed closeout state. |
| `aegis closeout --update-handoff` | Final closeout writes the closeout report and marks current work completed. Replaying after completed closeout should pass without reverting work to in-progress or churning state unless an explicit refresh mode exists. |
| `aegis doctor` | Read-only diagnostic. It produces checks, current-state classification, repair plan, and next action. |
| `aegis repair` | Dry-run by default and read-only. `--apply` executes only safe deterministic repair actions and writes `.aegis/reports/repair-report.json`. |

## Doctor Contract

`aegis doctor` is the canonical diagnostic surface for recovery. It should return a structured report with:

- `schema_version`
- `target_root`
- `read_only: true`
- `checked_at`
- `status`
- `summary`
- `current_state`
- `checks`
- `repair_plan`
- `next_action`

Doctor checks should cover:

- manifest presence, parseability, schema version, and foundation/installer metadata
- managed Aegis file presence without overwriting user files
- project-local CLI shim existence and executable bit
- installed workflow templates
- current work shape and status
- branch, session, plan, work-tracking, and report path consistency
- `sessions/current` and `plans/current` pointer health
- active work-tracking surfaces: tracker, findings, decisions, implementation, changelog, handoff, designs, and reports
- pending tracking queue
- latest verification and closeout report state
- optional integration state for Taskmaster and Serena
- stale active folders that are not referenced by current work

Doctor may produce warnings and manual-review items. It must not mutate files, even when a safe repair is obvious.

## Repair Contract

`aegis repair` consumes the doctor model. Without `--apply`, it is a read-only preview. With `--apply`, it may perform only deterministic low-risk actions:

- recreate `sessions/current` and `plans/current` from `.aegis/state/current-work.json`
- recreate expected empty directories such as the active report directory
- restore missing Aegis-managed runtime files from packaged/source assets when the file is absent and managed ownership is known
- fix executable bits on managed scripts
- normalize completed closeout metadata when current work and `.aegis/reports/closeout-report.json` already prove passed closeout

Repair must not:

- overwrite divergent user files
- edit source files
- clear non-empty pending tracking
- delete or archive stale active folders by default
- invent task ids
- create new current work
- weaken readiness, tracking, verification, or closeout gates

Mutating repair writes `.aegis/reports/repair-report.json` with applied actions, skipped actions, manual-review items, and verification guidance.

## Optional Integration Policy

Taskmaster and Serena are optional Aegis integrations. Absence is healthy when:

- `.aegis/state/current-work.json` marks the integration as `required: false`, or
- current work is absent and the project has no explicit integration requirement.

Absence is a failure only when current work marks the integration required. Doctor and closeout should provide actionable guidance rather than silently enabling or disabling those integrations.

## Recovery Philosophy

Aegis should prefer explicit state transitions over hidden correction. The right behavior is:

1. Diagnose drift with `aegis doctor`.
2. Present safe and unsafe repair categories.
3. Apply only reviewed safe repair actions with `aegis repair --apply`.
4. Require normal verification/closeout gates after repair.

The system becomes reliable when every command can be repeated after cancellation, overload, or user interruption and either returns an already-applied result, performs the same deterministic write, or refuses with a concrete next action.
