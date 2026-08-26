# ga-k9sd — beads-first workflow and reboot hardening

- Primary authority is Gas City bead `ga-k9sd` in the `gascity` rig store; status is `in_progress`, priority P1.
- Codex-facing guidance and reboot-readiness assets are staged on `codex/ga-k9sd-beads-first-guidance`; Taskmaster remains historical/read-only during migration.
- Historical Task 252 residue was empty and removed after its completed archive and merged PR were verified. Task 288 was legitimately archived through `scripts/codex-task work-tracking archive` after merged PR #289 was verified.
- Bead `ga-hoaq` tracks the separate advertised-but-missing work-tracking override defect.
- The source workflow now has a tested bead-native `wizard kickoff --bead` path and guard support for `Bead IDs`; it does not invoke Taskmaster.
- Claude/Aegis readiness now has a tested source-only bead path: `codex/<bead-id>-...`, current plan `Bead IDs` plus exact branch policy, current session/state, one matching ACTIVE tracker, and plan/tracker parity must all align. The real `ga-k9sd` checkout reports `READY`; arbitrary target repositories cannot use this path, and numeric Taskmaster compatibility remains intact.
- Fable passed the reboot-hardening package and Gas City supervisor self-prune head. Stable doctor/bootstrap installation remains deliberately unexecuted pending the refreshed exact-head review.
- Current plan/session/tracker are bound to `ga-k9sd`. The previously reviewed tree changed to include the readiness repair, so compute and send a refreshed exact tree/package to Fable before creating the signed local commit. Preserve unrelated untracked user artifacts.
