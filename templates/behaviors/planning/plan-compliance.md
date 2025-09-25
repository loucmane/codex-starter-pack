---
trigger: Beginning any workflow or modifying tracked files
action: Validate active plan using standard template and guard checks
blocks: Cannot proceed with edits or guard validation failure until plan passes
category: planning
enforcement: mandatory
version: 1.0.0
---

# Plan Compliance Behavior

## Trigger Condition
This behavior fires whenever:
- A new workflow/session begins (after ULTRATHINK).
- The guard detects changes staged for commit.
- A plan amendment or continuation is declared.

## Required Actions
1. Load active plan (`plans/current`) generated from [Standard Plan Template](../../workflows/processes/plan-template.md).
2. Confirm mandatory steps exist:
   - `plan-step-scope` is completed after discussion with loucmane.
   - `plan-step-implement` lists concrete deliverables (files/tests).
   - `plan-step-verify` is pending until evidence captured.
3. Record evidence (session/tracker entries with S:W:H:E, command outputs stored under `reports/`).
4. If emergency bypass required:
   - Add `plan-step-emergency` with reason, approval, and remediation plan.
   - Create follow-up plan/post-mortem within 24 hours.
5. Await `codex-guard plan` validation before editing files.

## Blocking Gate
- No active plan symlink (`plans/current`) or missing mandatory steps.
- Scope step incomplete or missing approval note.
- Demand for emergency bypass without proper logging.
- Plan hash changed since last guard run without re-validation.

## Satisfaction Criteria
- Guard reports `PLAN_COMPLIANCE=PASS`.
- Tracker checklist updated for each plan step.
- Plan sync log updated (`.plan_state/sync.log`).
- Evidence references (commands/files/tests) recorded.

## Cross-References
- [Standard Plan Template](../../workflows/processes/plan-template.md)
- [`codex-guard` Plan Validation](../../metadata/workflow-guards.json)
- [Session Lifecycle Workflow](../../workflows/session/lifecycle.md)
- [Meta Workflow Authoring Draft](../../designs/meta-workflow-authoring-draft.md)
