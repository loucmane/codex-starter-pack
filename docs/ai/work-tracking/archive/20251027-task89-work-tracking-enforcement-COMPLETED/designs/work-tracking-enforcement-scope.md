# Task 89 Work-Tracking Enforcement – Scope Notes

## Objectives
- Expand the seven-file work-tracking checklist into an enforceable workflow (TRACKER, IMPLEMENTATION, FINDINGS, DECISIONS, CHANGELOG, HANDOFF, REPORTS).
- Integrate guard signals that fail when any touched active folder lacks fresh updates in tracker/findings/decisions/changelog or when plan sync / Serena memory is missing.
- Enhance `scripts/codex-task` helpers (scaffold/update/archive) to prompt for all required files, timestamp logging, Serena memory entries, and Taskmaster status updates.
- Document the workflow inside `templates/workflows/taskmaster/` and update registries so future tasks route through the enforcement flow by default.

## Existing Baseline (Task 88 Alignment)
- Guard already checks: same-day folder edits, tracked ACTIVE deletions, plan sync hashes, `guard` CI workflow.
- Helpers: scaffold creates TRACKER + CHANGELOG + `reports/<slug>/`; archive moves folders; sessions update ensures ULTRATHINK logging.
- Pain points observed:
  - Findings/Decisions often updated manually → easy to miss.
  - Serena memory capture not enforced, leading to compaction gaps.
  - Multi-day active folders require explicit timestamp entries to satisfy guard; no automated reminder beyond audit warning.

## Scope for Task 89
1. **Workflow Definition**
   - Author `templates/workflows/taskmaster/work-tracking-enforcement.md` describing seven-file lifecycle, session hooks, and guard expectations.
   - Ensure plan template references the enforcement workflow (maybe cross-link from alignment workflow).
2. **Guard Enhancements (`scripts/codex-guard`)**
   - Detect when files under active folder are changed but corresponding FINDINGS/DECISIONS/CHANGELOG/HANDOFF (if applicable) lack current-day entries.
   - Enforce Serena memory update for any session that touches work-tracking files (maybe check `memories/<date>_*` or log entry in tracker referencing memory ID).
   - Recognize multi-day ACTIVE reuse: allow if tracker includes today’s timestamp + mention of audit warning acknowledgement.
3. **Helper Enhancements (`scripts/codex-task`)**
   - Scaffold command creates all seven docs + default TODOs (IMPLEMENTATION, FINDINGS, DECISIONS, CHANGELOG, HANDOFF stub).
   - Provide `work-tracking update --preset findings/decisions/changelog` shortcuts to reduce manual error.
   - Archive command optionally prompts to append final summary to HANDOFF.
4. **Taskmaster Alignment**
   - Update `.taskmaster/tasks/tasks.json` subtasks (88 already, add new 89 details) plus ensure Task 89 checklist includes Serena memory + audit usage.
5. **Evidence / Regression**
   - Create guard + pytest fixtures simulating missing updates to ensure new rules catch them.
   - Capture `codex-task audit` output post-changes to show clean baseline.

## Open Questions / Decisions Needed
- Do we mandate Serena memory per session (guard failure) or treat as warnings with audit tooling?
- Where to store multi-session HANDOFF docs (per task vs per session)?
- Should guard require explicit Taskmaster status change entries when closing tasks?
- How to make helper aware of branch naming (auto-suggest `feat/task-<id>-...`)?

## Implementation Notes Draft
- Begin with failing tests for guard signals covering: missing findings update, missing decisions entry, absent Serena memory tag in tracker.
- Update guard detection to parse tracker progress log for `[H:docs/findings]`, `[H:docs/decisions]`, `[H:docs/changelog]` entries dated today.
- Extend helper CLI with new subcommand `work-tracking remind` to print pending docs.
- Document workflow under `templates/workflows/taskmaster/` and add entry to registry.
- Update README/plan template references if required.

## Evidence Targets
- `docs/ai/work-tracking/active/20251027-task89-work-tracking-enforcement-ACTIVE/reports/work-tracking-enforcement/guard-*.txt`
- `reports/work-tracking-enforcement/tests-*.txt` for pytest runs.
- Serena memory: `2025-10-27_task89_work_tracking_enforcement` (TBD once captured).

## Next Action Items
1. Produce failing guard test cases for missing findings/decisions updates.
2. Prototype guard rule changes to satisfy the new tests.
3. Update helper scaffold + update commands; add CLI documentation.
4. Draft workflow documentation + registry updates.
5. Capture regression evidence + update Findings/Decisions/Handoff when enforcement works end-to-end.
