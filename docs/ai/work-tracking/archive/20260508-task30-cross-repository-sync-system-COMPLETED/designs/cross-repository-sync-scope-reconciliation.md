# Task 30 Scope Reconciliation - Cross-Repository Sync System

## Purpose

Task 30 was written before the portable foundation existed. Its original wording asks for automated synchronization between legacy and Codex repositories, including daily diffs, automatic PRs, conflict queues, a dashboard, bidirectional sync, and audit logging.

That wording is now historical context. The current foundation already has several of the expected primitives:

- repo-local `[repo_structure]` configuration in `.codex/config.toml`
- portable bootstrap via `python3 scripts/codex-task bootstrap init`
- drift detection via `python3 scripts/codex-guard drift-check`
- metrics/report composition via `python3 scripts/codex-task report generate`
- cross-project fixture coverage for alternate repository shapes
- adoption guidance in `templates/engine/validation/foundation-adoption-guide.md`
- rollback and rehearsal planning helpers for non-destructive migration work

The Task 30 scope must therefore be the remaining current-state gap, not the old migration-phase automation idea.

## Evidence Reviewed

| Evidence | Finding |
| --- | --- |
| `.taskmaster/tasks/task_030.txt` | The original task still references auto PRs, bidirectional sync, manual conflict queues, and a dashboard. Subtask 30.1 requires scope reconciliation before implementation. |
| `templates/engine/core/portable-foundation-spec.md` | The foundation is config-driven; scripts should derive paths from repo-local roots and preserve lifecycle semantics across repositories. |
| `docs/ai/work-tracking/archive/20260430-task4-scanner-configuration-system-COMPLETED/designs/backlog-alignment-audit.md` | Task 30 is explicitly listed as a migration-phase task requiring evidence-driven reframing. |
| Task 95 drift design and implementation notes | `python3 scripts/codex-guard drift-check` already exists and reports deterministic template/canonical-doc/command-surface drift. |
| Task 98 repo-structure contract | Cross-project behavior must use `.codex/config.toml` roots instead of hardcoded local paths. |
| Task 100 bootstrap outline | New repositories can receive starter foundation assets without clobbering existing files. |
| Task 101 fixture matrix | Alternate repo shapes already prove bootstrap, guard, metrics, and drift path resolution follow configured roots. |
| Task 102 adoption guide | Existing repo adoption should be phased; optional layers such as drift reports and metrics should not block first adoption. |
| Task 23 rehearsal planner | Migration helpers should be non-destructive planners that produce reviewable evidence, not unreviewed mutation engines. |

## Original Detail Reconciliation

| Original detail | Current status | Task 30 decision |
| --- | --- | --- |
| Daily diff detection using git | Git snapshots and status capture exist in rollback/rehearsal helpers; drift-check covers configured template drift. | Use git/source snapshots as metadata in a sync plan, but do not add scheduled automation. |
| Drift scanner for template divergence | Implemented by Task 95 as `codex-guard drift-check`. | Reuse as an input/recommended verification command; do not build a second drift scanner. |
| Generate auto PRs for required fixes | Not present, and unsafe without target repo credentials, branch policy, reviewer policy, and conflict semantics. | Defer. Task 30 must not push, branch, or open PRs automatically. |
| Conflict resolution/manual review queue | Not present as a cross-repo artifact. | Implement a manual review queue inside the sync plan output. |
| Sync status dashboard | Metrics dashboard exists as an optional reporting layer. | Defer UI/dashboard work; Task 30 outputs machine-readable JSON and a markdown runbook. |
| Bidirectional sync for transition period | Unsafe for the portable foundation because it can overwrite repository-specific policy and structure. | Reject for current scope. Use reviewed one-way source-to-target planning only. |
| Sync audit logging | Work-tracking evidence and generated reports already provide task-local audit logs. | Implement explicit `executes_mutations: false` plan output and store evidence under this task. |

## Selected Current-State Gap

Implement a non-destructive cross-repository sync planner:

```bash
python3 scripts/codex-task sync plan \
  --source-dir <foundation-source> \
  --target-dir <target-repo> \
  --report-file <sync-plan.json> \
  --runbook-file <sync-runbook.md>
```

The helper should:

- compare a small, governed set of portable foundation assets between source and target repositories
- respect repo-local configuration where possible
- emit JSON for automation and markdown for human review
- classify assets as `identical`, `different`, `missing`, or `source-missing`
- produce a manual review queue with recommended copy/update/review actions
- include source and target git snapshots when available
- state `mode: non-destructive-cross-repo-sync-plan`
- state `executes_mutations: false`
- recommend existing verification commands such as bootstrap, drift-check, taskmaster health, guard, and diff-check

The helper must not:

- create branches
- commit or push
- open PRs
- overwrite files
- perform bidirectional sync
- run destructive Git commands
- replace `codex-guard drift-check`
- create a dashboard UI

## Initial Foundation Asset Set

The first implementation should compare only stable foundation assets that are already part of the portable contract:

| Asset | Rationale |
| --- | --- |
| `.codex/config.toml` | Repo-local structure and runtime settings source. |
| `templates/metadata/template-metadata-policy.json` | Repo-local metadata policy data used by drift checks. |
| `templates/engine/core/portable-foundation-spec.md` | Canonical portability contract. |
| `templates/engine/validation/foundation-adoption-guide.md` | Canonical rollout guide. |
| `scripts/_repo_structure.py` | Shared config loader used by foundation scripts. |
| `scripts/codex-guard` | Guard and drift enforcement entrypoint. |
| `scripts/codex-task` | Session/work-tracking/bootstrap/report helper entrypoint. |
| `scripts/template-metrics-dashboard` | Optional reporting layer that uses configured roots. |

This list is intentionally conservative. A future task can promote the list into a config file or registry once real cross-repo usage shows which assets should be copied, adapted, or ignored per project type.

## Implementation Boundary

Task 30 should add the sync planner to `scripts/codex-task`, focused unit tests in `tests/meta_workflow_guard/test_codex_task.py`, and task-local evidence under:

`docs/ai/work-tracking/active/20260508-task30-cross-repository-sync-system-ACTIVE/reports/cross-repository-sync-system/`

No template/runtime policy should change unless the implementation uncovers a direct mismatch. The planner should be a review artifact that supports portable adoption, not an autonomous sync service.

## Acceptance Criteria

- `python3 scripts/codex-task sync plan --source-dir . --target-dir .` produces a non-mutating JSON plan and markdown runbook.
- Unit tests prove missing and changed target assets become manual review queue entries.
- Unit tests prove the helper does not mutate source or target files.
- The selected scope is recorded in `FINDINGS.md`, `DECISIONS.md`, `IMPLEMENTATION.md`, `TRACKER.md`, and the session log.
- Taskmaster subtask `30.1` is marked done after this scope gate.
- Taskmaster subtask `30.2` is completed only after implementation, test evidence, guard evidence, work-tracking audit, plan sync, and Serena memory are complete.

## Progress Log

- **2026-05-08 12:46** — [S:20260508|W:task30-cross-repository-sync-system|H:docs/design|E:docs/ai/work-tracking/active/20260508-task30-cross-repository-sync-system-ACTIVE/designs/cross-repository-sync-scope-reconciliation.md] Reframed Task 30 from historical auto-sync wording to a non-destructive cross-repository sync planner grounded in the current portable foundation.
