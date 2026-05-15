# Task 78 Final Documentation Scope Reconciliation

## Taskmaster Source

Task 78 asks for a comprehensive final documentation set:

- architecture documentation;
- operation manual;
- API documentation;
- troubleshooting guide;
- disaster recovery plan;
- capacity planning guide;
- compliance documentation;
- handover documentation.

That wording comes from the historical migration plan. It is too broad to execute literally because the current repository already contains the portable foundation documentation, static report packets, operational runbooks, validation helpers, session/work-tracking lifecycle docs, and Claude runtime adapter docs.

## Current Evidence

| Historical category | Current evidence | Task 78 implication |
| --- | --- | --- |
| Architecture documentation | `templates/engine/README.md`, `templates/engine/core/portable-foundation-spec.md`, `templates/integration/architecture/system-architecture.md`, `templates/integration/architecture/template-architecture.md` | Architecture docs already exist; do not create a duplicate architecture suite. |
| Operation manual | `templates/guides/index.md`, `templates/TOOLS.md`, `templates/workflows/session/lifecycle.md`, `templates/workflows/taskmaster/work-tracking-enforcement.md`, `reports/operational-runbook/README.md` | Operations are covered by workflow docs plus static runbook packet generation. |
| API/command documentation | `templates/TOOLS.md`, `AGENTS.md`, `.claude/TM_COMMANDS_GUIDE.md`, `reports/README.md` | The current foundation exposes command helpers and adapters, not an application API needing generated OpenAPI output. |
| Troubleshooting guide | `templates/guides/troubleshooting/issues.md`, `templates/engine/debugging/system-debug.md`, `templates/matrices/recovery/error-to-recovery.md`, `templates/engine/enforcement/meta-workflow-guard-remediation.md` | Troubleshooting docs exist across user, engine, recovery, and guard-remediation layers. |
| Disaster recovery and rollback | `reports/operational-runbook/README.md`, `reports/cleanup-automation/README.md`, `templates/matrices/recovery/error-to-recovery.md`, `templates/engine/fallbacks/error-handling.md`, `templates/metadata/emergency-response-policy.json` | Recovery is repository-native and static; no external DR platform should be invented. |
| Capacity, performance, cost, maintenance | `reports/template-performance/README.md`, `reports/cost-tracking/README.md`, `reports/maintenance/README.md`, `reports/success-metrics/README.md` | Capacity-style evidence is represented by static performance, cost, maintenance, and success scorecards. |
| Compliance and validation | `templates/engine/validation/validation-framework.md`, `templates/engine/validation/foundation-adoption-guide.md`, `templates/engine/validation/ENFORCEMENT-SUMMARY.md`, `python3 scripts/codex-guard validate --include-untracked`, `python3 scripts/codex-task validation final-suite` | Compliance is guard/validation evidence, not an external compliance system. |
| Handover documentation | `templates/workflows/session/compaction.md`, `templates/workflows/session/continuation.md`, `templates/workflows/session/lifecycle.md`, active work-tracking `HANDOFF.md` files, session logs, Serena memories | Handover is already a workflow artifact; the gap is finding the correct handover references quickly. |
| Migration/adoption documentation | `templates/engine/validation/foundation-adoption-guide.md`, `templates/engine/core/portable-foundation-spec.md`, `templates/guides/quickstart/getting-started.md` | Migration/adoption docs already exist and should be referenced, not rewritten. |
| Training and communication | `templates/guides/training/foundation-onboarding.md`, `templates/guides/communication/foundation-communication-templates.md`, `reports/knowledge-transfer-process/README.md` | Training and communication surfaces exist as repo-native guidance and static packets. |

## Proven Gap

The documentation is present but scattered. There is no single permanent map that answers:

1. which existing document satisfies each historical "final documentation" category;
2. which report packet or command refreshes the evidence for that category;
3. which historical requirements are intentionally out of scope for the portable foundation;
4. where a maintainer should start when handing the repository to another operator.

Without that map, Task 78 would either duplicate stable documentation or rely on the current agent remembering where the existing documentation lives.

## Selected Implementation Boundary

Task 78 should implement only the discoverability layer:

- add `templates/guides/reference/final-documentation-map.md` as the canonical final-documentation map;
- link that map from `templates/guides/index.md`;
- keep existing documentation canonical instead of rewriting it;
- capture evidence that the map exists, covers the historical categories, passes guard, and is referenced by the guide hub;
- keep the map honest about static, repo-native evidence boundaries.

## Explicit Non-Goals

- Do not generate a parallel architecture, operations, API, troubleshooting, disaster recovery, capacity, compliance, or handover documentation suite.
- Do not claim hosted documentation publication, external training delivery, external compliance certification, live monitoring, schedulers, dashboards, notifications, calendars, ticketing, BI systems, or incident-management integrations.
- Do not modify guard behavior, Claude runtime hooks, Taskmaster graph semantics, or report generators.
- Do not mark stale historical requirements as completed by creating empty placeholder docs.

## Acceptance Criteria

- This scope artifact is recorded and referenced from tracker/session updates.
- Taskmaster subtask `78.1` is marked done after the scope decision is captured.
- A permanent final-documentation map exists under `templates/guides/reference/`.
- The guide hub links to the final-documentation map.
- Verification captures:
  - documentation static checks for the map and guide hub link;
  - focused tests or guard checks relevant to the changed files;
  - plan sync;
  - work-tracking audit;
  - Taskmaster health;
  - guard;
  - diff-check.

## S:W:H:E

- **2026-05-15 11:15 CEST** - [S:20260515|W:task78-final-documentation|H:scope-reconciliation|E:docs/ai/work-tracking/active/20260515-task78-final-documentation-ACTIVE/designs/final-documentation-scope-reconciliation.md] Reconciled Task 78 from broad historical "final docs" wording to a narrow final-documentation map over existing portable foundation evidence.
