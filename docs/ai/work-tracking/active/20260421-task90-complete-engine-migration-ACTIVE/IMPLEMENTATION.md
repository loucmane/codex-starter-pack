# Task 90 Task 90 Complete Engine Migration – Implementation Notes

## Planned Workstreams
1. **Roadmap Audit**
   - [x] Inventory existing engine modules and missing migration targets.
   - [x] Identify registry/discovery surfaces that still require migration updates.
2. **Roadmap Reconciliation**
   - [x] Update `templates/engine/README.md` to reflect the current engine module set.
   - [x] Modernize `templates/engine/verify-phase1.sh` away from `.claude`-era assumptions.
3. **Module Authoring**
   - [ ] Implement missing engine modules under `templates/engine/`.
4. **Registry & Discoverability**
   - [x] Update registries/indexes/navigation so current engine modules and enforcement docs are discoverable.
5. **Documentation & Tests**
   - [x] Document usage and add/update tests for engine metadata coverage.
6. **Guard Hooks**
   - [x] Add required guard coverage tied to engine metadata discoverability and false-positive prevention.

## Notes & Considerations
- Audit the scope before editing implementation files so Task 90 does not sprawl into unrelated template work.
- Use archived Task 89 enforcement outputs as the current baseline for tracker/session/guard expectations.
- Current audit indicates the most likely first deliverable is reconciliation of stale engine docs/verification rather than authoring many new modules.
- The reconciled verifier now passes against the real engine tree and the current registry/metadata discovery surfaces; use that baseline before deciding whether any module authoring is still required.
- Current follow-up slice aligned registry/index and metadata surfaces, then added regression coverage so the same drift cannot return silently.

## Progress Log
- **2026-04-21 12:51** — [S:20260421|W:task90-complete-engine-migration|H:docs/implementation|E:docs/ai/work-tracking/active/20260421-task90-complete-engine-migration-ACTIVE/IMPLEMENTATION.md] Added kickoff workstreams aligned to Task 90 subtasks
- **2026-04-21 12:51** — [S:20260421|W:task90-complete-engine-migration|H:docs/implementation|E:docs/ai/work-tracking/active/20260421-task90-complete-engine-migration-ACTIVE/IMPLEMENTATION.md] Refined workstreams after audit found stale README and phase-1 verification script
- **2026-04-21 13:27** — [S:20260421|W:task90-complete-engine-migration|H:docs/implementation|E:docs/ai/work-tracking/active/20260421-task90-complete-engine-migration-ACTIVE/reports/complete-engine-migration/verify-phase1-2026-04-21-pass.txt] Recorded the first implementation slice as complete: current README/verifier reconciliation with a passing verification report
- **2026-04-21 14:17** — [S:20260421|W:task90-complete-engine-migration|H:docs/implementation|E:docs/ai/work-tracking/active/20260421-task90-complete-engine-migration-ACTIVE/reports/complete-engine-migration/tests-2026-04-21-engine-metadata.txt] Recorded the second implementation slice as complete: engine metadata/registry alignment plus regression coverage
