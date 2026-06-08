# Task 179 - Managed Bootstrap Upgrade

Task 179 fixed the Aegis installer bootstrap-refresh path exposed by HP-Coach after Task 178 merged.

## Context
- HP-Coach `plan-install` from Codex main showed 10 `manual-review` operations for files already recorded as Aegis-owned in `.aegis/foundation-manifest.json`.
- The affected files included `.aegis/bin/aegis`, `.claude/scripts/*`, `schemas/aegis/foundation-manifest.schema.json`, and `.aegis/foundation-manifest.json`.
- `repair` had no safe action, so the existing install could not reach the new dispatcher runtime without manual cleanup.

## Change
- Added installer ownership helpers in `scripts/_aegis_installer.py`.
- Existing files listed in manifest `managed_files` now classify as safe `modify` upgrades when content differs from current expected assets.
- Paths listed in manifest `customized_files` still classify as `manual-review`.
- Synced the packaged mirror at `aegis_foundation/assets/scripts/_aegis_installer.py`.
- Added installer tests for safe manifest-owned bootstrap upgrades and customized-file refusal.

## Verification
- Focused new tests passed.
- `PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_installer.py` passed: 81 passed, 1 skipped.
- HP-Coach dry-run after the fix reported `manual_reviews=0`, `modifies=10`, `creates=1`.
- `task-master validate-dependencies` and `python3 scripts/codex-task taskmaster health` passed with 178 tasks done and zero invalid dependency refs.

## Status
- Task 179 marked done.
- Active tracker: `docs/ai/work-tracking/active/20260608-task179-managed-bootstrap-upgrade-ACTIVE/`.
