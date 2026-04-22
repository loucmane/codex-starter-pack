# Task 91 – Standardize Template Metadata Implementation Notes

## Planned Workstreams
1. **Inventory & Scope**
   - [x] Record current frontmatter coverage and identify the main file classes.
   - [x] Define which template families are in scope for first-pass standardization.
2. **Schema**
   - [x] Publish the canonical metadata schema and required keys for modular templates.
3. **Batch Updates**
   - [x] Apply the schema to high-volume template families with partial frontmatter, starting with handlers.
   - [x] Handler slice completed across `triggers`, `orchestrators`, and `operators`.
   - [x] Behavior slice completed across the in-scope behavior files, with `templates/behaviors/index.md` left exempt.
   - [x] Guide slice completed across `templates/guides/**`.
   - [x] Matrix slice completed across `templates/matrices/**`, with `templates/matrices/index.md` kept policy-exempt as the aggregate navigation entry.
   - [x] Registry slice completed across non-exempt `templates/registry/**` modules, with `index.md` and `MIGRATION-REPORT.md` kept exempt.
   - [x] Engine/outlier slice completed across non-exempt `templates/engine/**`, `templates/shared/patterns/ultrathink-format.md`, and `templates/handlers/tools/external/consult-gpt5.md`.
4. **Guard**
   - [x] Extend `scripts/codex-guard` to enforce the agreed metadata presence on the in-scope file classes.
   - [x] Add a configurable metadata-policy layer so scope and exemptions are data-driven instead of hardcoded.
   - [x] Add multi-day active-folder reuse handling and fenced-code SWHE example filtering so verification works against real protocol usage.
5. **Documentation & Verification**
   - [x] Document the rollout and add tests/evidence for the new metadata enforcement behavior.

## Notes
- The kickoff inventory suggests handlers, behaviors, and engine modules with partial frontmatter are the best first-pass update targets.
- Aggregate, generated, or report-style docs should be reviewed separately before adding blanket frontmatter rules.
- The schema rollout is additive in the first pass: add `title`, `type`, and `status` while preserving family-specific fields already used by existing docs and tooling.
- After the handler slice, the next likely families are behaviors and then the smaller guide/matrix/registry groups.
- Portability now depends on `templates/metadata/template-metadata-policy.json`, which lets other repos reuse the same guard logic with different include/exclude/enforcement rules.
- After the behavior slice, the next likely families are guides, matrices, registry components, and selected engine modules with partial frontmatter.
- After the guide slice, the next likely families are matrices, registry components, selected engine modules, and the remaining outlier files.
- April 22 continuation begins with a formal session rollover: close the April 21 kickoff session first, then resume the implementation path with the `matrices` family as the next highest-leverage slice.
- Final verification evidence lives under `reports/standardize-template-metadata/` and the enforced metadata scan now returns zero remaining files.
