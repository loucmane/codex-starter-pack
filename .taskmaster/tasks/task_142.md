# Task ID: 142

**Title:** Dogfood Aegis Reconcile Across Real Repo History

**Status:** done

**Dependencies:** 141 ✓

**Priority:** medium

**Description:** Validate the new read-only Aegis reconcile report against the current repository history and safe isolated target-project copies before any future status automation is considered.

**Details:**

After Task 141 is merged, run the reconcile command as an evidence-gathering dogfood pass rather than a behavior-changing implementation task. Use the existing Python Aegis Foundation stack: `scripts/codex-task` wraps `aegis_reconcile`, core logic lives in `scripts/_aegis_installer.py` (`reconcile`, `_resolve_reconcile_base_ref`, `_reconcile_branch_candidates`, `_reconcile_finding`, `format_reconcile_summary`), package CLI support is in `aegis_foundation/cli.py`, MCP exposure is in `aegis_mcp/server.py`, and regression coverage is concentrated in `tests/meta_workflow_guard/test_aegis_installer.py`, `tests/meta_workflow_guard/test_aegis_mcp_server.py`, and `tests/claude_adapter/test_pretooluse_gates.py`. Create Task 142 work-tracking evidence under the normal `docs/ai/work-tracking/active/<date>-task142-.../reports/` pattern and capture each command, raw result, exit status, environment caveats, and interpretation. Run current-repo reconcile in both git-only mode (`--no-github`) and GitHub-enabled mode, classify every warning/error/finding as expected, explainable historical noise, false positive, false negative, environment limitation, or true drift. Specifically verify that squash-ambiguous git-only non-ancestor branches remain `unknown` unless GitHub PR metadata proves merge, matching the Task 141 tests for squash ambiguity. Run at least one safe isolated target-project smoke: prefer a temporary copy of hpfetcher if available, otherwise create/use a synthetic fixture or one of the existing Aegis target fixture shapes under `tests/fixtures/aegis-target-projects/`; never run mutation-capable closeout/status automation against a real external repo. Confirm by before/after checks that reconcile does not call Taskmaster status mutation, does not write `.taskmaster`, does not mutate git refs or worktree content, does not create or update PRs, and does not alter `.aegis` state beyond any explicitly documented report/evidence files created by the dogfood task itself. Document tuning recommendations as findings only; do not implement auto-status mutation, auto-closeout, PR mutation, or Taskmaster status updates as part of this task.

**Test Strategy:**

Capture and interpret outputs for `python3 scripts/codex-task aegis reconcile --target-dir . --no-github`, `python3 scripts/codex-task aegis reconcile --target-dir .`, and the isolated target-project reconcile smoke. Acceptance requires the current repo no-GitHub reconcile to be low-noise with zero errors, GitHub-enabled reconcile to report only explainable findings, and the target-project smoke to pass or record an explicit environment limitation. Verify read-only behavior with before/after `git status --short`, relevant `.taskmaster` and `.aegis` file checks, and evidence notes showing no Taskmaster, git, PR, or Aegis-state mutation. Run `python3 scripts/codex-task taskmaster health` and `python3 scripts/codex-guard validate`; run focused pytest such as `PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest tests/meta_workflow_guard/test_aegis_installer.py -k reconcile` only if reconcile behavior or tests are changed.
