# Findings

- 2026-05-07 — The existing `scripts/template-ssot-scanner/output/scripts/apply_reference_fixes.py` is generated output, not tracked source. It lacks the advertised `--dry-run`, has no backups, has no git rollback, and performs direct replacements when executed.
- 2026-05-07 — `scripts/template-ssot-scanner/README.md` advertises `python3 output/scripts/apply_reference_fixes.py --dry-run`, but current generated script content does not implement an argument parser.
- 2026-05-07 — Task 10 should improve scanner tooling safety rather than apply the historical generated fixes directly.
- 2026-05-07 — A real dry-run against current recommendations reports 119 would-change items and 1 unchanged item. This is useful evidence for a later reference-cleanup task, but Task 10 intentionally does not apply those content changes.
- 2026-05-07 — Foundation portability needs a first-class installer model rather than manual template copying. The leading option is a versioned local runtime/CLI installed into each project, with MCP used as an installer/control plane rather than the sole enforcement surface.
