# Findings

- 2026-08-31 — The transactional lifecycle used a flat Bead-ID regex even though native
  Beads generates hierarchical initiative children such as `ga-ur1c.1`.
- 2026-08-31 — The same flat-ID assumption existed downstream in `scripts/codex-task` and
  the Aegis kickoff installer, so fixing only the outer workflow would still fail during
  scaffold creation.
- 2026-08-31 — `bd show --json` includes informational relationships in `dependencies`.
  Treating every open relationship as a blocker caused `parent-child` and `relates-to`
  edges to refuse valid work before mutation.
- 2026-08-31 — The attach surface had the inverse defect: it accepted any relationship as
  a declared blocker, allowing an informational `relates-to` edge to be claimed and added
  to source-work tracking.
- 2026-08-31 — Archive preconditions were satisfied and the completed bundle was preserved.
