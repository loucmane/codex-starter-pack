# Task 253 Make Codex Hook Trust Verification Reproducible from Tracked State – Implementation Notes

## Implemented Workstreams
- Added named constants for the exact `/hooks` review command, exact hook-definition hash scope, and canonical unsupported-reason text.
- Reused the canonical reason when generating the tracked `codex.hook_trust` manifest gate.
- Added `_tracked_codex_hook_trust_guidance`, which returns guidance only for one complete, exact tracked gate contract.
- Changed strict Codex verification to derive guidance from that tracked gate and expose `source=manifest_gate` in check details.
- Added a clean-checkout regression that deletes the ignored install report before strict verification, plus missing, duplicate, and altered-gate denial coverage.
- Mirrored all runtime changes in `aegis_foundation/assets/scripts/_aegis_installer.py`.

## Security Boundary
- Hook trust remains a manual Codex client decision reviewed through `/hooks`.
- The verifier does not infer trust from repository content and does not permit bypass.
- Ambiguous or altered tracked policy produces an empty guidance record, causing the existing required strict check to fail.

## Rollback
- Revert the Task 253 commit. This restores install-report dependence and the original clean-checkout failure; no state or data migration is involved.
