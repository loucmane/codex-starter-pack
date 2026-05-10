# Task 48 Scope Reconciliation - Remaining Template and Backlog Alignment

## Purpose

Task 48 was written as a historical migration-phase task: "Execute Phase 2.3 Remaining Templates." The current repository has since gained the portable foundation, metadata policy, template registry, handler registry, bootstrap/adoption guidance, cross-project fixtures, Claude runtime adapter, targeted Taskmaster generation, direct Git execution mode, and multiple scanner/guard layers.

Task 48 must therefore not blindly migrate "remaining templates." Its first responsibility is to reconcile the old wording against the current foundation and identify the proven current-state gap.

## Evidence Reviewed

| Evidence | Finding |
| --- | --- |
| `task-master show 48` | Task 48 still asks for broad remaining-template migration, compatibility-map completion, and Phase 2 gate documentation. Subtask `48.1` is explicitly a scope reconciliation gate. |
| `templates/engine/core/portable-foundation-spec.md` | The foundation is now config-driven and portable across repository shapes. Remaining work should preserve that contract rather than add repo-specific migration branches. |
| `templates/engine/validation/foundation-adoption-guide.md` | Portable adoption already has a bootstrap path, validation checklist, and phased rollout model. Task 48 should not recreate adoption docs unless it finds a concrete mismatch. |
| `templates/handlers/index.md` | Task 26 completed the critical handler registry migration and compatibility aliases. Task 48 should use the registry as evidence, not rebuild it. |
| `.claude/engine/runtime-contract.md` | Tasks 103-107 established the Claude runtime adapter, smoke-tested it in the harness, and moved Codex to direct Git execution mode. Agent portability now belongs in a contract/follow-up layer, not ad hoc chat instructions. |
| Pending Taskmaster backlog | Remaining tasks still contain old phase names, broad automation/dashboard wording, and pre-portability assumptions. A backlog alignment pass is required before selecting implementation. |

## Original Detail Reconciliation

| Original Task 48 detail | Current state | Task 48 decision |
| --- | --- | --- |
| Identify remaining unmigrated templates | Template inventory and registry exist, but the remaining parent backlog still uses old migration-phase names. | Treat this as a backlog/template-scope audit first. Do not assume file migration remains. |
| Apply modular structure to each | Template modularization has largely happened through Tasks 90, 91, 26, and related metadata/registry tasks. | Only implement a file-level change if the audit finds a concrete unmigrated template family. |
| Update references and dependencies | Task 26 added handler index and compatibility aliases; Task 104 added targeted task-file generation. | Validate reference health as evidence, but avoid broad generated churn. |
| Validate with guard and scanner | Guard and scanner layers exist. | Required verification for Task 48, especially after Taskmaster updates. |
| Update compatibility map completely | Compatibility-map work is now split across template registry, handler index, metadata policy, and Taskmaster backlog alignment. | Document gaps; update compatibility files only if a missing live mapping is proven. |
| Prepare Phase 2 gate documentation | "Phase 2" is historical language. | Replace with current portable-foundation gate: backlog is aligned, portability direction recorded, agent-contract follow-up mapped. |

## Selected Current-State Gap

Task 48 should produce an evidence-backed alignment checkpoint:

1. Audit remaining pending Taskmaster tasks and classify them as current, stale, superseded, deferred, or needing re-scope.
2. Record the portability installer/adoption options and select the architecture direction.
3. Map agent runtime compatibility work onto existing Taskmaster tasks, especially Task 62, using Tasks 103-107 as completed evidence.
4. Update Taskmaster only after the audit shows which tasks require rewording or follow-up.

## Non-Goals

- Do not create a new parallel workflow engine.
- Do not rebuild the handler registry or template registry without a proven live gap.
- Do not introduce MCP as the sole installer path.
- Do not collapse old dashboard/governance tasks into implementation without checking whether they remain valuable.
- Do not mark broad phase tasks done merely because their names are stale.

## Acceptance Criteria

- `remaining-backlog-alignment-audit.md` classifies every pending parent Taskmaster task.
- `foundation-portability-options.md` documents installer/adoption options and the selected direction.
- `agent-runtime-contract-map.md` maps completed Claude work and future agent compatibility to Task 62 or follow-ups.
- `FINDINGS.md`, `DECISIONS.md`, `IMPLEMENTATION.md`, `TRACKER.md`, and the session log reference the scope decision.
- Taskmaster status for `48.1` is completed only after this scope gate is documented and plan sync passes.

## Progress Log

- **2026-05-10 16:00** — [S:20260510|W:task48-remaining-template-alignment|H:docs/design|E:docs/ai/work-tracking/active/20260510-task48-remaining-template-alignment-ACTIVE/designs/task48-scope-reconciliation.md] Reframed Task 48 from broad historical template migration to an evidence-backed backlog, portability, and agent-contract alignment checkpoint.
