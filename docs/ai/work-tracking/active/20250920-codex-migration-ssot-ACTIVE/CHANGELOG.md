# Changelog

## 2025-09-20

### Added
- Created Codex work-tracking folder with required documentation files and supporting subdirectories.
- Ported SSOT scanner suite into Codex repo and ran initial scans.
- Documented enforcement plan (codex-task helper + diff-aware guard with optional auto-fix).
- Implemented `scripts/codex-task` (session/work-tracking scaffolds) and `scripts/codex-guard` (diff-aware validator) with initial local validation.
- Captured duplicate analysis, migration detector, fix generation, and safe reorg outputs (`output/data/*`, `scripts/template-ssot-scanner/output/`).
- Logged scanner summary in `reports/2025-09-20-ssot-scanner-summary.md`.

### Changed
- Updated `templates/TOOLS.md` with explicit Serena MCP guidance for Codex users.
- Patched scanner scripts to detect `.codex/` configs alongside legacy `.claude/` paths.
- Confirmed Codex wrapper initializes with project agents catalog (`.codex/AGENTS.md`).
- Work-tracking/session logs now include codex-task/codex-guard S:W:H:E entries seeded via helper.

### Fixed
- N/A (auto-fix mode for guard still pending).

### Removed
- None.

## 2025-09-21

### Added
- Enterprise-level migration PRD deliverables (executive summary, RACI matrix, telemetry dashboards, communication templates, scorecard).
- Quick reference card and migration weekly scorecard framework for ongoing operations.

### Changed
- Updated `.taskmaster/docs/prd.txt` with budget/timeline targets, naming conventions, governance procedures, rehearsal checklist, and monitoring stack.

### Fixed
- N/A.

### Removed
- None.

## 2025-09-25

### Added
- Established active plan file (`plans/2025-09-25-plan-compliance-phase1.md`) and plan compliance checklist within tracker.
- Created `.plan_state/sync.log` hash record to support guard parity checks.
- Captured guard outputs in `reports/plan-compliance-phase1/guard-20250925-1849.txt`, `guard-20250925-2033.txt`, `guard-20250925-2035.txt`, and `guard-20250925-2122.txt`.
- Authored `templates/workflows/processes/meta-workflow-authoring.md`, orchestrator (`templates/handlers/orchestrators/meta-workflow-authoring.md`), and routing pattern (`templates/patterns/integration/workflow-gap-detection.md`).

### Changed
- Extended `scripts/codex-guard` with plan evidence validation, tracker status parity, plan sync log enforcement, and shallow conflict detection.
- Updated tracker/session logs with S:W:H:E entries for plan, orchestrator/pattern creation, sync logging, and guard execution.

### Issues
- Plan verification still open; need documentation sweep, Serena memory, and timestamp gate follow-through.

### Removed
- None.

## 2025-09-27

### Added
- Implemented `python3 scripts/codex-task plan sync` helper and appended Phase 2 plan file (`plans/2025-09-27-plan-compliance-phase2.md`).
- Captured guard output with emergency bypass validation (`reports/plan-compliance-phase2/guard-20250927-113559.txt`).
- Enforced branch/task alignment in `scripts/codex-guard` (feature branch must match plan Task IDs or policy `main-only`).

### Changed
- Updated `scripts/codex-guard` with tracker waiver check for emergency bypass.
- Refreshed session/work-tracking docs to reference plan sync command and bypass remediation notes.
- Marked Taskmaster Task 81 (plan compliance enforcement) as completed following guard/doc updates.
- Added Branch Policy guidance to plan template and plan compliance behavior.
- Guard now enforces meta workflow plan scope when workflows are modified.

### Issues
- Plan verification step still pending final Serena memory + handoff confirmation.

### Removed
- None.
