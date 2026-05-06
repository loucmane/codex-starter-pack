# Task 9 Scope Reconciliation

## Timestamp

- `date '+%Y-%m-%d %H:%M:%S %Z %z'` -> `2026-05-06 13:47:39 CEST +0200`
- `date '+%Y-%m-%d %H:%M:%S %Z %z'` -> `2026-05-06 14:25:57 CEST +0200`

## Current-State Inputs

- Taskmaster Task 9: `Setup Git Hooks Infrastructure`
- Current branch: `feat/task-9-git-hooks-infrastructure`
- Taskmaster next before kickoff: Task 10, but Task 9 remains pending and directly owns Git hook/auth infrastructure.
- Triggering event: Task 8 PR merged; Task 8 work tracking was archived; guard then failed because no ACTIVE work-tracking folder existed.
- User environment update: SSH/GPG auth cache now lasts 24 hours.

## Scope Decision

Task 9 is the correct active workflow container for the post-merge Git/auth system update because:

- the touched reusable templates cover GitHub fetch, push, branch cleanup, PR, and signed commit operations;
- the update belongs to Git workflow readiness and hook-system behavior rather than template registry implementation;
- leaving template edits outside an active task would repeat the system gap the user is trying to eliminate.

Task 10 remains the Taskmaster next task after this Git infrastructure setup is either completed or explicitly paused.

## In Scope For This Checkpoint

- Archive Task 8 work tracking after confirmed PR merge and branch cleanup.
- Start Task 9 with compliant session, plan, and work-tracking state.
- Record SSH/GPG 24-hour cache expectations in reusable Git/readiness/session/troubleshooting templates.
- Capture evidence for work-tracking audit, guard, and diff-check after the archive/template updates.

## Deferred To Task 9 Implementation

- Full pre-commit/pre-push hook installation and regression testing.
- Secret scanning, ruff, scanner incremental mode, and CI-compatible hook output formatting.
- Any bypass mechanism design; `--no-verify` remains explicitly user-authorized and documented only.

## Current-State Audit

### Existing tracked hook configuration

`.pre-commit-config.yaml` already exists and defines two local hooks:

- `codex-guard-validate`: `python3 scripts/codex-guard validate --include-untracked`
- `codex-guard-drift-check`: `python3 scripts/codex-guard drift-check --strict --report-dir ""`

Both hooks use:

- `language: system`
- `pass_filenames: false`
- `always_run: true`

This means the repo already has local pre-commit wiring for the core guard and drift-check path. Task 9 must not re-create that from scratch.

### Existing CI coverage

Two GitHub Actions workflows currently run guard-related checks:

- `.github/workflows/codex-guard.yml`
  - runs on pull requests and pushes;
  - runs plan sync, `codex-guard validate --include-untracked`, `codex-guard drift-check --strict`, and `template-metrics-dashboard`;
  - uploads template drift and metrics artifacts.

- `.github/workflows/meta-workflow-guard.yml`
  - runs on pull requests touching workflow/template/session/plan/test surfaces and pushes to `main`;
  - installs optional dependencies from `requirements-ci.txt` / `requirements.txt` if present;
  - runs the timestamp regression suite, plan sync, guard, drift-check, and template metrics dashboard;
  - uploads guard/drift/metrics artifacts.

This means CI is already an authoritative merge gate for guard behavior. Task 9 should improve local hook parity and coverage without duplicating CI workflows unnecessarily.

### Existing tests

`tests/meta_workflow_guard/test_guard_rules.py` already contains `test_pre_commit_config_runs_codex_guard_validate_and_drift`, which asserts:

- `.pre-commit-config.yaml` includes guard validation;
- `.pre-commit-config.yaml` includes drift-check with `--report-dir ""`;
- the local hooks use `pass_filenames: false`;
- the local hooks use `always_run: true`.

This is configuration coverage only. It does not prove hook installation, actual `pre-commit run`, bypass behavior, secret scanning, ruff, scanner incremental mode, or pre-push behavior.

### Local environment check

Evidence from shell checks:

- `pre-commit --version` is not on the default shell `PATH`.
- `.venv/bin/pre-commit --version` returns `pre-commit 4.6.0`.
- `.git/hooks/` contains only Git sample hooks; no active `pre-commit` or `pre-push` hook is installed.
- `git config --get commit.gpgsign` returns `true`.
- `git config --get gpg.program` returns `/usr/bin/gpg`.
- `git config --get remote.origin.url` returns `git@github.com:loucmane/codex-starter-pack.git`.

This confirms the repo has the dependency available in the project virtualenv, but local hook installation is not currently active in `.git/hooks/`.

### Portable foundation alignment

Task 9 must follow the portable foundation contract:

- use repo-local config and tracked files where possible;
- keep core behavior in `scripts/` and repo-adapter behavior in config/docs;
- avoid relying on untracked `.git/hooks/` scripts as the canonical source of behavior;
- keep local hook output non-mutating by default so pre-commit can run without dirtying the worktree;
- keep CI as the authoritative merge gate when local hooks are not installed.

The original Task 9 wording says to add custom hook scripts in `.git/hooks/` and implement `SKIP_HOOKS=1`. That wording is historical and should not be executed as-is because `.git/hooks/` is untracked, non-portable, and not suitable as the canonical system layer. Any bypass mechanism must be explicit, user-authorized, and logged in work tracking.

## Remaining Proven Gap

Task 9.2 should target local/CI hook parity and install verification rather than basic pre-commit creation.

Recommended current-scope implementation:

- Add a tracked hook verification path that checks whether pre-commit is available and whether the local `.git/hooks/pre-commit` entry is installed.
- Prefer documenting/running `.venv/bin/pre-commit install` or `uv run pre-commit install` over relying on a global `pre-commit` binary.
- Add tests that prove the current `.pre-commit-config.yaml` remains non-mutating and runs the expected guard/drift commands.
- Decide whether to add `ruff` only after running current formatting/lint evidence; do not add it blindly if it would create broad unrelated failures.
- Decide whether to add `detect-secrets` only after adding a baseline and test strategy; no current dependency or baseline exists.
- Defer repo-wide protected-path/pre-push policy design to a separate explicit decision if it overlaps with the Claude adapter enforcement work.

## Task 9.1 Conclusion

Subtask 9.1 can close once this document is referenced from tracker/session evidence and guard/audit/diff-check pass. Task 9.2 should begin from the remaining proven gap above.
