# Task 219 — Packaged installer mirror sync + parity guard (2026-06-14)

aegis_foundation/assets/scripts/ is the wheel/sdist-PACKAGED copy; live scripts/ is what runs
in-repo. They are supposed to be byte-identical mirrors (like the .claude/scripts/* mirrors).
They silently DRIFTED: assets/scripts/_aegis_installer.py missed TM 215/218/221 fixes AND still
carried the reverted TM-197 observation-globs — because NO parity test guarded the mirror, so
three fixes never reached the package. (This is why I edited only live scripts/_aegis_installer.py
during 215/218/221 and CI stayed green — no test enforced the mirror.)

## Fixed
- cp scripts/_aegis_installer.py -> aegis_foundation/assets/scripts/_aegis_installer.py
  (byte-identical; verified the full diff was 100% stale-only before syncing).
- tests/meta_workflow_guard/test_assets_scripts_parity.py: byte-parity for the
  Claude-maintainable .py mirrors (_aegis_installer, _repo_structure, template_governance/
  registry/versioning) + a guard that no NEW unmirrored .py drifts + tracking of Codex-owned drift.

## Codex-owned drift (NOT fixed by Claude)
aegis_foundation/assets/scripts/codex-guard and codex-task ALSO drifted from live, but
scripts/codex-* are Codex-owned — Claude must not edit them. Filed Codex-led TM 223; the parity
test lists them as KNOWN_CODEX_OWNED_DRIFT so the gap stays explicit. When Codex re-syncs them,
move them into the enforced mirror set.

## Lesson for future mirror edits
When editing a live scripts/*.py that has an assets/scripts mirror, sync BOTH copies (the
parity test now enforces this for the .py set). The .claude/scripts/* mirrors already had
parity tests; the top-level scripts/ mirrors did not until now.

See [[task221-drain-readonly-fix]], [[task218-recoverable-closeout-evidence]].
