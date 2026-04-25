# Decisions

- 2026-04-24 — Treat Task 102 as a documentation-only task unless a concrete mismatch in the docs reveals a real bug in existing helpers or policies.
- 2026-04-24 — Structure the guidance around new-repo adoption, existing-repo migration, optional layers, and verification so readers can enter at the right stage without reading every prior task artifact.
- 2026-04-24 — Publish the adoption guide as `templates/engine/validation/foundation-adoption-guide.md` and treat it as part of the canonical engine surface rather than burying it in task-local notes.
- 2026-04-25 — Treat `sessions/state.json.current: null`, no `sessions/current`, no `plans/current`, and no active work-tracking folder as a valid between-sessions state; guard/audit should not force stale symlinks back to a completed task just to pass validation.
