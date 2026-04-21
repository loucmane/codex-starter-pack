# Decisions

- 2026-04-21 — Start Task 90 from a fresh branch on clean `main` and use a new dated active folder instead of reusing the completed Task 89 folder.
- 2026-04-21 — Treat the first implementation step as a roadmap audit so engine module scope is confirmed before editing templates or registries.
- 2026-04-21 — Do not author any “missing” engine modules until the audit determines whether the README is stale documentation or the engine migration is genuinely incomplete.
- 2026-04-21 — Use README + verification-script reconciliation as the first Task 90 implementation slice unless later audit evidence reveals truly missing engine modules.
- 2026-04-21 — Keep the historical `templates/engine/verify-phase1.sh` path for continuity, but redefine it to validate the current engine surface instead of legacy `.claude` import assumptions.
- 2026-04-21 — Support both `id` and `name` frontmatter keys in engine verification because the current engine tree legitimately uses both conventions.
- 2026-04-21 — Treat registry/index plus metadata files as a single discoverability surface and update them together whenever engine inventory changes.
- 2026-04-21 — Fix the guard false positive in `scripts/codex-guard` rather than stripping valid `*-workflows.md` / `*-patterns.md` filenames from metadata documents.

## Progress Log
- **2026-04-21 12:51** — [S:20260421|W:task90-complete-engine-migration|H:docs/decisions|E:docs/ai/work-tracking/active/20260421-task90-complete-engine-migration-ACTIVE/DECISIONS.md] Recorded fresh-branch/fresh-folder kickoff decision and scope-first audit policy
- **2026-04-21 12:51** — [S:20260421|W:task90-complete-engine-migration|H:docs/decisions|E:docs/ai/work-tracking/active/20260421-task90-complete-engine-migration-ACTIVE/DECISIONS.md] Deferred module authoring until README/registry/CLAUDE drift is resolved by the roadmap audit
- **2026-04-21 12:51** — [S:20260421|W:task90-complete-engine-migration|H:docs/decisions|E:docs/ai/work-tracking/active/20260421-task90-complete-engine-migration-ACTIVE/DECISIONS.md] Selected README + verify-phase1 reconciliation as the likely first implementation slice for Task 90
- **2026-04-21 13:27** — [S:20260421|W:task90-complete-engine-migration|H:docs/decisions|E:templates/engine/verify-phase1.sh] Retained the historical verifier path while redefining its checks around the current engine tree and discovery surfaces
- **2026-04-21 13:27** — [S:20260421|W:task90-complete-engine-migration|H:docs/decisions|E:templates/engine/README.md] Documented mixed frontmatter handling instead of forcing a single schema across all engine documents
- **2026-04-21 14:17** — [S:20260421|W:task90-complete-engine-migration|H:docs/decisions|E:templates/registry/index.json] Decided to align registry/index and metadata together so engine discoverability surfaces stay consistent
- **2026-04-21 14:17** — [S:20260421|W:task90-complete-engine-migration|H:docs/decisions|E:scripts/codex-guard] Chose precise regex-based monolith detection instead of weakening metadata coverage to satisfy the guard
