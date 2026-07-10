# Task 235 Prevent semantic regression in managed Aegis updates – Implementation Notes

## Guard Parity
- Added `.aegis/state/current-work.json` completed-state fallback when no ACTIVE folder exists.
- Enforced archive-root containment and the `-COMPLETED` suffix before resolving `TRACKER.md`.
- Included active and archived work-tracking roots in changed-document validation.
- Added five focused active/completed resolution regressions.

## Managed Update Safety
- Added SHA-256 checksums to newly generated managed-file manifest records.
- Compared installed bytes to their recorded checksum before any generic managed overwrite.
- Recovered legacy source-backed baselines from the recorded source root/commit with `git show`.
- Preserved the original manifest through runtime pointer advancement during update apply.
- Added core and CLI coverage for pristine stale upgrades, divergence refusal, legacy recovery,
  successful apply, and second-preview idempotency.

## Packaged Assets
- Synchronized `scripts/codex-guard` and `scripts/_aegis_installer.py` to their
  `aegis_foundation/assets/scripts/` mirrors; byte parity passes.
