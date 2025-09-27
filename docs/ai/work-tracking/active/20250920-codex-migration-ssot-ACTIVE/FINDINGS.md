
> **Codex Equivalent:** References to Claude's TodoWrite/TodoRead should be handled in Codex by updating the plan tool (Plan update ≈ TodoWrite, Plan display ≈ TodoRead) alongside the work-tracking checklists.
# Findings

## Discoveries
- Historical reports (2025-08) highlight dangerous legacy scripts (`reorganize_files.sh`) and confirm the safety features we must preserve (`safe_reorganize.py`, consolidated reference fixer).
- Codex templates still rely heavily on Serena MCP tooling; documentation updates must reinforce that rather than remove it.
- Enterprise-grade migration PRD completed (exec summary, RACI, dashboards, governance, scorecard) to drive Taskmaster planning (target 80/300 tasks).

## Test Results
- `python3 scripts/template-ssot-scanner/scanner.py --base /home/loucmane/codex --no-checkpoints` ✅ (237 files; outputs in `output/data/`).
- `python3 scripts/template-ssot-scanner/analyze_references.py` ✅ (181 broken refs, 10 circular deps baseline).
- `python3 scripts/template-ssot-scanner/find_duplicates.py --generate-diffs --section-matching` ✅ (duplicate_analysis.json; overall migration 9%).
- `python3 scripts/template-ssot-scanner/migration_detector.py` ✅ (migration_status.json confirms 4 fully migrated files, etc.).
- `python3 scripts/template-ssot-scanner/generate_fixes.py` ✅ (fix_recommendations.json + scripts in `output/scripts/`).
- `python3 scripts/template-ssot-scanner/safe_reorganize.py` ✅ (dry-run; no moves proposed; report in `scripts/template-ssot-scanner/output/reports/`).
- `python3 scripts/codex-guard validate` ⚠️ (new plan enforcement checks pass structurally but block on missing `templates/workflows/processes/meta-workflow-authoring.md`; remediation pending).

## Performance Observations
- Scanner run inside Codex repo completed in ~0.2s (thanks to limited file set and local execution).

## Issues Encountered
- Taskmaster task graph requires audit to ensure each task/subtask aligns with the template migration plan (Session 2025-09-23-001).
- Optional packages for sequential thinking/fpl MCP still need manual installation; tracked separately.
- Migration status reports show majority of monolithic files still partially/not migrated (needs remediation via generated scripts).
- Guard previously blocked on missing `templates/workflows/processes/meta-workflow-authoring.md`; workflow + orchestrator + routing pattern now added (2025-09-25 20:31 CEST).
- Plan compliance Phase 1 verification complete (guard/test evidence logged, Serena memory recorded, plan archived).
- Tasks 81–84 (plan compliance enforcement, meta workflow enforcement, regression suite, timestamp guard) added to Taskmaster; tasks 15–20 now depend on timestamp guard (84).
- Drafted and inserted tasks 85–97 covering session workflows, domain packs, legacy anchors, Taskmaster alignment workflow, work-tracking orchestration, engine migration, metadata standardization, guard expansion, compaction behavior rewrite, and enhancement backlog (drift detection, wizard, metrics dashboard) with chained dependencies.

## Enforcement Helper Status (2025-09-20 20:18)
- `scripts/codex-task` now scaffolds S:W:H:E entries for sessions and work-tracking; `scanner run` can log executions post-command.
- `scripts/codex-guard validate` parses git changes and enforces handler/evidence compliance (supports `--include-untracked`).
- New `python3 scripts/codex-task plan sync` command records plan/tracker hash parity into `.plan_state/sync.log` for guard validation.
- Branch guard enforcement active: current branch must follow plan Branch Policy (e.g. `feat/<task-id>-…` or documented `main-only` waiver).
- Documentation updates pending (CODEX.md, templates/TOOLS.md) to publicize workflow usage.
- TODO: add guard auto-fix skeleton support and CI/pre-commit integration.

## Template System Audit (2025-09-23)
- Guard updated to enforce plan template (scope, continuation, emergency bypass) and tracker checklist alignment.
- Added design drafts for template drift detection, interactive wizard, metrics dashboard, and backlog per Claude recommendations.
- Incorporated Claude feedback: emergency bypass, plan amendments, conflict detection, new guard proposals added to drafts.
- Plan compliance, meta workflow, and timestamp gate drafts now include executable Taskmaster-style task outlines.
- Plan compliance + meta workflow designs updated with canonical step IDs, plan-template table, guard procedures, regression/rollback guidance.
- Drafting plan compliance behavior (minimum plan steps, guard enforcement) to formalize plan-first discipline.
- Codex plan tool serves as TodoWrite/TodoRead equivalent; use plan updates for task creation and plan summaries for status reviews.
- Meta workflow authoring plan drafted; assets (workflow, orchestrator, gap-detection pattern) pending implementation approval.
- Action 2 will establish a meta workflow authoring process (workflow + orchestrator + gap-detection pattern) to prevent future coverage gaps.
- Full inventory (237 templates) captured in templates/metadata/{template-inventory.txt, template-summary.csv, template-overview.md}.
- Missing session workflows (continuation/state-management); references currently broken and fall back to handlers/patterns only.
- No meta workflow for authoring new workflows/handlers/guards; Taskmaster edits lack enforced checklist.
- Domain-specific workflow packs (frontend/backend/API/testing/ops) absent; conventions/guards need expansion.
- Legacy WORKFLOWS.md anchors still referenced across handlers/patterns/registry; modular replacements required.
- Taskmaster alignment workflow, work-tracking orchestration, engine Phase 2/3 modules, and guide stubs still outstanding.
- Metadata inconsistencies: ~118 modules missing status, 40 lacking frontmatter; workflow guards limited to code-style keywords.
- Behavior compaction-detection file remains deprecated but indexed; needs archival or rewrite.
