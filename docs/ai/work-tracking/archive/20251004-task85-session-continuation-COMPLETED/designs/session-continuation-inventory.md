# Session Continuation & State Workflow Inventory (Task 85)

## Date / Time
- Captured: 2025-10-01 16:07 CEST (`date "+%Y-%m-%d %H:%M %Z"`)

## Existing Assets
- `templates/workflows/session/continuation.md` (stable v1.0.0) — defines continuation flow but still references TodoWrite/TodoRead pairing and lacks plan/guard hooks for Codex.
- `templates/workflows/session/state-management.md` — outlines persistence steps; references continuation workflow but missing explicit guard integration points.
- `templates/patterns/session/continuation-patterns.md` & `templates/patterns/session/state-patterns.md` — provide conceptual guidance; need cross-links to guard behaviours.
- `templates/handlers/orchestrators/work-continuation.md` — orchestrator exists; registry entry present under `templates/metadata/template-overview.md`, `templates/metadata/workflow-guards.json`, and `templates/registry/index.json`.
- `templates/workflows/session/compaction.md` & behaviours `session/compaction-preparation.md`, `session/compaction-detection.md` — already reference continuation checkpoints but do not enforce plan/tracker compliance after compaction handoff.
- Registry touchpoints found via `rg "continuation" templates -n` (see session log) include workflow, pattern, registry metadata, and guard JSON entries.

## Gaps Identified
1. **Codex-specific alignment** — Continuation/state workflows still reference TodoWrite/TodoRead mapping notes; require explicit Plan/Taskmaster + work-tracking enforcement steps (guard needs to verify plan/tracker alignment before continuation).
2. **Guard coverage** — `scripts/codex-guard` currently lacks dedicated validation for session continuation (e.g., ensuring session log + tracker chronology verified across compactions/continuations, verifying Serena memory references when required).
3. **Routing consistency** — Some registry documents still map to monolithic references (e.g., `templates/PATTERNS.md`, `templates/REGISTRY.md`) that should point to modular files. Need to confirm and update to maintain SSOT.
4. **State recovery workflow** — No dedicated orchestrator/operator chain ensures active plan/tracker/Serena state restored before continuing; design should specify guard + automation requirements.
5. **Evidence expectations** — Current workflows mention evidence qualitatively; Task 85 must formalize required artifacts (session log entry, tracker update, guard log, Serena memory) and ensure plan-step-verify captures them.

## Scope Recommendations
- Update continuation + state-management workflows to codify guard checkpoints and evidence lists.
- Author new orchestrator/behavior files if guard integration requires additional handlers (e.g., `session/continuation/validate-plan` behaviour).
- Refresh registry/metadata (JSON + markdown) to ensure continuation/state assets are indexed correctly under modular structure.
- Define regression test suite under `tests/session_continuation/` for guard validations.

## Next Actions
- Translate these gaps into implementation tasks for plan-step-implement.
- Update plan table `plan-step-scope` to completed with evidence reference to this document and tracker entries.
