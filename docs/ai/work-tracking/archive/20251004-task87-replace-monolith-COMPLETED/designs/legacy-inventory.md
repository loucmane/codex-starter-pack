# Legacy Reference Inventory (Task 87)

## Date / Time
- Captured: 2025-10-04 13:45 CEST

## Legacy Files
- templates/WORKFLOWS.md
- templates/PATTERNS.md
- templates/BUILDING-BETTER.md

## Initial Scan Commands
```bash
rg "WORKFLOWS.md" -n
rg "PATTERNS.md" -n
rg "BUILDING-BETTER" -n
```

## Reference Map

### CODEX.md
- `templates/WORKFLOWS.md#common-workflows` → `templates/workflows/examples/common-workflows.md` (updated 2025-10-04) — update quick links section.
- `templates/WORKFLOWS.md` → `templates/workflows/domain/README.md` (updated 2025-10-04) — point general workflow overview to modular index.
- `templates/BUILDING-BETTER.md#creating-handlers` → `templates/integration/guides/creating-handlers.md` (updated 2025-10-04) — direct to modular handler guide.

### templates/HANDLERS.md
- `WORKFLOWS.md#handler-start-new-work` → `templates/handlers/triggers/development/start-new-work.md` (updated 2025-10-04).
- `WORKFLOWS.md#handler-continue-work` → `templates/handlers/triggers/workflow/continue-work.md` (updated 2025-10-04).
- `WORKFLOWS.md#handler-standard-dev-workflow` → `templates/handlers/orchestrators/standard-dev-workflow.md` (updated 2025-10-04).
- `WORKFLOWS.md#handler-create-component` → `templates/handlers/triggers/development/create-component.md` (updated 2025-10-04).
- `WORKFLOWS.md#handler-refactor-code` → `templates/handlers/triggers/development/refactor-code.md` (updated 2025-10-04).
- `WORKFLOWS.md#handler-fix-problem` → `templates/handlers/triggers/debug/fix-bug.md` (updated 2025-10-04; confirmed mapping).
- `WORKFLOWS.md#handler-create-commit-message` → `templates/handlers/operators/git/create-commit-message.md` (created 2025-10-04).
- `WORKFLOWS.md#handler-show-capabilities` → `templates/handlers/triggers/session/show-capabilities.md` (updated 2025-10-04).
- Text references to `create-test-checkpoint` / `code-review-workflow` → respective modular handlers under `templates/handlers/triggers/test/` and `templates/handlers/triggers/analysis/` (updated 2025-10-04).

### templates/PATTERNS.md
- Legacy file now stubbed; ensure all external references point to `templates/patterns/*` modular directories.
- For routing/selection/evidence patterns, link to specific modular files (e.g., `templates/patterns/routing/meta-routing.md`, `templates/patterns/selection/tool-selection.md`).

### templates/BUILDING-BETTER.md
- `resolve-work-void` anchor → `templates/handlers/operators/workflow/resolve-work-void.md` (pending).
- Generic mention of **WORKFLOWS.md** → replaced with modular workflow directory overview (2025-10-04).

### templates/CONVENTIONS.md
- `[WORKFLOWS.md](WORKFLOWS.md)` → point to modular workflow index (pending).

### templates/REGISTRY.md
- Headings referencing `WORKFLOWS.md` (Development, Task Management, Session Management, Specialist Deployment, Testing, Work Tracking) → mapped to modular workflow docs (templates/workflows/domain/*.md) and copy updated (2025-10-04).
- Quick reference link `[WORKFLOWS.md#common-workflows]` → `templates/workflows/examples/common-workflows.md` (updated 2025-10-04).

### templates/MATRICES.md
- Decision matrix rows citing `WORKFLOWS.md` anchors → swapped to modular handler paths (templates/handlers/*, templates/workflows/domain/*) on 2025-10-04.
- Work tracking matrix row referencing `create-work-folder` updated to `templates/handlers/operators/workflow/create-work-folder.md` (2025-10-04).

### templates/tools/index.md
- Bullet now points to `templates/workflows/domain/README.md` with example links (2025-10-04).

### templates/USER-GUIDE.md
- References like `[WORKFLOWS.md#common-workflows]` → linked to `templates/workflows/examples/common-workflows.md` (2025-10-04).

### templates/PROJECT-BLOG.md
- Section linking to **WORKFLOWS.md** → updated to modular workflow overview (2025-10-04).

### templates/behaviors & registry
- Multiple mentions of `WORKFLOWS.md` in behaviors/registry/matrices/tools/user guide mapped to modular docs (2025-10-04).

### templates/handlers/orchestrators/work-activity.md
- Internal references to `WORKFLOWS.md#start-new-work` / `#continue-work` updated to orchestrator/trigger files (2025-10-04).

- `templates/metadata/template-summary.csv`, `template-inventory.txt` currently list monolith roots; replace rows with modular structure entries (domain workflows, pattern directories, etc.).
- `templates/metadata/workflow-guards.json` may reference monolith workflows; verify guard targets align with modular files.

### Metadata Artifacts
- `templates/metadata/template-overview.md`, `template-summary.csv`, `template-inventory.txt` still list monolith files — replace with modular entries (pending).

### External Outputs
- Generated reports under `output/data/` and `output/scripts/` reference monoliths; keep as historical evidence but ensure remediation scripts regenerate after replacements (note).

## Next Actions
1. Collect all references to monolithic sections.
2. Map each reference to new domain workflow or helper.
3. Track progress in tracker and plan table.
