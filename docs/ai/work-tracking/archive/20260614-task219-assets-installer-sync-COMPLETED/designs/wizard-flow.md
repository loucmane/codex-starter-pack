# Task 219 — Sync packaged installer mirror: design scope

Date: 2026-06-14. Discovered during TM 218: aegis_foundation/assets/scripts/_aegis_installer.py
(the wheel/sdist-packaged installer) drifted from live scripts/_aegis_installer.py — it missed
TM 215 (_manifest_schema_failure_message), 218 (evidence demotion), 221 (drain fix) AND still
carried the TM-197 observation-globs that were REVERTED in live (they changed detection and
failed 6 tests). No parity test guarded the mirror, so three fixes silently never reached the package.

## Verification before sync
Categorized the full diff: every assets-only line is stale (the reverted observation-globs
feature + the pre-215 `exc.message`). Nothing intentional/assets-only. Live is the source of truth.

## Change
- cp scripts/_aegis_installer.py -> aegis_foundation/assets/scripts/_aegis_installer.py
  (now byte-identical; brings 215/218/221, drops reverted globs).
- New tests/meta_workflow_guard/test_assets_scripts_parity.py: byte-parity for the
  Claude-maintainable .py mirrors (_aegis_installer, _repo_structure, template_*), a guard
  that no new unmirrored .py drifts, and explicit tracking of the Codex-owned drift.

## Codex-owned drift (NOT fixed here)
codex-guard and codex-task assets mirrors are ALSO drifted, but scripts/codex-* are Codex-owned;
Claude must not edit them. Filed as a Codex-led follow-up; tracked in the parity test's
KNOWN_CODEX_OWNED_DRIFT so the gap is explicit.

## Boundary
aegis_foundation/assets/scripts/_aegis_installer.py + the new parity test only. Live installer
unchanged. HP-Coach/codex run the live copy; this fixes the distributed package + prevents recurrence.
