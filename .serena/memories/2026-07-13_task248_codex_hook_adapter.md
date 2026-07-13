# Task 248 — First-Class Codex Hook Adapter

- Date: 2026-07-13
- Branch: feat/task-248-codex-hook-adapter-bootstrap
- Worktree: /tmp/codex-task248-bootstrap
- Taskmaster: Task 248, in progress, depends on Task 247.
- Source: owner-authorized canonical Codex apply_patch and managed hooks adapter specification.
- Runtime objective: parse the canonical apply_patch command strictly, normalize every Add/Update/Delete/Move source and destination path, evaluate all paths under existing Aegis policy, and record one atomic pending/evidence event with handler codex:apply_patch, operation metadata, and deterministic digest.
- Installer objective: make .codex/hooks.json a first-class managed Aegis asset independent of the Claude adapter, with profile/manifest/verification, client-reload, hook-trust, safe adoption, and manual-review behavior.
- Required proof: runtime READY/BLOCKED, all operations, multi-file safe-first/protected-later, malformed/degraded strict/advisory, one PostToolUse event, installer idempotence/parity, Codex-only and multi-agent installs, and a real Codex 0.144.3 hook smoke.
- Verified environment: codex-cli 0.144.3.
- Current boundary: kickoff is complete; guard requires the Task 248 scope design and this same-day Serena reference before source mutation.
- Preservation: primary checkout user drift under .codex, .agents, and local .aegis remains untouched; all work is isolated in /tmp worktrees.
- Downstream: after upstream merge, update Blog through aegis update preview/apply and strict verify, then stop for owner review of exact /hooks hashes without bypassing trust.
