---
id: final-documentation-map
type: user-guide
status: stable
audience: maintainers
skill-level: intermediate
title: Final Documentation Map
description: Canonical map from historical final-documentation categories to current portable foundation docs and evidence
dependencies:
  - templates/guides/index.md
  - templates/engine/core/portable-foundation-spec.md
  - templates/engine/validation/foundation-adoption-guide.md
  - reports/README.md
---

# Final Documentation Map

Use this map when a reviewer asks for "final documentation" for the portable Codex foundation. It points to the current canonical docs and evidence refresh commands instead of creating duplicate docs for each historical category.

The foundation is repository-native and file-backed. It does not claim hosted documentation, external training delivery, live dashboards, notification systems, external compliance certification, or external incident-management integrations unless a later task explicitly implements those systems.

## Start Here

| Need | Canonical entry point |
| --- | --- |
| Understand the whole foundation | [Guide hub](../index.md) |
| Understand the portable workflow contract | [Portable foundation specification](../../engine/core/portable-foundation-spec.md) |
| Adopt the foundation in another repository | [Foundation adoption guide](../../engine/validation/foundation-adoption-guide.md) |
| Find command and tool routing | [Tools guide](../../TOOLS.md) |
| Review static report packet commands | `reports/README.md` |
| Review Claude runtime boundaries | `.claude/engine/runtime-contract.md` |

## Category Map

| Historical final-doc category | Canonical current docs | Evidence refresh / verification | Boundary |
| --- | --- | --- | --- |
| Architecture documentation | [Engine README](../../engine/README.md), [portable foundation specification](../../engine/core/portable-foundation-spec.md), [system architecture](../../integration/architecture/system-architecture.md), [template architecture](../../integration/architecture/template-architecture.md) | `templates/engine/verify-phase1.sh`; `python3 scripts/codex-guard validate --include-untracked` | Do not create a second architecture tree unless the current engine or integration architecture changes. |
| Operation manual | [Guide hub](../index.md), [common workflows](../workflows/common.md), [session lifecycle](../../workflows/session/lifecycle.md), [work-tracking enforcement](../../workflows/taskmaster/work-tracking-enforcement.md), `reports/operational-runbook/README.md` | `python3 scripts/codex-task operations runbook --label <label> --report-file <runbook.json> --runbook-file <runbook.md>` | Operational guidance is static and file-backed; it does not install schedulers, send notifications, deploy code, or execute rollback. |
| API and command documentation | [Tools guide](../../TOOLS.md), `AGENTS.md`, `.claude/TM_COMMANDS_GUIDE.md`, `reports/README.md` | `python3 scripts/codex-task taskmaster health`; `task-master --help`; command-specific `--help` where available | This repository exposes CLI/helper contracts and adapter commands, not an application API requiring generated OpenAPI output. |
| Troubleshooting guide | [Troubleshooting issues](../troubleshooting/issues.md), [system debug](../../engine/debugging/system-debug.md), [error-to-recovery matrix](../../matrices/recovery/error-to-recovery.md), [guard remediation](../../engine/enforcement/meta-workflow-guard-remediation.md) | `python3 scripts/codex-task work-tracking audit`; `python3 scripts/codex-guard validate --include-untracked`; `git diff --check` | Troubleshooting should repair workflow state and evidence; do not bypass guard or rewrite history. |
| Disaster recovery and rollback | `reports/operational-runbook/README.md`, `reports/cleanup-automation/README.md`, [error-to-recovery matrix](../../matrices/recovery/error-to-recovery.md), [error handling fallback](../../engine/fallbacks/error-handling.md), [emergency response policy](../../metadata/emergency-response-policy.json) | `python3 scripts/codex-task operations runbook --label <label> --report-file <runbook.json> --runbook-file <runbook.md>`; `python3 scripts/codex-task cleanup plan --label <label> --dry-run` | Recovery planning is explicit and non-destructive by default; no external incident platform is implied. |
| Capacity, performance, cost, and maintenance | `reports/template-performance/README.md`, `reports/cost-tracking/README.md`, `reports/maintenance/README.md`, `reports/success-metrics/README.md` | `python3 scripts/codex-task report generate --kind telemetry --strict-drift --strict-monitoring --strict-phase0 --strict-performance --strict-cost --strict-migration-health`; `python3 scripts/codex-task maintenance plan --report-file <maintenance.json> --runbook-file <maintenance.md>` | These packets are static evidence, not live observability, billing, capacity, or scheduler services. |
| Compliance and validation documentation | [Validation framework](../../engine/validation/validation-framework.md), [foundation adoption guide](../../engine/validation/foundation-adoption-guide.md), [enforcement summary](../../engine/validation/ENFORCEMENT-SUMMARY.md), [evidence claims behavior](../../behaviors/validation/evidence-claims.md) | `python3 scripts/codex-task validation final-suite --execute --report-dir reports/final-validation-suite`; `python3 scripts/codex-guard validate --include-untracked`; `python3 scripts/codex-task taskmaster health` | Validation evidence supports repository workflow compliance; it is not an external legal or regulatory certification. |
| Handover and continuation documentation | [Session lifecycle](../../workflows/session/lifecycle.md), [session continuation](../../workflows/session/continuation.md), [compaction protocol](../../workflows/session/compaction.md), [work-tracking enforcement](../../workflows/taskmaster/work-tracking-enforcement.md), active task `HANDOFF.md` files | `python3 scripts/codex-task plan sync`; `python3 scripts/codex-task work-tracking audit`; task-local guard/test evidence | Handover state lives in the active session, plan, tracker, handoff, Taskmaster status, and optional Serena memory. |
| Migration and adoption documentation | [Foundation adoption guide](../../engine/validation/foundation-adoption-guide.md), [portable foundation specification](../../engine/core/portable-foundation-spec.md), [getting started guide](../quickstart/getting-started.md), [foundation onboarding](../training/foundation-onboarding.md) | `python3 scripts/codex-task foundation bootstrap --help`; `python3 scripts/codex-task validation final-suite --dry-run` | Adoption is portable and repository-scoped; do not hardcode project-specific roots unless the repo-structure config requires them. |
| Training, communication, and knowledge transfer | [Foundation onboarding training](../training/foundation-onboarding.md), [communication templates](../communication/foundation-communication-templates.md), `reports/knowledge-transfer-process/README.md`, `reports/stakeholder-reporting/README.md` | `python3 scripts/codex-task knowledge transfer-review --report-file <knowledge.json> --runbook-file <knowledge.md>`; `python3 scripts/codex-task stakeholder report --report-file <stakeholder.json> --runbook-file <stakeholder.md>` | Training and communication are repo-native prompts and static packets; no LMS, meeting scheduler, survey platform, or notification system is implied. |

## Final Review Checklist

Before claiming final documentation is current:

1. Confirm the guide hub points to this map.
2. Confirm each historical category above has a current canonical doc and an evidence refresh path.
3. Run task-local plan sync, work-tracking audit, Taskmaster health, guard, and diff-check.
4. Store verification logs in the active work-tracking `reports/` folder.
5. Update the active tracker and handoff with exact evidence paths.

## Progress Log

- **2026-05-15 11:15 CEST** — [S:20260515|W:task78-final-documentation|H:templates/guides/reference/final-documentation-map.md|E:docs/ai/work-tracking/active/20260515-task78-final-documentation-ACTIVE/designs/final-documentation-scope-reconciliation.md] Added the canonical final-documentation map over existing architecture, operations, command, troubleshooting, recovery, capacity, compliance, handover, migration, training, and communication docs.
