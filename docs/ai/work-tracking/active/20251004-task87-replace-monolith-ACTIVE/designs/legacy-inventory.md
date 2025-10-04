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
- `templates/WORKFLOWS.md#common-workflows` → `templates/workflows/examples/common-workflows.md` (pending) — update quick links section.
- `templates/WORKFLOWS.md` → `templates/workflows/domain/README.md` (pending) — point general workflow overview to modular index.
- `templates/BUILDING-BETTER.md#creating-handlers` → `templates/integration/guides/creating-handlers.md` (pending) — direct to modular handler guide.

### templates/HANDLERS.md
- `WORKFLOWS.md#handler-start-new-work` → `templates/handlers/triggers/development/start-new-work.md` (pending).
- `WORKFLOWS.md#handler-continue-work` → `templates/handlers/triggers/workflow/continue-work.md` (pending).
- `WORKFLOWS.md#handler-standard-dev-workflow` → `templates/handlers/orchestrators/standard-dev-workflow.md` (pending).
- `WORKFLOWS.md#handler-create-component` → `templates/handlers/triggers/development/create-component.md` (pending).
- `WORKFLOWS.md#handler-refactor-code` → `templates/handlers/triggers/development/refactor-code.md` (pending).
- `WORKFLOWS.md#handler-fix-problem` → `templates/handlers/triggers/debug/fix-bug.md` (pending — confirm naming alignment).
- `WORKFLOWS.md#handler-create-commit-message` → `templates/handlers/operators/git/create-commit-message.md` (missing — needs authoring).
- `WORKFLOWS.md#handler-show-capabilities` → `templates/handlers/triggers/session/show-capabilities.md` (pending).
- Text references to `create-test-checkpoint` / `code-review-workflow` → respective modular handlers under `templates/handlers/triggers/test/` and `templates/handlers/triggers/analysis/` (pending).

### templates/BUILDING-BETTER.md
- `resolve-work-void` anchor → `templates/handlers/operators/workflow/resolve-work-void.md` (pending).
- Generic mention of **WORKFLOWS.md** → replace with modular workflow directory overview (pending).

### templates/CONVENTIONS.md
- `[WORKFLOWS.md](WORKFLOWS.md)` → point to modular workflow index (pending).

### templates/behaviors & registry
- Multiple mentions of `WORKFLOWS.md` in `templates/behaviors/index.md`, `templates/behaviors/work-tracking/update-tracker.md`, `templates/REGISTRY.md`, `templates/behaviors/BEHAVIORS.md`, `templates/registry/index.md`, `templates/matrices/*.md`, `templates/tools/index.md`, `templates/USER-GUIDE.md`. Each needs mapping to modular workflow/doc equivalents; catalog replacements during sweep (pending).

### templates/handlers/orchestrators/work-activity.md
- Internal references to `WORKFLOWS.md#start-new-work` / `#continue-work` → update to orchestrator/trigger files (pending).

### Metadata Artifacts
- `templates/metadata/template-overview.md`, `template-summary.csv`, `template-inventory.txt` still list monolith files — replace with modular entries (pending).

### External Outputs
- Generated reports under `output/data/` and `output/scripts/` reference monoliths; keep as historical evidence but ensure remediation scripts regenerate after replacements (note).

## Next Actions
1. Collect all references to monolithic sections.
2. Map each reference to new domain workflow or helper.
3. Track progress in tracker and plan table.
