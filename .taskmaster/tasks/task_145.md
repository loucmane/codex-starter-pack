# Task ID: 145

**Title:** Add Reconcile Side-Effect Snapshot Oracle

**Status:** done

**Dependencies:** 144 ✓

**Priority:** medium

**Description:** Build a reusable pytest snapshot oracle that proves Aegis reconcile remains report-only by detecting any unexpected filesystem or git control-plane mutation. Apply it to the existing reconcile test matrix while allowing only explicitly declared report output paths.

**Details:**

Implement the helper in the test support layer used by `tests/meta_workflow_guard`, preferably as a small reusable module such as `tests/meta_workflow_guard/reconcile_side_effect_oracle.py` rather than adding another ad hoc `_snapshot_files()` helper. The current weak snapshots in `tests/meta_workflow_guard/test_aegis_installer.py` and `tests/meta_workflow_guard/test_aegis_cross_project_smoke.py` only compare regular-file text, so replace or supplement them for reconcile coverage with an oracle that records, for each tracked relative path: existence state, path type (`file`, `directory`, `symlink`, `missing`), file mode from `lstat`, symlink target via `os.readlink`, regular-file content hash such as SHA-256, and recursive directory membership. Diffing must detect absent-to-created paths, deletion, content edits, chmod changes, symlink target changes, and file/directory/symlink type swaps.

Expose two modes. First, a whole-tree mode for isolated `tmp_path` reconcile fixtures that snapshots the entire target tree and asserts no deltas except caller-declared output path(s). Do not blanket-exclude `.aegis/reports`; if reconcile writes there unexpectedly, the test should fail unless that exact path is declared. Permit only narrowly justified git discovery churn, e.g. `.git/FETCH_HEAD` and `.git/logs/**`, while still checking `.git/HEAD`, `.git/refs/**`, and `.git/packed-refs`. Guard this mode so it is used only against isolated fixtures under pytest temp directories, not the real repository. Second, add a focused control-plane mode for larger or real repositories that snapshots mutation-sensitive surfaces: `.aegis/**`, `.taskmaster/**`, `docs/ai/work-tracking/**`, `sessions/**`, `plans/**`, `.git/HEAD`, `.git/refs/**`, and `.git/packed-refs`.

Apply the oracle around direct `reconcile(...)` calls in `tests/meta_workflow_guard/test_aegis_installer.py`, where reconcile is imported from `scripts/_aegis_installer.py`. Cover the existing cases for merged-but-not-done, squash/GitHub, squash offline unknown, done offline unknown, done with open PR, and ambiguity/stubs. Add missing reconcile fixtures where applicable for drift-mixed, malformed or missing Taskmaster state, and GitHub unavailable/disabled behavior by monkeypatching `_run_gh_pr_list` or using `use_github=False`. Keep the implementation strictly test-side unless a small public helper is needed; do not add mutation behavior to `scripts/_aegis_installer.py::reconcile`, `scripts/codex-task aegis reconcile`, `aegis_foundation/cli.py::handle_reconcile`, or MCP `aegis.reconcile`. If a reconcile test intentionally writes a JSON or markdown report in the future, require the test to pass that exact relative output path as an allowed delta instead of allowing broad report directories.

**Test Strategy:**

Add dedicated pytest unit tests for the oracle helper, ideally in `tests/meta_workflow_guard/test_reconcile_side_effect_oracle.py`. Unit tests must independently prove detection of regular-file content edit, file creation, deletion, mode change, symlink target change, file-to-directory, directory-to-file, file-to-symlink or symlink-to-file swaps, missing-path handling, recursive directory membership changes, and allowed-delta handling. Include tests that `.git/FETCH_HEAD` and `.git/logs/**` can be tolerated in whole-tree mode while mutations to `.git/HEAD`, `.git/refs/**`, and `.git/packed-refs` fail.

Run focused reconcile side-effect coverage with commands such as `pytest tests/meta_workflow_guard/test_reconcile_side_effect_oracle.py tests/meta_workflow_guard/test_aegis_installer.py -k 'reconcile or side_effect_oracle'`. Also run the existing MCP/report-only checks if any MCP reconcile assertions are touched: `pytest tests/meta_workflow_guard/test_aegis_mcp_server.py -k reconcile`. Final verification must include `python3 scripts/codex-task taskmaster health`, `python3 scripts/codex-guard validate`, and `python3 scripts/codex-task work-tracking audit`. Acceptance requires whole-tree isolated tests to fail on any unexpected write anywhere in the fixture, focused mode to protect the listed control-plane surfaces, and only explicitly declared output path(s) to be accepted as deltas.
