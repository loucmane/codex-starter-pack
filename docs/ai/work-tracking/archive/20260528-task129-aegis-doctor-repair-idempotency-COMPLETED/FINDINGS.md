# Findings

- 2026-05-28 — Task 128 proved the portable happy path works in a real Claude session, but "state-of-the-art" requires recovery and replay semantics, not only successful first-run behavior.
- 2026-05-28 — The highest-leverage next surface is a read-only `doctor` report that explains installed state, current work, pending tracking, pointer/symlink health, managed file drift, optional integrations, strict verification, closeout state, and safe repair options without mutating target files.
- 2026-05-28 — Repair must be explicitly narrower than doctor. It can restore missing managed files, executable bits, expected directories, and current symlinks when those actions are mechanically derivable, but it must not overwrite divergent user files, clear non-empty pending tracking, or delete/archive stale active folders by default.
- 2026-05-29 — The second real Claude run passed the installed fresh-project workflow end to end after the replay/backfill fix: MCP install/start, native source edit, verification, handoff repair, closeout, and doctor completed without synthetic handler names or direct implementation/changelog edits.
