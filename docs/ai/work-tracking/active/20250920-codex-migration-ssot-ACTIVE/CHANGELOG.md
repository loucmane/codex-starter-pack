# Changelog

## 2025-09-20

### Added
- Created Codex work-tracking folder with required documentation files and supporting subdirectories.
- Ported SSOT scanner suite into Codex repo and ran initial scans.
- Documented enforcement plan (codex-task helper + diff-aware guard with optional auto-fix).
- Implemented `scripts/codex-task` (session/work-tracking scaffolds) and `scripts/codex-guard` (diff-aware validator) with initial local validation.
- Captured duplicate analysis, migration detector, fix generation, and safe reorg outputs (`output/data/*`, `scripts/template-ssot-scanner/output/`).
- Logged scanner summary in `reports/2025-09-20-ssot-scanner-summary.md`.

### Changed
- Updated `templates/TOOLS.md` with explicit Serena MCP guidance for Codex users.
- Patched scanner scripts to detect `.codex/` configs alongside legacy `.claude/` paths.
- Confirmed Codex wrapper initializes with project agents catalog (`.codex/AGENTS.md`).
- Work-tracking/session logs now include codex-task/codex-guard S:W:H:E entries seeded via helper.

### Fixed
- N/A (auto-fix mode for guard still pending).

### Removed
- None.
