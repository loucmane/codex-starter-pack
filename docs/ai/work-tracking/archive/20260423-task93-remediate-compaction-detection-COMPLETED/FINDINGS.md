# Findings

- 2026-04-23 — `compaction-detection.md` is marked deprecated but still contains executable blocking behavior, including session-end checklists and full `gac "..."` output requirements.
- 2026-04-23 — The active compaction-preparation handler/docs correctly separate compaction from session ending, but the aggregate `templates/BEHAVIORS.md` still combines them.
- 2026-04-23 — `scripts/codex-guard` still treats deprecated `compaction-detection.md` as a canonical GAC summary document, which keeps stale guidance alive through enforcement.
- 2026-04-23 — Retiring the deprecated file entirely from canonical guard enforcement is cleaner than trying to keep legacy GAC examples “correct” inside a tombstone file.
