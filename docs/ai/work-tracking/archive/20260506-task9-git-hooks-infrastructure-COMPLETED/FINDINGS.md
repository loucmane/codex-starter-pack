# Findings

- 2026-05-06 - After Task 8 archive, `python3 scripts/codex-guard validate --include-untracked` failed with `No ACTIVE work-tracking folder found under docs/ai/work-tracking/active/`; active Task 9 tracking was needed before continuing system-template edits.
- 2026-05-06 - The user configured SSH/GPG auth caching for 24 hours, which affects GitHub fetch, push, branch cleanup, PR, and signed commit workflows.
- 2026-05-06 - Current templates already covered Git commands and readiness but did not make auth-cache refresh a workflow expectation before GitHub operations.
- 2026-05-06 - `.pre-commit-config.yaml` already exists with local `codex-guard validate --include-untracked` and `codex-guard drift-check --strict --report-dir ""` hooks, so Task 9 should not recreate pre-commit from scratch.
- 2026-05-06 - `.venv/bin/pre-commit` exists at version 4.6.0, but `pre-commit` is not on the default shell `PATH` and `.git/hooks/` contains only sample hooks, so local hook installation is not active.
- 2026-05-06 - CI already runs guard, drift-check, and metrics through `.github/workflows/codex-guard.yml` and `.github/workflows/meta-workflow-guard.yml`; Task 9 should focus on local hook parity/verification and missing coverage.
- 2026-05-06 - Task 9's original `.git/hooks/` and `SKIP_HOOKS=1` wording is stale relative to the portable foundation because untracked `.git/hooks/` scripts are not a portable canonical system layer.
- 2026-05-06 - `.venv/bin/pre-commit run --all-files` initially failed because default pre-commit cache path `/home/loucmane/.cache/pre-commit` is read-only in the sandbox; rerunning with `PRE_COMMIT_HOME=/tmp/codex-pre-commit-cache` passed.
- 2026-05-06 - Current `.pre-commit-config.yaml` is operational when pre-commit is invoked through the project virtualenv and a writable cache path: both `Codex Guard Validate` and `Codex Guard Drift Check` passed.
- 2026-05-06 - `task-master update-subtask --id=9.1` failed because the configured Claude Code provider exited with an API error; the scope notes are therefore recorded in repo work-tracking artifacts, while the non-AI `set-status` update succeeded.
- 2026-05-06 - `python3 scripts/codex-task hooks verify` now proves the tracked `.pre-commit-config.yaml` still contains the guard and drift-check hooks, finds `.venv/bin/pre-commit` at version 4.6.0, and reports local `.git/hooks/pre-commit` installation state.
- 2026-05-06 - Strict hook verification failed before local install because `.git/hooks/pre-commit` was missing, then passed after `.venv/bin/pre-commit install`; the helper can now detect local hook drift without relying on manual inspection.
- 2026-05-06 - Focused regression tests cover hook-verifier parser support, required config snippets, missing pre-commit binary failure, missing local-hook warning mode, strict installed-hook mode, installed-hook acceptance, unmanaged hook rejection, and the existing pre-commit config guard/drift expectation.
