# Task 145 Design - Reconcile Side-Effect Snapshot Oracle

## Scope
Task 145 adds test-side proof that `aegis reconcile` remains report-only. The oracle must detect filesystem and git control-plane side effects before any future reconcile auto-mutation work can rely on it.

## Oracle Modes
- Whole-tree isolated fixture mode snapshots every path under a pytest temporary target and permits only caller-declared exact output paths. It tolerates narrow git discovery churn (`.git/FETCH_HEAD`, `.git/logs/**`) while still checking `.git/HEAD`, `.git/refs/**`, and `.git/packed-refs`.
- Focused control-plane mode snapshots mutation-sensitive surfaces for larger/noisy repositories: `.aegis/**`, `.taskmaster/**`, work-tracking, sessions, plans, `.git/HEAD`, `.git/refs/**`, and `.git/packed-refs`.

## Detection Contract
Each snapshot records path membership, path type, mode, symlink target, and regular-file digest. Diffs must catch file creation, deletion, content edits, mode changes, symlink target changes, and file/directory/symlink type swaps.

## Acceptance Boundary
This task is strictly test-side. It must not add mutation behavior or new mutation flags to `scripts/_aegis_installer.py::reconcile`, `scripts/codex-task aegis reconcile`, `aegis_foundation/cli.py::handle_reconcile`, or MCP `aegis.reconcile`.

## Verification Plan
- Unit-test every oracle detection class.
- Wrap the existing reconcile fixture matrix with whole-tree snapshots.
- Add malformed Taskmaster and GitHub-unavailable reconcile fixtures.
- Keep exact allowed-delta behavior ready for future report-output tests without blanket-excluding `.aegis/reports/`.
