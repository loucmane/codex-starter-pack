# Timestamp Guard Policy – Task 84

## Objectives
- Enforce that all timestamps in sessions, trackers, and related artefacts come from real-time commands (`date`), not manual edits.
- Ensure chronological consistency (session logs in chronological order, changelog reverse chronological, etc.).
- Provide guard-level errors when timestamps are stale, out-of-order, or missing command evidence.

## Target Artefacts
- `sessions/YYYY/MM/*` (session logs)
- `docs/ai/work-tracking/active/**/TRACKER.md`
- `docs/ai/work-tracking/active/**/CHANGELOG.md`
- Guard/test reports under `reports/timestamp-guard/`
- Any plan/implementation file requiring timestamps (future extension)

## Enforcement Rules
1. **Fresh Retrieval:** Any timestamp entry must be preceded by a command record (S:W:H:E) referencing `date` or equivalent. Guard checks that `date` occurred within the session and matches the recorded value.
2. **Format Validation:** Timestamps must follow `YYYY-MM-DD HH:MM ZZZ` (24-hour clock, timezone abbreviation). Guard rejects deviations.
3. **Chronology:**
   - Session logs: timestamps must be non-decreasing.
   - Changelog: newest entries first (reverse chronological).
   - Tracker progress entries: non-decreasing for time of day.
4. **Plan Sync Dependency:** Guard ties timestamp validation to plan-step-scope; plan must list affected artefacts.

## Implementation Plan
- Extend `scripts/codex-guard` to:
  - Parse relevant files and extract timestamp entries.
  - Locate matching `date` S:W:H:E entries.
  - Compare recorded timestamps with actual command output (cached per session).
  - Evaluate ordering rules and emit descriptive errors.
- Store violation details for remediation.

## Tests
- Unit tests for timestamp parsing and comparison.
- Integration tests with synthetic session/tracker files.
- Regression suite stored under `tests/timestamp_guard/`.

## Risk & Mitigation
- **Risk:** Missing timezone abbreviations → enforce guard expectations.
- **Risk:** Non-standard time zones/locales → rely on consistent `date` command output, allow override via configuration if needed.

## Next Steps
- Mark plan-step-scope complete once guard policy is reviewed.
- Implement guard & tests (plan-step-implement).
- Capture evidence and update documentation.
