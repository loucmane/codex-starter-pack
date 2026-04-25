# Reference Pattern Mapping

**Generated**: 2026-04-25 13:47 CEST
**Source**: `rg`

## Counts
- Wiki-style links: 1
- Include-style references: 3
- Raw path references across scanned markdown/Python/config files: 7292
- Current-surface path references excluding Codex history, active Task 1 reports, and work-tracking archive: 6385
- Live template/scanner references in current docs/scripts/tests/config: 1392
- Python import statements in `scripts/` and `tests/`: 140

## Evidence Files
- `wiki-link-refs.txt`
- `include-refs.txt`
- `template-path-refs.txt`
- `template-path-refs-current.txt`
- `template-path-refs-live.txt`
- `python-import-refs.txt`

## Findings
- Wiki-style references are almost absent; the one hit is an example in `templates/integration/architecture/template-architecture.md`.
- Include-style references are rare and mostly appear in session/history wording, not as active templating dependencies.
- Direct path references are the dominant dependency pattern.
- Historical plans, sessions, and work-tracking archives create substantial reference noise, so downstream analysis should prefer the `template-path-refs-live.txt` surface for active dependencies.
