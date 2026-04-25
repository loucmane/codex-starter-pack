# Monolithic Files Summary

**Generated**: 2026-04-25 13:45 CEST
**Source**: `git ls-files '*.md' | xargs -r du -b`

## Result
- Tracked markdown files scanned: 599
- Files above 100KB: 0
- Legacy root monoliths present: 0
- Current relocated monolith/index examples: `templates/WORKFLOWS.md`, `templates/PATTERNS.md`

## Largest Tracked Markdown Files
| Bytes | Path |
|-------|------|
| 38908 | `templates/REGISTRY.md` |
| 38436 | `templates/metadata/template-overview.md` |
| 34975 | `docs/ai/work-tracking/archive/20250920-codex-migration-ssot/TRACKER.md` |
| 33398 | `docs/ai/work-tracking/archive/20250920-codex-migration-ssot/reports/task82-summary-20250929-122938.md` |
| 31264 | `templates/USER-GUIDE.md` |
| 22511 | `templates/BUILDING-BETTER.md` |

## Evidence Files
- `markdown-size-inventory.txt`
- `monolithic-files-inventory.txt`
- `monolith-heading-map.txt`

## Interpretation
The original Task 1 expectation of multiple root-level markdown monoliths above 100KB is obsolete. Current markdown is substantially more modular, and the remaining large files are registry, overview, guide, and archived evidence files rather than active root monoliths.
