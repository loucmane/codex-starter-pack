
> **Codex Equivalent:** References to Claude's TodoWrite/TodoRead should be handled in Codex by updating the plan tool (Plan update ≈ TodoWrite, Plan display ≈ TodoRead) alongside the work-tracking checklists.
# Codex Migration SSOT Tracker

**Started**: 2025-09-20
**Status**: ACTIVE
**Last Updated**: 2025-09-20

## Goals
- [x] Establish Codex work-tracking + session scaffolding
- [x] Re-run SSOT scanner suite inside Codex repo
- [ ] Review scanner outputs and map required fixes
- [x] Document Serena/MCP integration updates in templates
- [ ] Prepare next actions for modularization cleanup
- [x] Implement `codex-task` helper + diff-aware guard

## Plan Compliance Phase 1 Checklist
- [x] plan-step-scope — Scope confirmed with loucmane for guard + plan enforcement work (2025-09-25 18:47 CEST)
- [x] plan-step-implement — Guard enhancements delivered, meta workflow workflow created, sync log refreshed (2025-09-25 20:33 CEST)
- [x] plan-step-verify — Guard/test evidence logged, Serena memory written, backlog staged for Taskmaster (2025-09-25 21:22 CEST)
- [ ] plan-step-emergency — Not applicable unless emergency bypass triggered

## Progress Log
- **2025-09-25 16:37** — Plan compliance Phase 1 resumed (new session established).
  `date "+%Y-%m-%d %H:%M %Z"` => `2025-09-25 16:37 CEST` (previous session start corrected for actual local time)
- **2025-09-25 18:48**
  `date "+%Y-%m-%d %H:%M %Z"` => `2025-09-25 18:48 CEST` — [S:20250925|W:plan-compliance-phase1|H:plans/2025-09-25-plan-compliance-phase1.md|E:files`plans/2025-09-25-plan-compliance-phase1.md`] Created active plan file and pointed `plans/current` symlink to it.
- **2025-09-25 19:00**
  `date "+%Y-%m-%d %H:%M %Z"` => `2025-09-25 19:00 CEST` — [S:20250925|W:plan-compliance-phase1|H:.plan_state/sync.log|E:files`.plan_state/sync.log`] Recorded initial plan/tracker sync entry (hash + timestamp) for guard validation.
- **2025-09-25 19:03**
  `date "+%Y-%m-%d %H:%M %Z"` => `2025-09-25 19:03 CEST` — [S:20250925|W:plan-compliance-phase1|H:scripts/codex-guard|E:files`reports/plan-compliance-phase1/guard-20250925-1849.txt`] Ran guard with new plan checks (flagging missing meta workflow template; remediation queued).
- **2025-09-25 20:30**
  `date "+%Y-%m-%d %H:%M %Z"` => `2025-09-25 20:30 CEST` — [S:20250925|W:plan-compliance-phase1|H:templates/workflows/processes/meta-workflow-authoring.md|E:files`templates/workflows/processes/meta-workflow-authoring.md`] Authored meta workflow authoring process to satisfy guard and unblock plan compliance.
- **2025-09-25 20:31**
  `date "+%Y-%m-%d %H:%M %Z"` => `2025-09-25 20:31 CEST` — [S:20250925|W:plan-compliance-phase1|H:templates/handlers/orchestrators/meta-workflow-authoring.md|E:files`templates/handlers/orchestrators/meta-workflow-authoring.md`] Added orchestrator to enforce plan-first workflow authoring.
- **2025-09-25 20:31**
  `date "+%Y-%m-%d %H:%M %Z"` => `2025-09-25 20:31 CEST` — [S:20250925|W:plan-compliance-phase1|H:templates/patterns/integration/workflow-gap-detection.md|E:files`templates/patterns/integration/workflow-gap-detection.md`] Added workflow gap detection pattern to route requests into meta workflow authoring.
- **2025-09-25 21:17**
  `date "+%Y-%m-%d %H:%M %Z"` => `2025-09-25 21:17 CEST` — [S:20250925|W:plan-compliance-phase1|H:.plan_state/sync.log|E:files`.plan_state/sync.log`] Refreshed plan ↔ tracker hash sync after workflow creation.
- **2025-09-25 20:33**
  `date "+%Y-%m-%d %H:%M %Z"` => `2025-09-25 20:33 CEST` — [S:20250925|W:plan-compliance-phase1|H:scripts/codex-guard|E:files`reports/plan-compliance-phase1/guard-20250925-2033.txt`] Guard validation now passes with plan compliance pipeline intact.
- **2025-09-25 21:18**
  `date "+%Y-%m-%d %H:%M %Z"` => `2025-09-25 21:18 CEST` — [S:20250925|W:plan-compliance-phase1|H:scripts/codex-guard|E:files`reports/plan-compliance-phase1/guard-20250925-2035.txt`] Guard re-run with `--include-untracked`; plan/tracker sync refreshed and evidence captured for verification step.
- **2025-09-25 21:22**
  `date "+%Y-%m-%d %H:%M %Z"` => `2025-09-25 21:22 CEST` — [S:20250925|W:plan-compliance-phase1|H:.plan_state/sync.log|E:files`.plan_state/sync.log`] Re-synced plan ↔ tracker after documentation updates.
- **2025-09-25 21:22**
  `date "+%Y-%m-%d %H:%M %Z"` => `2025-09-25 21:22 CEST` — [S:20250925|W:plan-compliance-phase1|H:scripts/codex-guard|E:files`reports/plan-compliance-phase1/guard-20250925-2122.txt`] Guard final pass (`--include-untracked`) captured for plan-step-verify evidence.
- **2025-09-25 21:22**
  `date "+%Y-%m-%d %H:%M %Z"` => `2025-09-25 21:22 CEST` — [S:20250925|W:plan-compliance-phase1|H:.serena/memories/plan_compliance_phase1_20250925|E:memory`plan_compliance_phase1_20250925`] Serena memory recorded for plan verification checkpoint.
- **2025-09-26 13:46**
  `date "+%Y-%m-%d %H:%M %Z"` => `2025-09-26 13:46 CEST` — [S:20250926|W:plan-compliance-followup|H:.taskmaster/tasks/tasks.json|E:note`rolled back`] Removed provisional Tasks 81–82 from Taskmaster; backlog remains in work-tracking for earlier insertion.
- **2025-09-26 14:02**
  `date "+%Y-%m-%d %H:%M %Z"` => `2025-09-26 14:02 CEST` — [S:20250926|W:plan-compliance-followup|H:docs/ai/work-tracking/active/20250920-codex-migration-ssot-ACTIVE/plans/taskmaster-audit-high-priority.md|E:files`.../plans/taskmaster-audit-high-priority.md`] Backlog expanded with plan compliance, timestamp gate, and enforcement framework task proposals (pending insertion).
- **2025-09-24 19:30**
  `date "+%Y-%m-%d %H:%M %Z"` => `2025-09-24 19:30 CEST` — [S:20250924|W:taskmaster-audit|H:scripts/codex-guard|E:note`guard run deferred`] Guard run deferred (plan pending); will validate once plan created.
- **2025-09-24 19:20**
  `date "+%Y-%m-%d %H:%M %Z"` => `2025-09-24 19:20 CEST` — [S:20250924|W:taskmaster-audit|H:scripts/codex-guard|E:files`scripts/codex-guard`] Extended guard with plan validation (plan template checks, tracker checklist, emergency bypass detection).
- **2025-09-24 19:05**
  `date "+%Y-%m-%d %H:%M %Z"` => `2025-09-24 19:05 CEST` — [S:20250924|W:taskmaster-audit|H:templates/behaviors/planning/plan-compliance|E:files`templates/behaviors/planning/plan-compliance.md`] Authored plan compliance behavior (plan template enforcement, emergency bypass protocol).
- **2025-09-24 18:55**
  `date "+%Y-%m-%d %H:%M %Z"` => `2025-09-24 18:55 CEST` — [S:20250924|W:taskmaster-audit|H:templates/workflows/processes/plan-template|E:files`templates/workflows/processes/plan-template.md`] Added plan template workflow (canonical steps, amendments, continuation, emergency bypass).
- **2025-09-24 18:50**
  `date "+%Y-%m-%d %H:%M %Z"` => `2025-09-24 18:50 CEST` — [S:20250924|W:taskmaster-audit|H:templates/engine/enforcement/behavioral-hooks|E:files`docs/ai/work-tracking/active/20250920-codex-migration-ssot-ACTIVE/designs/enforcement-framework-draft.md; docs/ai/work-tracking/active/20250920-codex-migration-ssot-ACTIVE/designs/template-drift-detection-draft.md; docs/ai/work-tracking/active/20250920-codex-migration-ssot-ACTIVE/designs/template-wizard-draft.md; docs/ai/work-tracking/active/20250920-codex-migration-ssot-ACTIVE/designs/template-metrics-dashboard-draft.md; docs/ai/work-tracking/active/20250920-codex-migration-ssot-ACTIVE/designs/template-enhancements-backlog.md`] Logged new enhancement drafts (drift detection, wizard, metrics dashboard, backlog).
- **2025-09-24 12:55**
  `date "+%Y-%m-%d %H:%M %Z"` => `2025-09-24 12:55 CEST` — [S:20250924|W:taskmaster-audit|H:templates/engine/enforcement/behavioral-hooks|E:note`drafts updated per Claude`] Updated design drafts with emergency bypass, plan amendments, conflict detection, migration strategy, task refinements.
- **2025-09-23 20:12** — [S:20250923|W:taskmaster-audit|H:templates/engine/enforcement/behavioral-hooks|E:files`docs/ai/work-tracking/active/20250920-codex-migration-ssot-ACTIVE/designs/enforcement-framework-draft.md`] Enforcement framework draft added (template-first guard requirements).
- **2025-09-23 20:05** — [S:20250923|W:taskmaster-audit|H:templates/handlers/triggers/session/end-session|E:note`handoff prep`] Session ending; tomorrow review drafts then implement plan compliance behavior/guard.
- **2025-09-23 19:55** — [S:20250923|W:taskmaster-audit|H:templates/workflows/processes/meta-workflow-authoring|E:note`drafts now task-ready`] Noted that design drafts now contain executable task/subtask outlines for implementation.
- **2025-09-23 19:50** — [S:20250923|W:taskmaster-audit|H:templates/workflows/processes/meta-workflow-authoring|E:note`task outlines appended`] Drafts now include proposed Taskmaster tasks/subtasks for implementation.
- **2025-09-23 19:40** — [S:20250923|W:taskmaster-audit|H:templates/behaviors/timestamps/before-adding|E:files`docs/ai/work-tracking/active/20250920-codex-migration-ssot-ACTIVE/designs/timestamp-gate-draft.md`] Timestamp gate drafted (command evidence, guard checks, optional helper).
- **2025-09-23 19:37** — [S:20250923|W:taskmaster-audit|H:templates/behaviors/planning/plan-compliance|E:note`timestamp gate request`] Logging need for timestamp gate and task/subtask planning discussion.
- **2025-09-23 18:15** — [S:20250923|W:taskmaster-audit|H:templates/behaviors/planning/plan-compliance|E:note`plan/meta drafts expanded`] Updated plan + meta workflow drafts (step IDs, sync procedure, regression/rollback notes).
- **2025-09-23 18:08** — [S:20250923|W:taskmaster-audit|H:templates/workflows/processes/meta-workflow-authoring|E:files`docs/ai/work-tracking/active/20250920-codex-migration-ssot-ACTIVE/designs/meta-workflow-authoring-draft.md`] Drafted meta workflow authoring design (creation + update process).
- **2025-09-23 18:02** — [S:20250923|W:taskmaster-audit|H:templates/behaviors/planning/plan-compliance|E:note`plan template+guard draft`] Extended plan compliance draft with template outline, guard spec, bypass rules, and sync logging.
- **2025-09-23 17:52** — [S:20250923|W:taskmaster-audit|H:templates/behaviors/planning/plan-compliance|E:note`plan sync draft`] Documented plan sync validator (guard enforces plan/tracker parity).
- **2025-09-23 17:47** — [S:20250923|W:taskmaster-audit|H:templates/behaviors/planning/plan-compliance|E:files`docs/ai/work-tracking/active/20250920-codex-migration-ssot-ACTIVE/designs/plan-compliance-draft.md`] Drafted plan compliance design doc (requirements + open questions).
- **2025-09-23 17:45** — [S:20250923|W:taskmaster-audit|H:templates/behaviors/planning/plan-compliance|E:note`documenting plan guardrails`] Documenting plan compliance requirements (minimum steps, guard checks) before implementation.
- **2025-09-23 17:08** — [S:20250923|W:taskmaster-audit|H:templates/workflows/processes/meta-workflow-authoring|E:note`codex plan vs todo`] Noted Codex plan tool as functional equivalent of Claude Todo list (plan update = TodoWrite, plan display = TodoRead).
- **2025-09-23 16:01** — [S:20250923|W:taskmaster-audit|H:templates/workflows/processes/meta-workflow-authoring|E:note`drafting only`] Implementation paused; drafting meta workflow authoring plan prior to changes.
- **2025-09-23 16:10** — [S:20250923|W:taskmaster-audit|H:templates/workflows/processes/meta-workflow-authoring|E:note`implementation deferred`] Holding Action 2 implementation until plan is reviewed.
- **2025-09-23 15:36** — [S:20250923|W:taskmaster-audit|H:templates/workflows/processes/meta-workflow-authoring|E:note`Action 2 plan documented`] Logged scope for meta workflow authoring (workflow + orchestrator + pattern + enforcement touchpoints).
- **2025-09-23 13:55** — [S:20250923|W:taskmaster-audit|H:templates/workflows/processes/meta-workflow-authoring|E:note`Action 2 scoping started`] Preparing meta workflow authoring plan prior to template edits.
- **2025-09-23 12:12** — [S:20250923|W:taskmaster-audit|H:templates/workflows/session/lifecycle|E:note`documented Action 1 scope`] Added recommended-actions tracking and prepped session continuation/state-management workflow plan prior to implementation.
- **2025-09-22 10:48** — [S:20250922|W:taskmaster-audit|H:templates/handlers/triggers/session/prepare-compaction|E:note`ready for new chat`] All work saved, ready for new context (compaction).
- **2025-09-22 10:48** — [S:20250922|W:taskmaster-audit|H:templates/handlers/triggers/session/prepare-compaction|E:note`checkpoint saved`] Completing Taskmaster audit checkpoint before compaction.
- **2025-09-22 10:48** — [S:20250922|W:taskmaster-audit|H:templates/handlers/triggers/session/prepare-compaction|E:note`context approaching limit`] ⚠️ Context approaching limit, preparing for compaction.
- **2025-09-22 10:45** — [S:20250922|W:taskmaster-audit|H:templates/workflows/patterns/task-management|E:files`docs/ai/work-tracking/active/20250920-codex-migration-ssot-ACTIVE/plans/taskmaster-audit-high-priority.md`] Logged proposed Task 15 “Author Development Workflow Modules” in audit plan for review prior to modifying tasks.json.
- **2025-09-22 10:15** — [S:20250922|W:taskmaster-audit|H:templates/handlers/triggers/session/start-session|E:note`session 2025-09-23-001 started for Taskmaster audit`] Session 2025-09-23-001 initiated to audit Taskmaster tasks for template-system alignment.
- **2025-09-20 13:05** — [S:20250920|W:codex-migration|H:templates/workflows/session/lifecycle|E:docs/ai/work-tracking/...`seeded`] Created work-tracking folder and seeded implementation plan.
- **2025-09-20 14:20** — [S:20250920|W:codex-migration|H:templates/tools/search/serena-guide|E:command`codex-wrapper --dry-run -- resume`] Verified Codex wrapper dry-run picks up `.codex/AGENTS.md` and registers the agents catalog.
- **2025-09-20 15:27** — [S:20250920|W:codex-migration|H:templates/workflows/patterns/task-management|E:plan`codex-task+guard`] Drafted enforcement plan (codex-task helper + diff-aware guard with optional auto-fix) and recorded decision.
- **2025-09-20 16:21** — [S:20250920|W:codex-migration|H:templates/workflows/analysis/evidence-gathering|E:command`python3 scripts/template-ssot-scanner/find_duplicates.py --generate-diffs --section-matching`] Ran duplicate analysis (outputs in `output/data/duplicate_analysis.json`).
- **2025-09-20 16:22** — [S:20250920|W:codex-migration|H:templates/workflows/analysis/evidence-gathering|E:command`python3 scripts/template-ssot-scanner/migration_detector.py`] Generated migration status report (`output/data/migration_status.json`).
- **2025-09-20 16:23** — [S:20250920|W:codex-migration|H:templates/workflows/analysis/evidence-gathering|E:command`python3 scripts/template-ssot-scanner/generate_fixes.py`] Produced fix recommendations & scripts (`output/data/fix_recommendations.json`, `output/scripts/`).
- **2025-09-20 16:24** — [S:20250920|W:codex-migration|H:templates/workflows/analysis/evidence-gathering|E:command`python3 scripts/template-ssot-scanner/safe_reorganize.py`] Ran safe reorganization simulation (no moves proposed; report in `scripts/template-ssot-scanner/output/reports/`).
- **2025-09-20 20:17** — [S:20250920|W:codex-migration|H:templates/coordination/session-swhe-integration|E:files`scripts/codex-task`] Logged codex-task helper for auto S:W:H:E scaffolds.
- **2025-09-20 20:18** — [S:20250920|W:codex-migration|H:templates/coordination/enforcement-enhancement-session|E:files`scripts/codex-guard`] Guard validates session/work-tracking S:W:H:E entries with handler/evidence checks.
- **2025-09-20 20:37** — [S:20250920|W:codex-migration|H:templates/handlers/triggers/docs/create-docs|E:files`CODEX.md; AGENTS.md; templates/TOOLS.md`] Extended docs to cover codex-task logging + codex-guard validations.
- **2025-09-20 21:06** — [S:20250920|W:codex-migration|H:templates/conventions/git/commit-format|E:files`templates/conventions/git/commit-format.md`] Aligned gac convention with new Summary layout and quote discipline.
- **2025-09-20 21:17** — [S:20250920|W:codex-migration|H:templates/handlers/triggers/session/end-session|E:note`session wrap-up`] Ended session for 2025-09-20; handoff + roadmap prep queued for next work block.
- **2025-09-21 12:24** — [S:20250921|W:codex-migration|H:templates/handlers/triggers/session/start-session|E:note`session initialized`] Session 2025-09-21-001 started; targeting remediation roadmap and guard planning.
- **2025-09-21 18:04** — [S:20250921|W:codex-migration|H:templates/handlers/triggers/docs/create-docs|E:files`.taskmaster/docs/prd.txt`] Elevated migration PRD to enterprise spec (exec summary, RACI, dashboards, scorecard, budget).
- **2025-09-23 10:15** — [S:20250923|W:codex-migration|H:templates/handlers/triggers/session/start-session|E:note`session 2025-09-23-001 started for Taskmaster audit`] Session 2025-09-23-001 initiated to audit Taskmaster tasks for template-system alignment.
- **2025-09-23 10:39** — [S:20250923|W:codex-migration|H:templates/workflows/patterns/task-management|E:files`.taskmaster/tasks/tasks.json`] Inserted Task 15 “Author Development Workflow Modules” and renumbered downstream IDs to reflect workflow enforcement priority.

## Current State
Scaffolding complete; baseline + follow-up scanner outputs captured (duplicates, migration status, fix scripts, safe reorganize). Enforcement helpers (`codex-task`, `codex-guard`) documented and validated; enterprise migration PRD ready for Taskmaster parsing (expansion target to be redefined) and remediation planning resumed on 2025-09-21 12:16 CEST.

## Next Steps
1. Align with loucmane on revised Taskmaster expansion targets before running PRD parse.
2. Synthesize scanner outputs into a remediation roadmap (reports + FINDINGS/CHANGELOG).
3. Define guard auto-fix/CI integration plan and capture follow-up tasks.
4. Prioritize reference/migration fixes using generated scripts and address circular dependencies/orphaned files.
5. Execute template system remediation actions sequentially (Action 1–10), documenting scope/results in sessions/ & work-tracking before changing tasks.json.

## Action Checklists

### Action 2 - Meta Workflow Authoring
- [ ] Draft meta workflow authoring process outline
- [ ] Create workflow file `templates/workflows/processes/meta-workflow-authoring.md`
- [ ] Add orchestrator handler enforcing the workflow
- [ ] Add gap-detection pattern routing to workflow
- [ ] Update registry/conventions/behaviors/Taskmaster references
- [ ] Document guard requirements for Action 9
- [ ] Log changes in sessions, tracker, implementation, findings

### Action 2 - Meta Workflow Authoring
- [ ] Draft meta workflow authoring process outline
- [ ] Create workflow file `templates/workflows/processes/meta-workflow-authoring.md`
- [ ] Add orchestrator handler enforcing the workflow
- [ ] Add gap-detection pattern routing to workflow
- [ ] Update registry/conventions/behaviors/Taskmaster references
- [ ] Document guard requirements for Action 9
- [ ] Log changes in sessions, tracker, implementation, findings

### Plan Compliance Enforcement
- [ ] Plan contains ≥3 steps (scope confirmation, implementation, verification)
- [ ] Plan step 1: Scope confirmed with loucmane
- [ ] Plan steps reference concrete deliverables (files/tests)
- [ ] Tracker checklist updated to mirror plan
- [ ] Guard hook documented (`codex-guard validate` plan check)
- [ ] Session/work-tracking entries note plan compliance status

## Plan Compliance Checklist
- [ ] plan-step-scope
- [ ] plan-step-implement
- [ ] plan-step-verify
- [ ] plan-step-emergency (if applicable)
