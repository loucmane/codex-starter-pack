# Task 85 – Continuation & State Workflow Implementation Plan

**Captured**: 2025-10-02 14:20 CEST (`date "+%Y-%m-%d %H:%M %Z"`)

## Objectives
- Refine `templates/workflows/session/continuation.md` and `state-management.md` for Codex-first workflow (plan + tracker instead of TodoWrite/TodoRead).
- Ensure guard coverage for continuation/state flows (plan compliance, tracker chronology, Serena memory presence when required).
- Prepare concrete implementation steps for subtasks 85.2–85.5 and regression coverage (85.7).

## Planned Modifications
### Workflows & Handlers (Subtasks 85.2 & 85.3)
1. **Continuation Workflow (`templates/workflows/session/continuation.md`)**
   - Remove TodoWrite/TodoRead references; replace with plan + Taskmaster alignment steps.
   - Add explicit requirement to run `python3 scripts/codex-guard validate --include-untracked` before resuming.
   - Include evidence checklist: updated session log, tracker entry, guard log, Serena memory ID (if active).
   - Insert continuation guard hook: reference new behavior `templates/behaviors/session/continuation/validation.md`.
2. **State Management Workflow (`templates/workflows/session/state-management.md`)**
   - Update core artifacts list to emphasize plan/Taskmaster integration.
   - Add state restoration sequence referencing continuation workflow + guard check.
   - Define when Serena memory is optional vs. required, with fallback instructions.
3. **New/Updated Behaviors & Operators**
   - Create `templates/behaviors/session/continuation/validation.md` to enforce plan/tracker sync before continuation.
   - Update `templates/handlers/orchestrators/work-continuation.md` to call validation behavior + guard.

### Registry & Metadata (Subtask 85.4)
- Update `templates/registry/index.json` and `templates/metadata/template-overview.md` to reference new behavior file.
- Refresh legacy references in `templates/PATTERNS.md`, `templates/REGISTRY.md` to point to modular workflow/behavior paths.
- Extend `templates/metadata/workflow-guards.json` with continuation-guard entry referencing new behavior and guard checks.

### Guard Enhancements (Subtask 85.5)
- Add `validate_continuation_state()` in `scripts/codex-guard` to ensure:
  - Plan/tracker hash sync recorded within current session before continuation entries.
  - Session log entries include guard log reference when resuming after compaction/continuation.
  - Optional: require Serena memory link if `MEMORY-REFS.md` indicates Serena usage.
- Provide auto-fix hints (if guard fails) pointing to continuation workflow steps.

### Documentation & Evidence (Subtask 85.6)
- Update `docs/ai/work-tracking/active/.../IMPLEMENTATION.md` and `FINDINGS.md` as changes land.
- Prepare checklist for plan-step-implement completion (session + tracker entries, guard log, updated plan table).

### Regression Suite (Subtask 85.7)
- Add tests under `tests/session_continuation/`:
  1. Unit tests for guard: simulate missing plan sync, missing session continuation evidence.
  2. Integration test: run `scripts/codex-guard validate` against sample repo snapshot with continuation data.
  3. Future placeholder for Serena memory enforcement (skipped unless Serena enabled).
- Store outputs in `reports/session-continuation/tests-<timestamp>.txt`.

## Execution Order
1. Implement workflow updates (continuation + state-management) and create validation behavior file.
2. Update orchestrator + registry metadata to wire new behavior.
3. Enhance guard with continuation/state checks.
4. Document evidence + update plan/tracker.
5. Write regression tests and capture outputs.

## Risks & Mitigations
- **Guard strictness**: may block workflows for users not using Serena. Mitigation: add configuration flag or fallback instructions.
- **Legacy references**: ensure no lingering monolithic references remain; run SSOT scanner if needed.
- **Test coverage scope**: start with guard-based tests; add workflow rendering tests later if time allows.

## Dependencies
- `scripts/codex-guard`
- `templates/workflows/session/continuation.md`
- `templates/workflows/session/state-management.md`
- `templates/registry/index.json`
- `templates/metadata/workflow-guards.json`
- `tests/session_continuation/` (new)

## Next Actions
- Update plan table (plan-step-implement evidence list) once initial edits begin.
- Begin editing continuation workflow per this design, logging S:W:H:E entries for each change.
