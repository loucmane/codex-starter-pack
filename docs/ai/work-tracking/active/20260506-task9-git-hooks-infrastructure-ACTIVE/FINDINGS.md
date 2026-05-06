# Findings

- 2026-05-06 - After Task 8 archive, `python3 scripts/codex-guard validate --include-untracked` failed with `No ACTIVE work-tracking folder found under docs/ai/work-tracking/active/`; active Task 9 tracking was needed before continuing system-template edits.
- 2026-05-06 - The user configured SSH/GPG auth caching for 24 hours, which affects GitHub fetch, push, branch cleanup, PR, and signed commit workflows.
- 2026-05-06 - Current templates already covered Git commands and readiness but did not make auth-cache refresh a workflow expectation before GitHub operations.
