# Task 93 Remediate Compaction Detection Behavior – Implementation Notes

## Planned Workstreams
- Scope audit: document current conflicts and references before behavior edits.
- Behavior retirement: reduce deprecated `compaction-detection.md` to a compatibility pointer instead of executable guidance.
- Aggregate doc cleanup: split compaction and session-end guidance in `templates/BEHAVIORS.md`.
- Guard alignment: stop enforcing GAC summary requirements on retired compaction detection guidance.
- Regression coverage: add focused tests so the deprecated behavior cannot become canonical again.

## Completed Workstreams
- Replaced the deprecated behavior body with a short tombstone that redirects to canonical compaction/session-end sources.
- Split aggregate session guidance so compaction and session end are now separate sections in `templates/BEHAVIORS.md`.
- Removed deprecated compaction detection from `scripts/codex-guard` canonical GAC summary docs.
- Added focused tests confirming deprecated compaction guidance is ignored for GAC enforcement and no longer considered canonical.
